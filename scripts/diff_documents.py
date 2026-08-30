"""
CLI Tool to Compute Semantic Diff between two BIS Standard Documents (Step 5).
Usage:
    python scripts/diff_documents.py --old DOC-001 --new DOC-012
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.ingestion.change_detector import ChangeDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Compute semantic diff between two normalized standard documents.")
    parser.add_argument("--old", required=True, help="Baseline Document ID (e.g. DOC-001)")
    parser.add_argument("--new", required=True, help="Revised Document ID (e.g. DOC-012)")
    args = parser.parse_args()

    detector = ChangeDetector()
    diff = detector.compute_semantic_diff_between_versions(args.old, args.new)

    print("\n" + "=" * 90)
    print(f"📊 SEMANTIC STANDARD DIFF REPORT: {args.old} (Baseline) ➔ {args.new} (Revision)")
    print("=" * 90)
    print(f"Has Semantic Changes: {diff['has_semantic_changes']} | Total Delta Items: {diff['total_changes_count']}")
    print("-" * 90)

    # 1. Modified Requirements
    mod_reqs = diff["requirements_diff"]["modified"]
    print(f"\n🔹 MODIFIED REQUIREMENTS ({len(mod_reqs)}):")
    if mod_reqs:
        for r in mod_reqs:
            print(f"   • Parameter: {r.get('parameter')} (Clause {r.get('clause')})")
            print(f"     Old Limit: {r.get('old_operator')} {r.get('old_value')} {r.get('old_unit')}")
            print(f"     New Limit: {r.get('new_operator')} {r.get('new_value')} {r.get('new_unit')}")
    else:
        print("   (None)")

    # 2. Added Requirements
    added_reqs = diff["requirements_diff"]["added"]
    print(f"\n🔹 ADDED REQUIREMENTS ({len(added_reqs)}):")
    if added_reqs:
        for r in added_reqs[:5]:
            print(f"   • {r.get('parameter')} in Clause {r.get('clause')}: {r.get('operator')} {r.get('value')} {r.get('unit')}")
        if len(added_reqs) > 5:
            print(f"   ... and {len(added_reqs) - 5} more.")
    else:
        print("   (None)")

    # 3. Removed Requirements
    rem_reqs = diff["requirements_diff"]["removed"]
    print(f"\n🔹 REMOVED REQUIREMENTS ({len(rem_reqs)}):")
    if rem_reqs:
        for r in rem_reqs:
            print(f"   • {r.get('parameter')} in Clause {r.get('clause')}")
    else:
        print("   (None)")

    # 4. Definitions
    def_diff = diff["definitions_diff"]
    print(f"\n🔹 DEFINITIONS DELTA: +{def_diff['added_count']} added, -{def_diff['removed_count']} removed, ~{def_diff['modified_count']} modified")

    # 5. Tables
    tab_diff = diff["tables_diff"]
    print(f"\n🔹 TABLES DELTA: {tab_diff['modified_count']} modified tables")

    print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    main()
