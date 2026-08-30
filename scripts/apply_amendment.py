"""
CLI Tool to Apply Amendments onto Base Standards and Query Temporal Lineage (Steps 13 & 14).
Usage:
    python scripts/apply_amendment.py --base DOC-001 --amendment DOC-012 --effective-date 2026-07-01
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.versioning.amendment_processor import AmendmentProcessor
from ai.versioning.temporal_engine import TemporalEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Consolidate Base Standard + Amendment and audit temporal validity.")
    parser.add_argument("--base", default="DOC-001", help="Base Standard Document ID (e.g. DOC-001)")
    parser.add_argument("--amendment", default="DOC-012", help="Amendment Document ID (e.g. DOC-012)")
    parser.add_argument("--effective-date", default="2026-07-01", help="Effective Date of Amendment (YYYY-MM-DD)")
    args = parser.parse_args()

    base_path = ROOT_DIR / "data" / "normalized" / f"{args.base}.json"
    amd_path = ROOT_DIR / "data" / "normalized" / f"{args.amendment}.json"

    with open(base_path, "r", encoding="utf-8") as f:
        base_doc = json.load(f)
    with open(amd_path, "r", encoding="utf-8") as f:
        amd_doc = json.load(f)

    processor = AmendmentProcessor()
    consolidated = processor.apply_amendment_to_base(
        base_norm_doc=base_doc,
        amendment_norm_doc=amd_doc,
        effective_date=args.effective_date,
        amendment_label=f"Amendment / Revision {args.amendment}",
    )

    temporal_engine = TemporalEngine()

    print("\n" + "=" * 90)
    print(f"📜 AMENDMENT CONSOLIDATION REPORT: {args.base} + {args.amendment}")
    print("=" * 90)
    summary = consolidated["consolidation_summary"]
    print(f"Effective Date:                  {summary['effective_date']}")
    print(f"Total Active Requirements:       {summary['total_active_requirements']}")
    print(f"Total Superseded Requirements:   {summary['total_superseded_requirements']}")
    print("-" * 90)

    # Historical query at 2015-01-01
    reqs_2015 = temporal_engine.filter_effective_requirements(consolidated["requirements"], query_date="2015-01-01")
    print(f"\n📅 Requirements Active in 2015 (Historical): {len(reqs_2015)}")

    # Current query at 2026-08-01
    reqs_2026 = temporal_engine.filter_effective_requirements(consolidated["requirements"], query_date="2026-08-01")
    print(f"📅 Requirements Active in 2026 (Current):    {len(reqs_2026)}")

    print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    main()
