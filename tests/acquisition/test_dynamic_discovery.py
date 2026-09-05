"""
Comprehensive Tests for Phase 3 Final Discovery Cleanup.
Validates:
1. Zero hardcoded candidate lists in discovery strategies.
2. Zero ps_products.json or ps_coverage dependency (at source and AST levels).
3. All candidate URLs resolve to whitelisted authoritative domains.
4. Navigation/chrome/language-switcher links are strictly rejected.
5. Session-gated sources (SRC-010, SRC-015) are explicitly classified as SESSION_REQUIRED.
6. Retired endpoints are updated to authoritative endpoints (e.g. LIMS for laboratories).
7. SRC-018 statutory document classification correctly categorizes ACT, RULE, REGULATION, NOTIFICATION, AMENDMENT, ADMINISTRATIVE_DOCUMENT.
8. Cross-document relationships (Standard <-> Amendment, Standard <-> QCO, Standard <-> Manual, Standard <-> SIT) are preserved.
9. Deduplication and exclusion metrics are accurate.
"""
import ast
import inspect
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.acquisition.discovery.base import BaseDiscoveryStrategy, DiscoveryMetrics
from ai.acquisition.discovery.html_search import HTMLSearchStrategy, parse_standards_from_html, parse_labs_from_html
from ai.acquisition.discovery.html_catalog import HTMLCatalogStrategy, parse_directory_tables, parse_compulsory_cert_links
from ai.acquisition.discovery.pdf_links import PDFLinkDiscoveryStrategy, parse_pdf_anchors, classify_statutory_document
from ai.acquisition.discovery.gazette_search import GazetteSearchStrategy, parse_gazette_entries
from ai.acquisition.discovery.registry_query import RegistryQueryStrategy, parse_registry_table
from ai.acquisition.discovery.direct_html import DirectHTMLStrategy, parse_portal_articles
from ai.acquisition.discovery.link_filter import (
    filter_document_links,
    is_navigation_url,
    is_navigation_title,
    matches_document_pattern,
    LinkFilterMetrics
)
from ai.acquisition.discovery_engine import DiscoveryEngine, CandidateDocument
from ai.acquisition.source_gate import AUTHORIZED_GOV_DOMAINS, is_domain_authorized


# ────────────────────────────────────────────────────────────
# 1. INDEPENDENCE FROM ps_products.json
# ────────────────────────────────────────────────────────────

DISCOVERY_MODULES = [
    "ai.acquisition.discovery.base",
    "ai.acquisition.discovery.html_search",
    "ai.acquisition.discovery.html_catalog",
    "ai.acquisition.discovery.pdf_links",
    "ai.acquisition.discovery.gazette_search",
    "ai.acquisition.discovery.registry_query",
    "ai.acquisition.discovery.direct_html",
    "ai.acquisition.discovery.link_filter",
    "ai.acquisition.discovery_engine",
]


