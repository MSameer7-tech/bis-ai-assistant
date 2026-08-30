"""
CLI script to process a single acquired BIS document artifact through the Phase 2C ingestion pipeline.
Usage:
    python scripts/process_document.py --document-id DOC-001
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.ingestion.processor import DocumentProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Process a single acquired BIS document into structured JSON.")
    parser.add_argument("--document-id", required=True, help="Document ID to process (e.g. DOC-001)")
    args = parser.parse_args()

    processor = DocumentProcessor()
    doc = processor.process_document(args.document_id)

    meta = doc.get("extraction_metadata", {})
    quality = meta.get("quality_summary", {})

    print("\n" + "=" * 60)
    print(f"✅ Extraction Summary for {args.document_id}:")
    print(f"   • Title: {doc.get('document_metadata', {}).get('title')}")
    print(f"   • Standard / Doc: {doc.get('document_metadata', {}).get('standard_number')}")
    print(f"   • Total Pages: {meta.get('total_pages')}")
    print(f"   • Total Sections: {meta.get('total_sections')}")
    print(f"   • Total Clauses (Root): {meta.get('total_clauses')}")
    print(f"   • Total Clauses (All Subclauses): {meta.get('flat_clauses_count')}")
    print(f"   • Total Tables: {meta.get('total_tables')}")
    print(f"   • Total Annexes: {meta.get('total_annexes')}")
    print(f"   • OCR Used: {meta.get('ocr_used')}")
    print(f"   • Extraction Quality: {quality.get('overall_quality')}")
    print(f"   • Output File: data/processed/{args.document_id}.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
