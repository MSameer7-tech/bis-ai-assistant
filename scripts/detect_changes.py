"""
CLI script to scan acquired BIS documents for changes and verify data freshness.
Usage:
    python scripts/detect_changes.py
    python scripts/detect_changes.py --document-id DOC-001
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.ingestion.change_detector import ChangeDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Scan BIS documents for content modifications and data freshness.")
    parser.add_argument("--document-id", help="Optional specific Document ID to check (e.g. DOC-001)")
    args = parser.parse_args()

    detector = ChangeDetector()

    if args.document_id:
        report = detector.check_document_change(args.document_id)
        print("\n" + "=" * 75)
        print(f"🔍 Change Detection Report for {args.document_id}:")
        print("=" * 75)
        print(f"   • Has Changed:     {report.get('has_changed')}")
        print(f"   • Change Type:     {report.get('change_type')}")
        print(f"   • Current Hash:    {str(report.get('current_hash'))[:20]}...")
        print(f"   • Action Required: {report.get('action_required')}")
        print("=" * 75 + "\n")
    else:
        summary = detector.scan_all_sources()
        print("\n" + "=" * 85)
        print(f"🔍 Data Freshness & Change Detection Audit ({summary['scanned_count']} Documents Scanned):")
        print("=" * 85)
        print(f"{'Doc ID':<10} | {'Status':<12} | {'Action Required':<22} | {'Current Hash'}")
        print("-" * 85)

        for d in summary["details"]:
            doc_id = d.get("document_id", "UNKNOWN")
            status = "CHANGED" if d.get("has_changed") else "UP TO DATE"
            action = d.get("action_required", "none")
            h_str = str(d.get("current_hash", "-"))[:24] + "..." if d.get("current_hash") else "-"
            print(f"{doc_id:<10} | {status:<12} | {action:<22} | {h_str}")

        print("=" * 85)
        print(f"Summary: {summary['unchanged_count']} up-to-date, {summary['changed_count']} changed, {summary['missing_count']} missing.\n")


if __name__ == "__main__":
    main()
