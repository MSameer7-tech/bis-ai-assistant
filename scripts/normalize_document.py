"""
CLI script to normalize a single processed BIS document artifact into Phase 2D semantic JSON.
Usage:
    python scripts/normalize_document.py --document-id DOC-001
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.processing.normalizer import DocumentNormalizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Normalize a single processed BIS document into semantic JSON.")
    parser.add_argument("--document-id", required=True, help="Document ID to normalize (e.g. DOC-001)")
    args = parser.parse_args()

    normalizer = DocumentNormalizer()
    doc = normalizer.normalize_document(args.document_id)

    meta = doc.get("normalization_metadata", {})
    doc_meta = doc.get("document_metadata", {})

    print("\n" + "=" * 70)
    print(f"✅ Semantic Normalization Summary for {args.document_id}:")
    print(f"   • Standard / Doc: {doc_meta.get('standard_number') or doc_meta.get('title')}")
    print(f"   • Total Entities Extracted: {meta.get('total_entities')}")
    print(f"   • Total Requirements Statements: {meta.get('total_requirements')}")
    print(f"   • Total Semantic Relationships: {meta.get('total_relationships')}")
    print(f"   • Total Normalized Tables: {meta.get('total_tables')}")
    print(f"   • Referenced Standards: {len(doc.get('references', []))}")
    print(f"   • Output File: data/normalized/{args.document_id}.normalized.json")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
