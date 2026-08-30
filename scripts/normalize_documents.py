"""
CLI script to normalize all pilot BIS documents through the Phase 2D semantic normalization pipeline.
Usage:
    python scripts/normalize_documents.py
"""

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
    normalizer = DocumentNormalizer()
    results = normalizer.normalize_all_documents()

    print("\n" + "=" * 85)
    print(f"✅ Phase 2D Semantic Normalization Complete for {len(results)} Pilot Documents:")
    print("=" * 85)
    print(f"{'Doc ID':<10} | {'Standard/Doc Number':<30} | {'Entities':<10} | {'Reqs':<6} | {'Rels':<6} | {'Refs'}")
    print("-" * 85)

    for doc_id, doc in results.items():
        meta = doc.get("normalization_metadata", {})
        doc_num = str(doc.get("document_metadata", {}).get("standard_number") or doc.get("document_metadata", {}).get("title") or "")[:28]
        entities = meta.get("total_entities", 0)
        reqs = meta.get("total_requirements", 0)
        rels = meta.get("total_relationships", 0)
        refs = meta.get("total_references", 0)
        print(f"{doc_id:<10} | {doc_num:<30} | {entities:<10} | {reqs:<6} | {rels:<6} | {refs}")

    print("=" * 85)
    print("Normalized JSON files written to data/normalized/*.normalized.json\n")


if __name__ == "__main__":
    main()
