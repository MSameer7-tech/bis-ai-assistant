"""
Secure PDF Downloader for BIS Standards Acquisition.
Validates HTTP response headers (ETag, Last-Modified) and ensures cryptographic SHA-256 integrity.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class DocumentDownloader:
    """Acquires standard documents with SHA-256 hash checks and HTTP header cache validation."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def check_remote_metadata(self, url: str) -> Dict[str, Any]:
        """Performs HEAD request to check ETag and Last-Modified headers before full download."""
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                res = client.head(url)
                headers = res.headers
                return {
                    "url": url,
                    "status_code": res.status_code,
                    "etag": headers.get("etag"),
                    "last_modified": headers.get("last-modified"),
                    "content_length": int(headers.get("content-length", 0)) if headers.get("content-length") else None,
                }
        except Exception as e:
            logger.warning("Remote metadata check failed for %s: %s", url, e)
            return {"url": url, "error": str(e)}

    def download_document(
        self,
        url: str,
        target_path: Path,
        expected_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Downloads document to target_path and verifies SHA-256 hash."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                res = client.get(url)
                res.raise_for_status()

                with open(target_path, "wb") as f:
                    f.write(res.content)

            computed_hash = compute_sha256(target_path)
            file_size = target_path.stat().st_size

            hash_match = True
            if expected_sha256 and expected_sha256.lower() != computed_hash.lower():
                hash_match = False
                logger.error("SHA-256 mismatch for %s! Expected: %s vs Got: %s", url, expected_sha256, computed_hash)

            return {
                "url": url,
                "target_path": str(target_path),
                "file_size_bytes": file_size,
                "sha256": computed_hash,
                "hash_match": hash_match,
                "etag": res.headers.get("etag"),
                "last_modified": res.headers.get("last-modified"),
                "success": True,
            }
        except Exception as e:
            logger.error("Download failed for %s: %s", url, e)
            return {"url": url, "success": False, "error": str(e)}
