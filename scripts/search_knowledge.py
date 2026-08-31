"""
CLI Script to Execute Hybrid Search and Display Authoritative Provenance (Step 11 & 14).
Usage:
    python scripts/search_knowledge.py --query "What is the minimum insulation resistance?"
    python scripts/search_knowledge.py --query "What torque applies to GX53 cap?"
    python scripts/search_knowledge.py --query "What was the torque requirement in 2015?" --as-of 2015-01-01
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.vectorstore.hybrid_search import HybridSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Query BIS Knowledge Base with Hybrid Search & Temporal Gate.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--as-of", help="Historical effective date (YYYY-MM-DD)")
    parser.add_argument("--standard", help="Filter by standard number (e.g. 'IS 16102 (Part 1) : 2012')")
    args = parser.parse_args()

    engine = HybridSearchEngine()
    filters = {}
    if args.standard:
        filters["standard_number"] = args.standard

    results = engine.search(
        query=args.query,
        top_k=args.top_k,
        as_of_date=args.as_of,
        filters=filters if filters else None,
    )

    print("\n" + "=" * 90)
    print(f"🔍 HYBRID RETRIEVAL RESULTS FOR: \"{args.query}\"")
    if args.as_of:
        print(f"📅 Temporal Gate (As of): {args.as_of}")
    print("=" * 90)

    if not results:
        print("No matching knowledge chunks found.")
    else:
        for idx, res in enumerate(results, 1):
            prov = res.get("provenance", {})
            print(f"\n[{idx}] Score: {res['score']:.4f} | Chunk ID: {res['chunk_id']}")
            print(f"    Standard: {prov.get('standard_number')} | Clause: {prov.get('clause')} | Pages: {prov.get('pages')}")
            print(f"    Type: {res.get('chunk_type')} | Force: {res.get('normative_force')} | Status: {res.get('temporal_status')}")
            print("    " + "-" * 80)
            preview = res["text"].replace("\n", "\n    ")
            if len(preview) > 350:
                preview = preview[:350] + "..."
            print(f"    {preview}")

    print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    main()