class TestPsProductsIndependence:
    """Proves discovery is dynamically driven by source registries, not bounded by ps_products.json."""

    @pytest.mark.parametrize("module_name", DISCOVERY_MODULES)
    def test_no_ps_products_reference_in_source(self, module_name):
        """Source code of every discovery module must not mention ps_products."""
        mod = sys.modules.get(module_name) or __import__(module_name, fromlist=[""])
        source = inspect.getsource(mod)
        assert "ps_products" not in source, f"{module_name} references ps_products"
        assert "ps_coverage" not in source, f"{module_name} references ps_coverage"

    @pytest.mark.parametrize("module_name", DISCOVERY_MODULES)
    def test_no_ps_products_import_in_ast(self, module_name):
        """AST-level check: no import of ps_products paths."""
        mod = sys.modules.get(module_name) or __import__(module_name, fromlist=[""])
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_path = ""
                if isinstance(node, ast.ImportFrom) and node.module:
                    module_path = node.module
                assert "ps_products" not in module_path, f"{module_name} imports ps_products"
                assert "ps_coverage" not in module_path, f"{module_name} imports ps_coverage"

    def test_discovery_engine_does_not_load_ps_products(self):
        """DiscoveryEngine.__init__ operates completely independently of benchmark files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reg_path = Path(tmpdir) / "source_registry.json"
            reg_path.write_text(json.dumps({"sources": []}))
            engine = DiscoveryEngine(registry_path=reg_path)
            candidates = engine.discover_all_candidates()
            assert candidates == []


# ────────────────────────────────────────────────────────────
# 2. ZERO HARDCODED CANDIDATE LISTS
# ────────────────────────────────────────────────────────────

class TestNoHardcodedLists:
    """Ensures strategies extract records dynamically, with no static document candidate tables."""

    @pytest.mark.parametrize("module_name", DISCOVERY_MODULES)
    def test_no_static_records_list_in_source(self, module_name):
        mod = sys.modules.get(module_name) or __import__(module_name, fromlist=[""])
        source = inspect.getsource(mod)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("records", "candidates_list", "hardcoded_docs"):
                        if isinstance(node.value, ast.List) and len(node.value.elts) > 3:
                            pytest.fail(f"{module_name} contains hardcoded list '{target.id}' at line {node.lineno}")


# ────────────────────────────────────────────────────────────
# 3. LINK NOISE & NAVIGATION FILTERING
# ────────────────────────────────────────────────────────────

class TestLinkNoiseFilter:
    """Verifies that website chrome, login links, language switchers, and non-docs are rejected."""

    def test_navigation_urls_rejected(self):
        nav_urls = [
            "https://www.bis.gov.in/",
            "https://www.bis.gov.in/wp-login.php",
            "https://www.bis.gov.in/contact-us/",
            "https://www.bis.gov.in/about-us/",
            "https://www.bis.gov.in/privacy-policy/",
            "https://www.bis.gov.in/sitemap/",
            "https://www.bis.gov.in/cart/",
            "https://www.bis.gov.in/my-account/",
            "javascript:void(0)",
            "mailto:support@bis.gov.in",
        ]
        for url in nav_urls:
            assert is_navigation_url(url) is True, f"Failed to reject nav URL: {url}"

    def test_noise_query_parameters_rejected(self):
        noisy_urls = [
            "https://www.bis.gov.in/page/?lang=hi",
            "https://www.bis.gov.in/page/?lang=ta",
            "https://www.manakonline.in/MANAK/sessionExpire",
        ]
        for url in noisy_urls:
            assert is_navigation_url(url) is True, f"Failed to reject noisy query: {url}"

    def test_nav_titles_rejected(self):
        nav_titles = [
            "Home", "About Us", "Contact Us", "Login", "Skip to main content",
            "Privacy Policy", "Sitemap", "Accessibility", "हिन्दी", "English", "Overview"
        ]
        for t in nav_titles:
            assert is_navigation_title(t) is True, f"Failed to reject nav title: {t}"

    def test_filter_document_links_calculates_exclusion_metrics(self):
        raw = [
            {"url": "https://www.bis.gov.in/standards/IS-1786-2008.pdf", "title": "IS 1786 : 2008 Steel Bars"},
            {"url": "https://www.bis.gov.in/contact-us/", "title": "Contact Us"},
            {"url": "https://www.bis.gov.in/about-us/?lang=hi", "title": "About Us"},
            {"url": "https://unauthorized-domain.com/doc.pdf", "title": "External Doc"},
            {"url": "https://www.bis.gov.in/standards/IS-1786-2008.pdf", "title": "Duplicate IS 1786"},
        ]
        valid, metrics = filter_document_links(raw, "SRCF-001", AUTHORIZED_GOV_DOMAINS)
        assert len(valid) == 1
        assert valid[0]["url"] == "https://www.bis.gov.in/standards/IS-1786-2008.pdf"
        assert metrics.raw_links == 5
        assert metrics.valid_candidates == 1
        assert metrics.excluded_navigation >= 1
        assert metrics.excluded_duplicate >= 1
        assert metrics.excluded_invalid_path >= 1


# ────────────────────────────────────────────────────────────
# 4. STATUTORY DOCUMENT CLASSIFICATION (SRC-018)
# ────────────────────────────────────────────────────────────

class TestStatutoryClassification:
    """Verifies that SRC-018 documents are classified accurately without tagging everything as STATUTORY_ACT."""

    def test_act_classification(self):
        assert classify_statutory_document("The Bureau of Indian Standards Act, 2016", "/acts/BIS-ACT-2016.pdf") == "ACT"
        assert classify_statutory_document("Act No. 11 of 2016", "/acts/Act11_2016.pdf") == "ACT"

    def test_rule_classification(self):
        assert classify_statutory_document("Bureau of Indian Standards Rules, 2018", "/acts/BIS-RULES-2018.pdf") == "RULE"

    def test_regulation_classification(self):
        assert classify_statutory_document("Bureau of Indian Standards (Conformity Assessment) Regulations, 2018", "/regs/Conformity.pdf") == "REGULATION"
        assert classify_statutory_document("Bureau of Indian Standards (Hallmarking) Regulations, 2018", "/regs/Hallmarking.pdf") == "REGULATION"

    def test_administrative_document_classification(self):
        admin_samples = [
            ("Handbook for Interns", "/docs/Intern_Handbook.pdf"),
            ("Revised Fee Structure for Certification", "/docs/Fee_Structure_2023.pdf"),
            ("Organisation Chart - Dec 2024", "/docs/Organisation-Chart.pdf"),
            ("Annual Report 2022-23", "/docs/Annual-Report-2022-23.pdf"),
            ("GIGW Compliance Certificate", "/docs/Certificates_GIGW.pdf"),
            ("List of 89 Centres provided Central Assistance", "/docs/Centres_Assistance.pdf"),
        ]
        for title, url in admin_samples:
            assert classify_statutory_document(title, url) == "ADMINISTRATIVE_DOCUMENT", f"Failed for {title}"

    def test_amendment_classification(self):
        assert classify_statutory_document("Amendment to Conformity Assessment Regulations", "/regs/Amd_2020.pdf") == "AMENDMENT"


# ────────────────────────────────────────────────────────────
# 5. ZERO-YIELD & SESSION-GATED SOURCE RESOLUTION
# ────────────────────────────────────────────────────────────

class TestZeroYieldResolution:
    """Verifies that the 5 zero-yield sources are properly addressed."""

    def test_session_gated_sources_marked_correctly(self):
        with open(ROOT_DIR / "data" / "sources" / "source_registry.json") as f:
            reg = json.load(f)

        src_map = {s["source_id"]: s for s in reg["sources"]}
        assert src_map["SRC-010"]["status"] == "SESSION_REQUIRED"
        assert src_map["SRC-015"]["status"] == "SESSION_REQUIRED"
        assert src_map["SRC-010"]["verification_metadata"]["acquisition_eligible"] is False
        assert src_map["SRC-015"]["verification_metadata"]["acquisition_eligible"] is False

    def test_lims_endpoints_updated_for_laboratories(self):
        with open(ROOT_DIR / "data" / "sources" / "source_registry.json") as f:
            reg = json.load(f)

        src_map = {s["source_id"]: s for s in reg["sources"]}
        assert "lims.bis.gov.in" in src_map["SRC-012"]["canonical_url"]
        assert "lims.bis.gov.in" in src_map["SRC-013"]["canonical_url"]
        assert src_map["SRC-012"]["host"] == "lims.bis.gov.in"
        assert src_map["SRC-013"]["host"] == "lims.bis.gov.in"
        assert is_domain_authorized(src_map["SRC-012"]["canonical_url"]) is True
        assert is_domain_authorized(src_map["SRC-013"]["canonical_url"]) is True

    def test_session_gated_sources_do_not_throw_errors(self):
        engine = DiscoveryEngine()
        cands_10, m_10 = engine.discover_from_endpoint("SRC-010")
        assert cands_10 == []
        assert "SESSION_REQUIRED" in m_10.source_errors[0]

        cands_15, m_15 = engine.discover_from_endpoint("SRC-015")
        assert cands_15 == []
        assert "SESSION_REQUIRED" in m_15.source_errors[0]


# ────────────────────────────────────────────────────────────
# 6. CROSS-DOCUMENT RELATIONSHIP INTEGRITY
# ────────────────────────────────────────────────────────────

class TestCrossDocumentRelationships:
    """Verifies that discovered candidates preserve formal relationship metadata."""

    def test_amendment_preserves_parent_relationship(self):
        strat = PDFLinkDiscoveryStrategy()
        src = {
            "source_id": "SRC-003",
            "source_family_id": "SRCF-002",
            "canonical_url": "https://www.bis.gov.in/amendments/"
        }
        cands, _ = strat.discover(src)
        assert len(cands) > 0
        for c in cands:
            assert c.relationship_type == "AMENDS"
            assert c.parent_document_id is not None
            assert c.related_standard_id is not None

    def test_product_manual_preserves_guideline_relationship(self):
        strat = PDFLinkDiscoveryStrategy()
        src = {
            "source_id": "SRC-006",
            "source_family_id": "SRCF-004",
            "canonical_url": "https://www.bis.gov.in/product-manuals/"
        }
        cands, _ = strat.discover(src)
        assert len(cands) > 0
        for c in cands:
            assert c.relationship_type == "CERTIFICATION_GUIDELINE_FOR"
            assert c.parent_document_id is not None

    def test_sit_schedule_preserves_testing_relationship(self):
        strat = PDFLinkDiscoveryStrategy()
        src = {
            "source_id": "SRC-007",
            "source_family_id": "SRCF-005",
            "canonical_url": "https://www.bis.gov.in/sit/"
        }
        cands, _ = strat.discover(src)
        assert len(cands) > 0
        for c in cands:
            assert c.relationship_type == "TESTING_SCHEDULE_FOR"
            assert c.parent_document_id is not None

    def test_qco_preserves_mandate_relationship(self):
        strat = GazetteSearchStrategy()
        src = {
            "source_id": "SRC-004",
            "source_family_id": "SRCF-003",
            "canonical_url": "https://www.egazette.gov.in/"
        }
        cands, _ = strat.discover(src)
        assert len(cands) > 0
        qcos_with_std = [c for c in cands if c.related_standard_id]
        assert len(qcos_with_std) > 0
        for c in qcos_with_std:
            assert c.relationship_type == "MANDATES_CERTIFICATION_FOR"
