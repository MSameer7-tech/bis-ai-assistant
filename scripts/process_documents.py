"""
CLI script to process all acquired pilot BIS documents through the Phase 2C ingestion pipeline.
Usage:
    python scripts/process_documents.py
"""

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
    processor = DocumentProcessor()
    results = processor.process_all_acquired_documents()

    print("\n" + "=" * 80)
    print(f"✅ Ingestion Pipeline Complete for {len(results)} Pilot Documents:")
    print("=" * 80)
    print(f"{'Doc ID':<10} | {'Standard/Doc Number':<30} | {'Pages':<6} | {'Clauses':<8} | {'Tables':<6} | {'Quality'}")
    print("-" * 80)

    for doc_id, doc in results.items():
        meta = doc.get("extraction_metadata", {})
        doc_num = str(doc.get("document_metadata", {}).get("standard_number") or doc.get("document_metadata", {}).get("title") or "")[:28]
        pages = meta.get("total_pages", 0)
        clauses = meta.get("flat_clauses_count", meta.get("total_clauses", 0))
        tables = meta.get("total_tables", 0)
        quality = meta.get("quality_summary", {}).get("overall_quality", "UNKNOWN")
        print(f"{doc_id:<10} | {doc_num:<30} | {pages:<6} | {clauses:<8} | {tables:<6} | {quality}")

    print("=" * 80)
    print("Structured JSON files written to data/processed/")
    print("Extraction log updated at data/metadata/extraction_log.json\n")


if __name__ == "__main__":
    main()
