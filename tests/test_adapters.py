"""
Unit tests for BIS Source Adapters (ai/acquisition/sources/).
Verifies discovery, domain filtering, limit constraints, and metadata fetching.
"""

from ai.acquisition.sources.bis_standards import BISStandardsAdapter
from ai.acquisition.sources.bis_notifications import BISNotificationsAdapter
from ai.acquisition.crawler_models import DiscoveryDocumentType


def test_bis_standards_adapter_discovery_limit():
    adapter = BISStandardsAdapter()
    results = adapter.discover(limit=5)
    assert len(results) == 5
    for item in results:
        assert item.standard_number.startswith("IS ")
        assert item.domain in ["electrical", "electronics_it", "construction_civil", "food_agriculture", "mechanical", "medical_safety", "chemicals_materials"]


def test_bis_standards_adapter_domain_filter():
    adapter = BISStandardsAdapter()
    results = adapter.discover(domain="electrical")
    assert len(results) > 0
    for item in results:
        assert item.domain == "electrical"


def test_bis_standards_adapter_fetch_metadata():
    adapter = BISStandardsAdapter()
    meta = adapter.fetch_metadata("IS 1786 : 2024")
    assert meta is not None
    assert "High Strength Deformed Steel Bars" in meta.title
    assert meta.domain == "construction_civil"


def test_bis_notifications_adapter_discovery():
    adapter = BISNotificationsAdapter()
    results = adapter.discover()
    assert len(results) >= 3
    for item in results:
        assert item.document_type in [DiscoveryDocumentType.QCO, DiscoveryDocumentType.GAZETTE_NOTIFICATION]
