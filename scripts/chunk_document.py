"""
CLI script to generate structure-aware knowledge chunks for a single normalized BIS document.
Usage:
    python scripts/chunk_document.py --document-id DOC-001
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.chunking.chunker import StructureAwareChunker

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate structure-aware knowledge chunks for a document.")
    parser.add_argument("--document-id", required=True, help="Document ID to chunk (e.g. DOC-001)")
    args = parser.parse_args()

    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(args.document_id)

    # Count by chunk_type
    type_counts = {}
    for c in chunks:
        ch_type = c.get("chunk_type", "unknown")
        type_counts[ch_type] = type_counts.get(ch_type, 0) + 1

    print("\n" + "=" * 70)
    print(f"✅ Structure-Aware Chunking Complete for {args.document_id}:")
    print(f"   • Total Chunks: {len(chunks)}")
    for t, cnt in sorted(type_counts.items()):
        print(f"     - {t:<20}: {cnt} chunks")
    print(f"   • Output File: data/chunks/{args.document_id}.chunks.json")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
