"""
CLI Script to Compute Chunk-Level Differences and Hash Match between Standards Editions (Step 8).
Usage:
    python scripts/diff_chunks.py --old DOC-001 --new DOC-012
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.chunking.chunk_diff import ChunkDiffEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Compute chunk-level hash differences between two document chunk files.")
    parser.add_argument("--old", required=True, help="Baseline Document ID (e.g. DOC-001)")
    parser.add_argument("--new", required=True, help="New / Revised Document ID (e.g. DOC-012)")
    args = parser.parse_args()

    old_path = ROOT_DIR / "data" / "chunks" / f"{args.old}.json"
    new_path = ROOT_DIR / "data" / "chunks" / f"{args.new}.json"

    engine = ChunkDiffEngine()
    diff = engine.compare_chunk_files(old_path, new_path)

    print("\n" + "=" * 90)
    print(f"🔬 CHUNK-LEVEL HASH DIFF AUDIT: {args.old} ➔ {args.new}")
    print("=" * 90)
    print(f"Total Old Chunks: {diff['total_old_chunks']} | Total New Chunks: {diff['total_new_chunks']}")
    print(f"🟢 Unchanged Chunks (Reuse Vectors):     {diff['unchanged_count']}")
    print(f"🟡 Modified Chunks (Re-embed Only):      {diff['modified_count']}")
    print(f"🔵 Added Chunks (Create Vector):         {diff['added_count']}")
    print(f"🔴 Deleted Chunks (Remove Vector):       {diff['deleted_count']}")
    print(f"⚡ Total Vectors to Embed:               {diff['reembed_required_count']} / {diff['total_new_chunks']}")
    print("-" * 90)

    if diff["modified_chunks"]:
        print(f"\nModified Chunks (Content Hash Mismatch):")
        for m in diff["modified_chunks"][:5]:
            print(f"   • Clause {m.get('clause')}: {m.get('title')} (Old: {m.get('old_content_hash')[:10]}... ➔ New: {m.get('new_content_hash')[:10]}...)")
        if len(diff["modified_chunks"]) > 5:
            print(f"   ... and {len(diff['modified_chunks']) - 5} more.")

    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
