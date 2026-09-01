#!/usr/bin/env python3
"""
BIS Document Integrity Validation Runner (Gate 3).
Validates acquired files against multi-tier integrity criteria and outputs structured report.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

from ai.ingestion.pdf_validator import PDFValidator, PDFValidationStatus


def run_validation(target_dir: Path, output_file: Path = None):
    logger.info(f"Scanning and validating documents in {target_dir}...")
    
    reports = PDFValidator.validate_directory(target_dir)
    total = len(reports)

    if total == 0:
        logger.warning(f"No PDF files found in {target_dir}.")
        return

    status_counts = Counter(r["status"] for r in reports)
    valid_count = status_counts.get(PDFValidationStatus.TEXT_PDF.value, 0) + status_counts.get(PDFValidationStatus.SCANNED_PDF.value, 0)

    print("\n" + "=" * 80)
    print(f"📄 BIS DOCUMENT INTEGRITY VALIDATION REPORT (GATE 3)")
    print("=" * 80)
    print(f"Target Directory:        {target_dir}")
    print(f"Total Files Scanned:     {total:>5d}")
    print(f"Integrity Pass Rate:     {valid_count:>5d} / {total} ({valid_count/total*100:.1f}%)")
    print("-" * 80)
    print("Classification Breakdown:")
    for status_name, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        status_icon = "✅" if status_name in [PDFValidationStatus.TEXT_PDF.value, PDFValidationStatus.SCANNED_PDF.value, PDFValidationStatus.VALID_PDF.value] else "❌"
        print(f"  {status_icon} {status_name:<28}: {count:>4d} ({count/total*100:>5.1f}%)")
    print("-" * 80)

    # Show failures if any
    failures = [r for r in reports if r["status"] not in [PDFValidationStatus.TEXT_PDF.value, PDFValidationStatus.SCANNED_PDF.value, PDFValidationStatus.VALID_PDF.value]]
    if failures:
        print(f"⚠️ Corrupted / Invalid Files Sample ({min(len(failures), 5)} of {len(failures)}):")
        for f in failures[:5]:
            print(f"   • {f['file_name']}: {f['status']} - {f['error_details']}")
    else:
        print("🎉 ALL FILES PASSED INTEGRITY VERIFICATION!")
    print("=" * 80 + "\n")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as out:
            for r in reports:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
        logger.info(f"Saved full validation details to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate PDF integrity")
    parser.add_argument("--dir", type=str, default=str(DATA_DIR / "raw" / "standards"), help="Directory containing PDF files")
    parser.add_argument("--output", type=str, default=str(DATA_DIR / "registry" / "validation_report.jsonl"), help="Output JSONL report path")
    args = parser.parse_args()
    run_validation(Path(args.dir), Path(args.output))
