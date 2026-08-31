"""
Unit tests for Crawler Data Models (ai/acquisition/crawler_models.py).
Verifies strict validation of standard numbers, taxonomy domains, URLs, and ISO dates.
"""

import pytest
from pydantic import ValidationError

from ai.acquisition.crawler_models import (
    DiscoveredStandard,
    DiscoveryBatchReport,
    DiscoveryDocumentType,
    normalize_standard_number,
)


def test_discovered_standard_valid_creation():
    doc = DiscoveredStandard(
        standard_number="IS 1786 : 2024",
        title="High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        edition="Fifth Revision",
        document_type=DiscoveryDocumentType.STANDARD,
        domain="construction_civil",
        category="steel_metals",
        product_type="high_strength_deformed_steel_bars",
        source_url="https://standardsbis.bsbedge.com/is1786_2024",
        pdf_url="https://standardsbis.bsbedge.com/pdf/is1786_2024.pdf",
        authority="Bureau of Indian Standards (CED 54)",
        pub_date="2024-07-01",
        valid_from="2024-07-01",
        valid_until=None,
    )
    assert doc.standard_number == "IS 1786 : 2024"
    assert doc.domain == "construction_civil"
    assert doc.source_url == "https://standardsbis.bsbedge.com/is1786_2024"
    assert doc.pub_date == "2024-07-01"


def test_standard_number_normalization():
    assert normalize_standard_number("IS1786:2024") == "IS 1786 : 2024"
    assert normalize_standard_number("IS 374:2019") == "IS 374 : 2019"
    assert normalize_standard_number("is 269 : 2015") == "is 269 : 2015"

    doc = DiscoveredStandard(
        standard_number="IS374:2019",
        title="Electric Ceiling Fans",
        domain="electrical",
        source_url="https://standardsbis.bsbedge.com/is374",
    )
    assert doc.standard_number == "IS 374 : 2019"


def test_invalid_domain_rejected():
    with pytest.raises(ValidationError) as exc_info:
        DiscoveredStandard(
            standard_number="IS 1234 : 2020",
            title="Fake Standard",
            domain="aerospace_rocketry",  # NOT in 7 controlled domains
            source_url="https://standardsbis.bsbedge.com/fake",
        )
    assert "Domain 'aerospace_rocketry' is invalid" in str(exc_info.value)


def test_unknown_domain_allowed():
    doc = DiscoveredStandard(
        standard_number="IS 9999 : 2025",
        title="Unclassified Product Standard",
        domain="unknown",
        source_url="https://standardsbis.bsbedge.com/unclassified",
    )
    assert doc.domain == "unknown"


def test_invalid_document_type_rejected():
    with pytest.raises(ValidationError):
        DiscoveredStandard(
            standard_number="IS 1234 : 2020",
            title="Fake Standard",
            document_type="invalid_doc_type",
            domain="electrical",
            source_url="https://standardsbis.bsbedge.com/fake",
        )


def test_invalid_date_rejected():
    with pytest.raises(ValidationError) as exc_info:
        DiscoveredStandard(
            standard_number="IS 1234 : 2020",
            title="Fake Standard",
            domain="electrical",
            source_url="https://standardsbis.bsbedge.com/fake",
            pub_date="31-08-2026",  # invalid format, must be YYYY-MM-DD
        )
    assert "must be in YYYY-MM-DD or YYYY format" in str(exc_info.value)


def test_invalid_url_rejected():
    with pytest.raises(ValidationError) as exc_info:
        DiscoveredStandard(
            standard_number="IS 1234 : 2020",
            title="Fake Standard",
            domain="electrical",
            source_url="ftp://invalid-server/file",
        )
    assert "Invalid URL protocol" in str(exc_info.value)


def test_markdown_url_normalized():
    doc = DiscoveredStandard(
        standard_number="IS 1234 : 2020",
        title="Fake Standard",
        domain="electrical",
        source_url="[BIS Portal](https://standardsbis.bsbedge.com/doc1234)",
    )
    assert doc.source_url == "https://standardsbis.bsbedge.com/doc1234"


def test_discovery_batch_report_aggregation():
    report = DiscoveryBatchReport(
        discovered_count=2,
        new_count=1,
        unchanged_count=1,
    )
    assert report.discovered_count == 2
    assert report.new_count == 1
    assert report.unchanged_count == 1
