"""
CLI script to generate structure-aware knowledge chunks for all pilot BIS documents.
Usage:
    python scripts/chunk_documents.py
"""

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
    chunker = StructureAwareChunker()
    results = chunker.chunk_all_documents()

    print("\n" + "=" * 80)
    print(f"✅ Phase 2E Chunking Complete for {len(results)} Pilot Documents:")
    print("=" * 80)
    print(f"{'Doc ID':<10} | {'Total Chunks':<14} | {'Definitions':<12} | {'Tables':<8} | {'Annexes'}")
    print("-" * 80)

    for doc_id, chunks in results.items():
        defs = sum(1 for c in chunks if c.get("chunk_type") == "definition")
        tabs = sum(1 for c in chunks if c.get("chunk_type") == "table")
        annexes = sum(1 for c in chunks if c.get("chunk_type") == "annex")
        print(f"{doc_id:<10} | {len(chunks):<14} | {defs:<12} | {tabs:<8} | {annexes}")

    print("=" * 80)
    print("Chunk files written to data/chunks/*.chunks.json\n")


if __name__ == "__main__":
    main()
