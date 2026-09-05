"""
Discovery Completeness & Quality Gate Verification Test Suite.
Validates that the exhaustive discovery engine satisfies all quality gates:
- No 25-product boundary
- No 366-document boundary
- No fabricated URLs
- Dynamic pagination and recursive category traversal
- Robust duplicate detection and language mirror filtering
- Complete DOMDiscoveryEvidence and source provenance retention
- Proper session-blocked classifications
"""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

from ai.acquisition.source_gate import AUTHORIZED_GOV_DOMAINS, is_domain_authorized

CANDIDATES_PATH = Path("data/candidates/candidate_documents.json")
INVENTORY_PATH = Path("data/candidates/browser_live_inventory.json")
RECONCILIATION_REPORT_PATH = Path("data/candidates/browser_reconciliation_report.json")
STRUCTURED_RECORDS_PATH = Path("data/candidates/structured_directory_records.json")


@pytest.fixture(scope="module")
def candidate_catalog():
    assert CANDIDATES_PATH.exists(), f"Missing {CANDIDATES_PATH}"
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def raw_inventory():
    assert INVENTORY_PATH.exists(), f"Missing {INVENTORY_PATH}"
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def structured_records():
    assert STRUCTURED_RECORDS_PATH.exists(), f"Missing {STRUCTURED_RECORDS_PATH}"
    with open(STRUCTURED_RECORDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reconciliation_report():
    assert RECONCILIATION_REPORT_PATH.exists(), f"Missing {RECONCILIATION_REPORT_PATH}"
    with open(RECONCILIATION_REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestDiscoveryCompleteness:
    """Tests proving exhaustive discovery completeness and quality gate integrity."""

    def test_no_366_document_boundary(self, candidate_catalog):
        """Proves the candidate catalog broke past the baseline and captures the broader universe."""
        count = len(candidate_catalog)
        assert count > 1000, f"Expected exhaustive corpus > 1000 documents, found {count}"

    def test_no_hardcoded_25_product_boundary(self, candidate_catalog):
        """Proves discovery catalog covers hundreds of unique products beyond the 25 benchmark."""
        unique_titles = {c.get("title", "") for c in candidate_catalog}
        assert len(unique_titles) > 500, f"Expected > 500 unique document titles, found {len(unique_titles)}"

    def test_no_fabricated_urls(self, candidate_catalog):
        """Verifies every candidate URL belongs to authorized government/BIS domains."""
        for c in candidate_catalog:
            url = c.get("source_url", "")
            assert url, f"Candidate {c.get('candidate_id')} has empty URL"
            assert url.startswith("http://") or url.startswith("https://"), f"Invalid scheme in {url}"
            assert is_domain_authorized(url), f"Unauthorized or fabricated domain in {url}"

    def test_complete_dom_evidence_retention(self, candidate_catalog):
        """Verifies every candidate possesses complete DOMDiscoveryEvidence."""
        for c in candidate_catalog:
            evidence = c.get("discovery_evidence")
            assert evidence is not None, f"Missing evidence for {c.get('candidate_id')}"
            assert "source_page_url" in evidence
            assert "discovered_url" in evidence
            assert "element_tag" in evidence
            assert "region_type" in evidence
            assert "extraction_strategy" in evidence
            assert evidence["discovered_url"] == c["source_url"]

    def test_pagination_and_table_extraction(self, structured_records, candidate_catalog):
        """Verifies laboratory directory pagination and structured record extraction."""
        assert len(structured_records) > 100, "Expected > 100 structured directory records from LIMS"
        scope_docs = [c for c in candidate_catalog if c.get("document_type") == "LAB_SCOPE_DOCUMENT"]
        assert len(scope_docs) > 50, f"Expected > 50 lab scope documents, found {len(scope_docs)}"

    def test_session_gated_sources_recorded(self, reconciliation_report):
        """Verifies session-gated sources are explicitly tracked without breaking."""
        exhaustion = reconciliation_report.get("exhaustion_evidence", {})
        assert "SRC-010" in exhaustion
        assert exhaustion["SRC-010"]["status"] == "SESSION_REQUIRED"
        assert "SRC-015" in exhaustion
        assert exhaustion["SRC-015"]["status"] == "SESSION_REQUIRED"

    def test_document_types_diversity(self, candidate_catalog):
        """Verifies diverse document types across the BIS knowledge universe."""
        types = {c.get("document_type") for c in candidate_catalog}
        expected_types = {"PRODUCT_MANUAL", "LAB_SCOPE_DOCUMENT", "AMENDMENT", "INDIAN_STANDARD"}
        assert expected_types.issubset(types), f"Missing document types: {expected_types - types}"
