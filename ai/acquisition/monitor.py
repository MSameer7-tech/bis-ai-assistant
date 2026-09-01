"""
Phase 5A: BIS Source Monitoring & Discovery Telemetry.
Separates discovery from acquisition. Monitors the 9 BIS source families,
collects HTTP telemetry (ETag, Last-Modified, size, headers), and generates
candidate discovery records for downstream change detection.
"""
import os
import sys
import json
import time
import hashlib
import logging
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ACQUISITION_DIR = DATA_DIR / "acquisition"
DISCOVERY_DIR = ACQUISITION_DIR / "discovery"
TELEMETRY_DIR = ACQUISITION_DIR / "telemetry"

from ai.acquisition.sources.bis_catalog_adapter import BIS_SOURCE_FAMILIES

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/json,text/html;q=0.9,*/*;q=0.8"
}


class SourceMonitor:
    """
    Monitors official BIS source families and records telemetry without full corpus downloads.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or ACQUISITION_DIR
        self.discovery_dir = self.output_dir / "discovery"
        self.telemetry_dir = self.output_dir / "telemetry"
        self._ensure_directories()

    def _ensure_directories(self):
        self.discovery_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

    def probe_endpoint_telemetry(self, source_key: str, source_info: Dict[str, Any], timeout: float = 3.0) -> Dict[str, Any]:
        """
        Gathers HTTP telemetry (ETag, Last-Modified, Status, Content-Type, Content-Length).
        """
        url = source_info.get("search_endpoint") or source_info.get("base_url")
        telemetry = {
            "source_key": source_key,
            "source_name": source_info.get("name"),
            "family": source_info.get("family"),
            "url": url,
            "probed_at": datetime.now().isoformat(),
            "http_status": None,
            "etag": None,
            "last_modified": None,
            "content_type": None,
            "content_length": None,
            "response_time_ms": 0,
            "status": "UNREACHABLE",
            "error_details": None
        }

        if not url:
            telemetry["status"] = "INVALID_URL"
            telemetry["error_details"] = "No URL specified"
            return telemetry

        start = time.time()
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                elapsed = int((time.time() - start) * 1000)
                telemetry["http_status"] = resp.getcode()
                telemetry["etag"] = resp.headers.get("ETag")
                telemetry["last_modified"] = resp.headers.get("Last-Modified")
                telemetry["content_type"] = resp.headers.get_content_type()
                c_len = resp.headers.get("Content-Length")
                telemetry["content_length"] = int(c_len) if c_len and c_len.isdigit() else None
                telemetry["response_time_ms"] = elapsed
                telemetry["status"] = "ONLINE" if resp.getcode() == 200 else f"HTTP_{resp.getcode()}"
        except urllib.error.HTTPError as e:
            telemetry["http_status"] = e.code
            telemetry["status"] = f"HTTP_{e.code}"
            telemetry["error_details"] = str(e)
            telemetry["response_time_ms"] = int((time.time() - start) * 1000)
        except Exception as e:
            telemetry["status"] = "CONNECTION_ERROR"
            telemetry["error_details"] = str(e)
            telemetry["response_time_ms"] = int((time.time() - start) * 1000)

        return telemetry

    def monitor_all_sources(self) -> List[Dict[str, Any]]:
        """
        Monitors all 9 BIS source families and records telemetry log.
        """
        results = []
        logger.info("Monitoring 9 official BIS source families...")

        for s_key, s_data in BIS_SOURCE_FAMILIES.items():
            res = self.probe_endpoint_telemetry(s_key, s_data)
            results.append(res)

        # Save to telemetry log
        telemetry_file = self.telemetry_dir / "source_telemetry.jsonl"
        with open(telemetry_file, "a", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        logger.info(f"  ✓ Saved telemetry to: {telemetry_file}")

        return results

    def build_candidate_queue(self, manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Creates a decoupled candidate discovery queue (candidate_queue.jsonl)
        separating discovery from acquisition.
        """
        m_path = manifest_path or (DATA_DIR / "registry" / "document_manifest.jsonl")
        if not m_path.exists():
            logger.warning(f"Manifest {m_path} not found.")
            return []

        candidates = []
        with open(m_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    cand = {
                        "candidate_id": f"CAND-{item.get('document_id', '0000')}",
                        "document_id": item.get("document_id"),
                        "catalog_id": item.get("catalog_id"),
                        "entity_type": item.get("entity_type"),
                        "standard_number": item.get("standard_number"),
                        "edition": item.get("edition"),
                        "title": item.get("title"),
                        "source_url": item.get("download_url"),
                        "discovered_at": item.get("discovered_at", datetime.now().isoformat()),
                        "queue_status": "QUEUED_FOR_CHANGE_DETECTION"
                    }
                    candidates.append(cand)

        queue_file = self.discovery_dir / "candidate_queue.jsonl"
        with open(queue_file, "w", encoding="utf-8") as out:
            for c in candidates:
                out.write(json.dumps(c, ensure_ascii=False) + "\n")

        logger.info(f"  ✓ Generated candidate queue: {queue_file} ({len(candidates)} items)")
        return candidates
