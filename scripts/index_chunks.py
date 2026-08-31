"""
CLI Script to Index BIS Knowledge Chunks into Vector Store & BM25 (Step 13).
Usage:
    python scripts/index_chunks.py
"""

import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.vectorstore.indexer import IncrementalIndexer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    indexer = IncrementalIndexer()
    metrics = indexer.index_chunks()

    print("\n" + "=" * 60)
    print("📦 BIS INCREMENTAL VECTOR INDEXING REPORT")
    print("=" * 60)
    print(f"Total Chunks in Repository:  {metrics['total_chunks']}")
    print(f"🟢 Unchanged Chunks (Reused): {metrics['unchanged_count']}")
    print(f"🟡 Modified Chunks:           {metrics['modified_count']}")
    print(f"🔵 Added Chunks:              {metrics['added_count']}")
    print(f"⚡ Vectors Generated:         {metrics['embeddings_generated']}")
    print(f"💾 Total Vector Store Count:  {metrics['vector_store_count']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
