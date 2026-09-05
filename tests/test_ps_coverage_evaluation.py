"""
PS Coverage & Query Evaluation Test Suite (Phase Q).
Validates 100% PS product resolution, query understanding, and safe refusal.
"""
import json
import pytest
from pathlib import Path

from ai.coverage.product_resolver import ProductResolver
from ai.intelligence.query_understanding import QueryUnderstandingEngine
from ai.intelligence.chain_reasoner import CertificationChainReasoner
from ai.coverage.auditor import PSCoverageAuditor

ROOT_DIR = Path(__file__).resolve().parent.parent
PS_QUERIES_PATH = ROOT_DIR / "tests" / "evaluation" / "ps_queries.json"
MANIFEST_PATH = ROOT_DIR / "data" / "ps_coverage" / "ps_products.json"
REGISTRY_PATH = ROOT_DIR / "data" / "ps_coverage" / "source_registry.json"


@pytest.fixture(scope="module")
def resolver():
    return ProductResolver(manifest_path=MANIFEST_PATH)


@pytest.fixture(scope="module")
def query_engine():
    return QueryUnderstandingEngine()


@pytest.fixture(scope="module")
def chain_reasoner():
    return CertificationChainReasoner()


@pytest.fixture(scope="module")
def auditor():
    return PSCoverageAuditor(manifest_path=MANIFEST_PATH, registry_path=REGISTRY_PATH)


def test_ps_coverage_audit_100_percent(auditor):
    """Verifies that the coverage audit achieves 100% full coverage across all 25 PS commodities."""
    report = auditor.audit()
    assert report["total_ps_products"] == 25
    assert report["fully_covered_count"] == 25
    assert report["partially_covered_count"] == 0
    assert report["uncovered_count"] == 0
    assert report["overall_ps_coverage_pct"] == 100.0
    assert report["gate_passed"] is True


def test_all_25_ps_products_resolvable(resolver):
    """Verifies that every single PS product in manifest resolves by ID, canonical name, and standard."""
    products = resolver.get_all_products()
    assert len(products) == 25
    for p in products:
        m_name = resolver.resolve_from_term(p.canonical_name)
        assert m_name is not None, f"Failed to resolve by canonical name: {p.canonical_name}"
        assert m_name.product.id == p.id

        m_std = resolver.resolve_from_standard(p.canonical_standard)
        assert m_std is not None, f"Failed to resolve by standard: {p.canonical_standard}"
        assert p.canonical_standard.upper() in m_std.product.canonical_standard.upper() or m_std.product.canonical_standard.upper() in p.canonical_standard.upper()


def test_ps_query_suite_resolution(query_engine, chain_reasoner):
    """Verifies end-to-end intent, standard, and scheme resolution on benchmark queries."""
    with open(PS_QUERIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for suite in data.get("test_suites", []):
        expected_std = suite["expected_standard"]
        expected_scheme = suite["expected_scheme"]

        for q_item in suite.get("queries", []):
            q_text = q_item["query"]
            parsed = query_engine.parse_query(q_text)
            assert parsed.canonical_product is not None, f"Query '{q_text}' failed product resolution"
            assert parsed.standard_code is not None, f"Query '{q_text}' failed standard resolution"
            assert expected_std in parsed.standard_code, f"Expected {expected_std} in {parsed.standard_code} for query '{q_text}'"

            # Check Chain Reasoner
            target_term = parsed.standard_code or parsed.canonical_product
            chain = chain_reasoner.resolve_chain(target_term)
            assert chain is not None
            assert chain.scheme_code == expected_scheme, f"Expected {expected_scheme}, got {chain.scheme_code} for query '{q_text}'"


def test_adversarial_abstention_and_safe_refusal(query_engine, resolver):
    """Verifies that non-existent / out-of-scope commodities are cleanly rejected without hallucination."""
    with open(PS_QUERIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for adv in data.get("adversarial_tests", []):
        q_text = adv["query"]
        ps_match = resolver.resolve_from_query(q_text)
        assert ps_match is None, f"Adversarial query '{q_text}' should NOT match any PS product"

        parsed = query_engine.parse_query(q_text)
        assert parsed.canonical_product is None, f"Parsed query for '{q_text}' should have canonical_product=None"
