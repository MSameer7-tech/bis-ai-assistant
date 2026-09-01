#!/usr/bin/env python3
"""
Controlled BIS Document Queue Downloader & Integrity Gate (Gate 3).
Downloads priority batches (e.g. 50 documents) and verifies magic bytes, size, and validity
before promotion to the corpus.
"""
import os
import sys
import json
import time
import hashlib
import argparse
import urllib.request
import urllib.error
import ssl
import logging
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
STAGING_DIR = DATA_DIR / "raw" / "downloads_staging"

from ai.ingestion.pdf_validator import PDFValidator, PDFValidationStatus

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8"
}


def compute_file_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def select_balanced_batch(manifest_records: List[Dict[str, Any]], limit: int = 50) -> List[Dict[str, Any]]:
    """
    Selects a balanced batch:
    - 20 active standards
    - 10 amendments
    - 10 product manuals
    - 5 SITs
    - 5 QCOs / schemes
    """
    by_type = {
        "standard": [],
        "amendment": [],
        "product_manual": [],
        "sit": [],
        "qco": [],
        "certification_scheme": []
    }
    
    for r in manifest_records:
        t = r.get("entity_type", "other")
        if t in by_type:
            by_type[t].append(r)

    selected = []
    # Target allocations
    targets = {
        "standard": int(limit * 0.40),         # 20 of 50
        "amendment": int(limit * 0.20),        # 10 of 50
        "product_manual": int(limit * 0.20),   # 10 of 50
        "sit": int(limit * 0.10),              # 5 of 50
        "qco": int(limit * 0.10),              # 5 of 50
    }

    for t_name, target_count in targets.items():
        items = by_type.get(t_name, [])[:target_count]
        selected.extend(items)

    # Fill remainder if any
    if len(selected) < limit:
        for r in manifest_records:
            if r not in selected:
                selected.append(r)
                if len(selected) >= limit:
                    break

    return selected[:limit]


def download_batch(limit: int = 50):
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    manifest_file = REGISTRY_DIR / "document_manifest.jsonl"
    
    if not manifest_file.exists():
        logger.error("Manifest not found. Run scripts/discover_bis_catalog.py first.")
        return

    all_records = []
    with open(manifest_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_records.append(json.loads(line))

    batch = select_balanced_batch(all_records, limit=limit)
    logger.info(f"Initiating controlled acquisition of {len(batch)} prioritized documents...")

    results = []
    status_counts = Counter()

    for idx, item in enumerate(batch, 1):
        doc_id = item["document_id"]
        entity_type = item["entity_type"]
        std_num = item.get("standard_number", "DOC")
        url = item.get("download_url")
        
        safe_name = f"{doc_id}_{entity_type}_{std_num.replace(' ', '_').replace('/', '_')}.pdf"
        target_path = STAGING_DIR / safe_name

        logger.info(f"[{idx:02d}/{len(batch)}] Downloading {doc_id} ({entity_type}: {std_num})...")

        # If already exists in raw standards directory, link/copy directly
        existing_raw = list((DATA_DIR / "raw" / "standards").glob(f"*{std_num.replace(' ', '_')}*.pdf"))
        if existing_raw:
            with open(existing_raw[0], "rb") as sf, open(target_path, "wb") as df:
                df.write(sf.read())
            val_res = PDFValidator.validate_file(target_path)
        else:
            # Download from URL
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=5.0, context=SSL_CTX) as resp:
                    data = resp.read()
                    with open(target_path, "wb") as f:
                        f.write(data)
                val_res = PDFValidator.validate_file(target_path)
            except Exception as e:
                val_res = {
                    "file_path": str(target_path),
                    "file_name": safe_name,
                    "exists": False,
                    "size_bytes": 0,
                    "status": "DOWNLOAD_FAILED",
                    "error_details": str(e)
                }

        status_counts[val_res["status"]] += 1
        results.append({
            "document_id": doc_id,
            "entity_type": entity_type,
            "standard_number": std_num,
            "target_path": str(target_path),
            "validation": val_res
        })

    # Summary
    print("\n" + "=" * 80)
    print(f"📥 CONTROLLED DOCUMENT DOWNLOAD & INTEGRITY REPORT (GATE 3)")
    print("=" * 80)
    print(f"Total Batch Target:      {len(batch):>5d}")
    print(f"Staging Directory:       {STAGING_DIR}")
    print("-" * 80)
    print("Validation Breakdown:")
    for stat_name, cnt in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        icon = "✅" if stat_name in [PDFValidationStatus.TEXT_PDF.value, PDFValidationStatus.SCANNED_PDF.value, PDFValidationStatus.VALID_PDF.value] else "❌"
        print(f"  {icon} {stat_name:<28}: {cnt:>4d} ({cnt/len(batch)*100:>5.1f}%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download controlled batch of documents")
    parser.add_argument("--limit", type=int, default=50, help="Number of documents to acquire (default: 50)")
    args = parser.parse_args()
    download_batch(limit=args.limit)
