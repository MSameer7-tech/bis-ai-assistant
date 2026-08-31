"""
CLI Runner for Automated BIS Standards Discovery & Acquisition.
Usage:
    PYTHONPATH=. .venv/bin/python scripts/crawl_bis_sources.py --limit 5 --dry-run
    PYTHONPATH=. .venv/bin/python scripts/crawl_bis_sources.py --domain electrical --limit 1 --auto-ingest
"""

import argparse
import json
import logging
from pprint import pprint
import sys

from ai.acquisition.crawler import BISCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="BIS Standards Discovery and Acquisition Crawler")
    parser.add_argument("--domain", type=str, default=None, help="Target product domain (e.g. electrical, construction_civil)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of standards to discover")
    parser.add_argument("--dry-run", action="store_true", help="Scan and assess without downloading or indexing")
    parser.add_argument("--auto-ingest", action="store_true", help="Automatically ingest discovered new or modified documents")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion even if unchanged")
    parser.add_argument("--include-notifications", action="store_true", help="Include regulatory QCOs and gazette notifications")

    args = parser.parse_args()

    crawler = BISCrawler()

    print("=" * 80)
    print("🌐 BIS STANDARDS AUTOMATED DISCOVERY & ACQUISITION")
    print(f"Domain Filter:       {args.domain or 'All Domains'}")
    print(f"Discovery Limit:     {args.limit or 'Unlimited'}")
    print(f"Mode:                {'DRY RUN (Assessment Only)' if args.dry_run else ('AUTO-INGEST' if args.auto_ingest else 'DISCOVERY ONLY')}")
    print(f"Force Reprocess:     {args.force}")
    print("=" * 80)

    report = crawler.crawl(
        domain=args.domain,
        limit=args.limit,
        auto_ingest=args.auto_ingest,
        dry_run=args.dry_run,
        force=args.force,
        include_notifications=args.include_notifications,
    )

    print("\n📊 DISCOVERY & ASSESSMENT SUMMARY:")
    print(f"Total Discovered:    {report['discovered_count']}")
    print(f"🟢 UNCHANGED:        {report['unchanged_count']}")
    print(f"🔵 NEW:              {report['new_count']}")
    print(f"🟡 MODIFIED:         {report['modified_count']}")
    print(f"❌ INVALID:          {report['invalid_count']}")

    if report["new_items"]:
        print("\n🔵 Discovered NEW Standards:")
        for item in report["new_items"]:
            print(f"  • [{item['domain']}] {item['standard_number']} - {item['title'][:60]}...")

    if report["unchanged_items"]:
        print("\n🟢 Discovered UNCHANGED Standards:")
        for item in report["unchanged_items"][:5]:
            print(f"  • [{item['domain']}] {item['standard_number']} ({item['document_id']}) -> {item['reason']}")
        if len(report["unchanged_items"]) > 5:
            print(f"  ... and {len(report['unchanged_items']) - 5} more unchanged standards.")

    if report["ingestion_results"]:
        print("\n🚀 INGESTION PIPELINE RESULTS:")
        for res in report["ingestion_results"]:
            print(f"  • {res['standard_number']} ({res.get('document_id')}): {res['status']}")

    print("=" * 80)


if __name__ == "__main__":
    main()
