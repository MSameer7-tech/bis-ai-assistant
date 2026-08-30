"""
CLI script to execute Phase 2C text extraction and structure parsing on acquired pilot documents.
"""

import argparse
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
    parser = argparse.ArgumentParser(description="Process acquired PDF documents into structured JSON.")
    parser.add_argument("--document-id", help="Specific Document ID to process (e.g. DOC-001)")
    parser.add_argument("--all", action="store_true", help="Process all acquired documents in documents.json")

    args = parser.parse_args()
    processor = DocumentProcessor()

    if args.document_id:
        doc = processor.process_document(args.document_id)
        logger.info(
            "Processed %s: %d pages, %d clauses, %d tables",
            args.document_id,
            doc["total_pages"],
            doc["total_clauses"],
            doc["total_tables"],
        )
    elif args.all:
        results = processor.process_all_acquired_documents()
        logger.info("Processed %d documents successfully.", len(results))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
