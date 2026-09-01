"""
Phase 6B: Resilient HTTP Client & Multi-Portal Request Replay Layer.
Provides:
- Session pooling and cookie management
- Exponential backoff with randomized jitter
- User-Agent rotation
- Strict response timeouts and magic-byte content validation
- Structured failure logging to data/acquisition/telemetry/failed_acquisitions.jsonl
"""
import os
import sys
import json
import time
import random
import logging
import urllib.request
import urllib.error
import http.cookiejar
import ssl
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TELEMETRY_DIR = DATA_DIR / "acquisition" / "telemetry"
FAILED_LOG_FILE = TELEMETRY_DIR / "failed_acquisitions.jsonl"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


class ResilientHTTPClient:
    """
    HTTP Client with automated session handling, backoff, and failure classification.
    """

    def __init__(self, max_retries: int = 3, base_backoff: float = 1.0):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=SSL_CTX)
        )
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

    def log_failure(
        self,
        catalog_id: str,
        url: str,
        http_status: Optional[int],
        content_type: Optional[str],
        failure_class: str,
        error_msg: str,
        retryable: bool = False
    ):
        """Logs structured failure telemetry."""
        record = {
            "catalog_id": catalog_id,
            "attempted_url": url,
            "timestamp": datetime.now().isoformat(),
            "http_status": http_status,
            "content_type": content_type,
            "failure_class": failure_class,
            "error_message": str(error_msg),
            "retryable": retryable
        }
        with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.warning(f"Logged acquisition failure for {catalog_id}: [{failure_class}] {error_msg}")

    def fetch_url(
        self,
        url: str,
        catalog_id: str = "UNKNOWN",
        timeout: float = 10.0,
        expected_type: str = "application/pdf"
    ) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Executes resilient fetch with retry, jitter, and failure diagnosis.
        """
        telemetry = {
            "url": url,
            "http_status": None,
            "content_type": None,
            "content_length": 0,
            "attempts": 0,
            "success": False,
            "error": None
        }

        for attempt in range(1, self.max_retries + 1):
            telemetry["attempts"] = attempt
            # Jitter before request
            time.sleep(random.uniform(0.1, 0.3) * attempt)

            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "*/*"
            }

            try:
                req = urllib.request.Request(url, headers=headers)
                with self.opener.open(req, timeout=timeout) as resp:
                    status = resp.getcode()
                    c_type = resp.headers.get_content_type()
                    content = resp.read()
                    
                    telemetry["http_status"] = status
                    telemetry["content_type"] = c_type
                    telemetry["content_length"] = len(content)

                    # Verify Content Type / Magic Bytes
                    if expected_type == "application/pdf":
                        if not content.startswith(b"%PDF-"):
                            if b"<html" in content.lower() or b"<!doctype html" in content.lower():
                                self.log_failure(catalog_id, url, status, c_type, "PORTAL_HTML_REDIRECT", "Received HTML portal landing page instead of PDF stream")
                                return None, telemetry
                            else:
                                self.log_failure(catalog_id, url, status, c_type, "CORRUPT_MAGIC_BYTES", "File does not begin with %PDF- header")
                                return None, telemetry

                    telemetry["success"] = True
                    return content, telemetry

            except urllib.error.HTTPError as e:
                telemetry["http_status"] = e.code
                if e.code == 403:
                    self.log_failure(catalog_id, url, 403, None, "ACCESS_DENIED", "HTTP 403: WAF or access forbidden", retryable=False)
                    return None, telemetry
                elif e.code == 404:
                    self.log_failure(catalog_id, url, 404, None, "HTTP_404", "HTTP 404: Resource not found", retryable=False)
                    return None, telemetry
                elif e.code in [500, 502, 503, 504]:
                    if attempt == self.max_retries:
                        self.log_failure(catalog_id, url, e.code, None, "SERVER_ERROR", f"Server error HTTP {e.code}", retryable=True)
                time.sleep(self.base_backoff * (2 ** (attempt - 1)))
            except urllib.error.URLError as e:
                if attempt == self.max_retries:
                    self.log_failure(catalog_id, url, None, None, "CONNECTION_ERROR", str(e.reason), retryable=True)
                time.sleep(self.base_backoff * (2 ** (attempt - 1)))
            except Exception as e:
                if attempt == self.max_retries:
                    self.log_failure(catalog_id, url, None, None, "UNKNOWN_ERROR", str(e), retryable=False)
                time.sleep(self.base_backoff * (2 ** (attempt - 1)))

        return None, telemetry
