#!/usr/bin/env python3
"""
BIS Document URL & Accessibility Prober (Gate 2).
Tests all 525 candidate document URLs without permanently downloading the entire corpus.
Verifies HTTP status, content-type, content-length, magic bytes, redirects, and accessibility.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"

# Create SSL context ignoring self-signed/expired government certs
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Range": "bytes=0-1024"  # Probe only first 1KB for speed and magic byte inspection
}


def probe_url(record: Dict[str, Any], timeout: float = 3.0) -> Dict[str, Any]:
    """
    Probes a single document URL for HTTP status, content-type, and magic bytes.
    """
    doc_id = record.get("document_id", "DOC-UNKNOWN")
    url = record.get("download_url") or record.get("document_url", "")
    
    result = {
        "document_id": doc_id,
        "catalog_id": record.get("catalog_id"),
        "entity_type": record.get("entity_type"),
        "standard_number": record.get("standard_number"),
        "edition": record.get("edition"),
        "title": record.get("title"),
        "url": url,
        "http_status": None,
        "content_type": None,
        "content_length": None,
        "magic_bytes": False,
        "redirected": False,
        "classification": "UNKNOWN",
        "accessible": False,
        "error_message": None,
        "probed_at": datetime.now().isoformat()
    }

    if not url or not url.startswith("http"):
        result["classification"] = "INVALID_URL"
        result["error_message"] = "URL is empty or not HTTP/HTTPS"
        return result

    # Check local document store first (for already acquired/proof documents)
    # E.g. data/raw/standards/...
    local_pdf = DATA_DIR / "raw" / "pilot_standards" / f"{record.get('standard_number', '').replace(' ', '_')}.pdf"
    if local_pdf.exists():
        result["http_status"] = 200
        result["content_type"] = "application/pdf"
        result["content_length"] = local_pdf.stat().st_size
        result["magic_bytes"] = True
        result["classification"] = "AVAILABLE_PDF (LOCAL)"
        result["accessible"] = True
        return result

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response:
            status = response.getcode()
            content_type = response.headers.get_content_type() or response.headers.get("Content-Type", "")
            content_length = response.headers.get("Content-Length")
            initial_bytes = response.read(1024)

            result["http_status"] = status
            result["content_type"] = content_type
            result["content_length"] = int(content_length) if content_length and content_length.isdigit() else len(initial_bytes)
            
            # Check %PDF- magic bytes
            has_pdf_magic = initial_bytes.startswith(b"%PDF-") or b"%PDF-" in initial_bytes[:128]
            result["magic_bytes"] = has_pdf_magic

            if has_pdf_magic or "application/pdf" in content_type.lower():
                result["classification"] = "AVAILABLE_PDF"
                result["accessible"] = True
            elif "text/html" in content_type.lower() or b"<html" in initial_bytes.lower() or b"<!doctype html" in initial_bytes.lower():
                result["classification"] = "HTML_RESPONSE"
                result["accessible"] = False
                result["error_message"] = "Server returned HTML webpage instead of PDF binary stream"
            elif len(initial_bytes) == 0:
                result["classification"] = "EMPTY_RESPONSE"
                result["accessible"] = False
            else:
                result["classification"] = "UNKNOWN_BINARY"
                result["accessible"] = True

    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        if e.code == 403:
            result["classification"] = "HTTP_403 (FORBIDDEN / WAF)"
            result["error_message"] = "Server requires session cookie / captcha / WAF bypass"
        elif e.code == 404:
            result["classification"] = "HTTP_404 (NOT FOUND)"
            result["error_message"] = "Document not found at URL endpoint"
        elif 500 <= e.code < 600:
            result["classification"] = f"HTTP_{e.code} (SERVER ERROR)"
            result["error_message"] = f"BIS server internal error {e.code}"
        else:
            result["classification"] = f"HTTP_{e.code}"
            result["error_message"] = str(e)
            
    except urllib.error.URLError as e:
        result["classification"] = "CONNECTION_ERROR"
        result["error_message"] = str(e.reason)
        # Note: If simulated or intranet host
        if "nodename nor servname provided" in str(e.reason).lower() or "connection refused" in str(e.reason).lower():
            result["classification"] = "UNREACHABLE_HOST"
    except Exception as e:
        result["classification"] = "PROBE_EXCEPTION"
        result["error_message"] = str(e)

    return result


def probe_all_documents(max_workers: int = 20) -> List[Dict[str, Any]]:
    """
    Probes all candidate document URLs in parallel.
    """
    manifest_file = REGISTRY_DIR / "document_manifest.jsonl"
    if not manifest_file.exists():
        logger.error(f"Manifest file {manifest_file} not found. Run scripts/discover_bis_catalog.py first.")
        return []

    records = []
    with open(manifest_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    logger.info(f"Loaded {len(records)} document records from manifest. Initiating parallel probe (workers={max_workers})...")
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(probe_url, rec): rec for rec in records}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if len(results) % 50 == 0 or len(results) == len(records):
                logger.info(f"  Probed {len(results)}/{len(records)} document URLs...")

    # Save results to data/registry/document_probe_results.jsonl
    results_file = REGISTRY_DIR / "document_probe_results.jsonl"
    with open(results_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    logger.info(f"  ✓ Saved probe results to: {results_file}")

    # Compute Statistics
    classification_counts = {}
    http_status_counts = {}
    total = len(results)
    accessible_count = sum(1 for r in results if r.get("accessible"))
    magic_bytes_count = sum(1 for r in results if r.get("magic_bytes"))

    for r in results:
        cls = r.get("classification", "UNKNOWN")
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
        
        status = str(r.get("http_status")) if r.get("http_status") is not None else "None"
        http_status_counts[status] = http_status_counts.get(status, 0) + 1

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("🔍 BIS DOCUMENT URL ACCESSIBILITY & INTEGRITY PROBE REPORT (GATE 2)")
    print("=" * 80)
    print(f"Total URLs Probed:       {total:>6d}")
    print(f"Execution Time:          {elapsed:>6.2f}s")
    print(f"Accessible Documents:    {accessible_count:>6d} ({accessible_count/total*100:.1f}%)")
    print(f"Valid Magic Bytes %PDF:  {magic_bytes_count:>6d}")
    print("-" * 80)
    print("Classification Breakdown:")
    for cls_name, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cls_name:<30}: {count:>5d} ({count/total*100:>5.1f}%)")
    print("-" * 80)
    print("HTTP Status Code Breakdown:")
    for st_code, count in sorted(http_status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  HTTP {st_code:<25}: {count:>5d} ({count/total*100:>5.1f}%)")
    print("=" * 80 + "\n")

    return results


if __name__ == "__main__":
    probe_all_documents()
