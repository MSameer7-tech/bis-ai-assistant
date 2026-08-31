"""
Integration and Unit Tests for BISCrawler (ai/acquisition/crawler.py).
Verifies multi-source discovery, change detection, dry-run mode, and idempotence.
"""

from ai.acquisition.crawler import BISCrawler
from ai.acquisition.crawler_models import DiscoveredStandard


def test_crawler_discover_deduplication():
    crawler = BISCrawler()
    items = crawler.discover(limit=10)
    assert len(items) <= 10
    assert len(items) > 0
    # Check deduplication
    std_codes = [it.standard_number for it in items]
    assert len(std_codes) == len(set(std_codes))


def test_crawler_dry_run_assessment():
    crawler = BISCrawler()
    report = crawler.crawl(limit=5, dry_run=True)
    assert report["discovered_count"] == 5
    assert report["dry_run"] is True
    assert report["auto_ingest"] is False
    assert (report["unchanged_count"] + report["new_count"] + report["modified_count"]) == 5


def test_crawler_idempotence_on_existing_corpus():
    crawler = BISCrawler()
    # Test on IS 1786 : 2024 which is already in corpus
    report = crawler.crawl(domain="construction_civil", limit=2, dry_run=True)
    assert report["discovered_count"] >= 1
    # Existing standard should be marked UNCHANGED
    unchanged_stds = [it["standard_number"] for it in report["unchanged_items"]]
    assert any("1786" in s or "269" in s for s in unchanged_stds)
