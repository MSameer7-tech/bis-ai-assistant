"""
Unit Test Suite for Phase 5: Production Intelligence & Answer Engine.
Verifies all intelligence layers:
- QueryUnderstandingEngine (5A)
- UnifiedHybridRetriever (5B)
- CertificationChainReasoner (5D)
- RegulatoryTimelineEngine (5E)
- RegulatorySafetyLayer (5G)
- StandardizedCitationFormatter (5F)
- ProductionIntelligenceEngine (5C)
"""
import pytest
from ai.intelligence.query_understanding import QueryUnderstandingEngine, QueryIntent
from ai.intelligence.hybrid_retriever import UnifiedHybridRetriever
from ai.intelligence.chain_reasoner import CertificationChainReasoner
from ai.intelligence.timeline_engine import RegulatoryTimelineEngine
from ai.intelligence.safety_layer import RegulatorySafetyLayer, SafetyVerdict
from ai.intelligence.citation_formatter import StandardizedCitationFormatter
from ai.intelligence.answer_generator import ProductionIntelligenceEngine


@pytest.fixture
def parser():
    return QueryUnderstandingEngine()


@pytest.fixture
def retriever():
    return UnifiedHybridRetriever()


@pytest.fixture
def chain_reasoner():
    return CertificationChainReasoner()


@pytest.fixture
def timeline_engine():
    return RegulatoryTimelineEngine()


@pytest.fixture
def safety_layer():
    return RegulatorySafetyLayer()


@pytest.fixture
def formatter():
    return StandardizedCitationFormatter()


@pytest.fixture
def intelligence_engine():
    return ProductionIntelligenceEngine()


def test_5a_query_understanding_multi_intent(parser):
    q = "I manufacture 5-star ceiling fans. Do I need BIS certification and what tests are required?"
    res = parser.parse_query(q)
    assert res.canonical_product is not None
    assert "Ceiling Fan" in res.canonical_product
    assert QueryIntent.MANDATORY_STATUS in res.intents
    assert QueryIntent.TESTING_REQUIREMENTS in res.intents
    assert res.is_multi_hop is True
    assert res.scheme_hint == "SCHEME-I"


def test_5a_query_understanding_crs_battery(parser):
    q = "Is BIS registration required for Lithium Ion Batteries under CRS?"
    res = parser.parse_query(q)
    assert res.canonical_product is not None
    assert "Lithium" in res.canonical_product
    assert res.scheme_hint == "SCHEME-II"
    assert QueryIntent.MANDATORY_STATUS in res.intents


def test_5b_hybrid_retrieval_graph_traversal(parser, retriever):
    q = "What tests and laboratories apply to Electric Ceiling Fans under IS 374?"
    parsed = parser.parse_query(q)
    res = retriever.retrieve(parsed, top_k=3)
    assert len(res.graph_nodes) > 0
    assert any(n.relation == "GOVERNED_BY_STANDARD" for n in res.graph_nodes)


def test_5d_certification_chain_ceiling_fans(chain_reasoner):
    res = chain_reasoner.resolve_chain("Electric Ceiling Fans")
    assert res.standard_number == "IS 374"
    assert res.scheme_code == "SCHEME-I"
    assert res.is_qco_mandatory is True
    assert res.chain_status == "COMPLETE"
    assert len(res.nodes) == 9
    assert all(n.is_present for n in res.nodes)
    assert "IS 374" in res.compliance_summary


def test_5d_certification_chain_tmt_rebars(chain_reasoner):
    res = chain_reasoner.resolve_chain("IS 1786")
    assert res.standard_number == "IS 1786"
    assert res.scheme_code == "SCHEME-I"
    assert res.is_qco_mandatory is True
    assert res.chain_status == "COMPLETE"


def test_5d_certification_chain_crs_batteries(chain_reasoner):
    res = chain_reasoner.resolve_chain("IS 16046 (Part 2)")
    assert res.scheme_code == "SCHEME-II"
    assert res.is_qco_mandatory is True
    assert res.chain_status == "COMPLETE"


def test_5e_timeline_engine_historical_edition(timeline_engine):
    res = timeline_engine.resolve_timeline("IS 374", as_of_date="2020-01-01")
    assert "IS 374" in res.active_standard_edition
    assert res.target_date == "2020-01-01"
    assert len(res.events) > 0


def test_5g_safety_layer_unsupported_material(parser, retriever, safety_layer):
    q = "What is the tensile strength of titanium alloy Grade 5?"
    parsed = parser.parse_query(q)
    retrieved = retriever.retrieve(parsed, top_k=2)
    check = safety_layer.evaluate_safety(parsed, retrieved)
    assert check.is_safe_to_generate is False
    assert check.verdict == SafetyVerdict.BLOCK_OUT_OF_SCOPE
    assert "Titanium" in check.refusal_message


def test_5g_safety_layer_cross_domain_trap(parser, retriever, safety_layer):
    q = "What is the air delivery of steel reinforcement bars?"
    parsed = parser.parse_query(q)
    retrieved = retriever.retrieve(parsed, top_k=2)
    check = safety_layer.evaluate_safety(parsed, retrieved)
    assert check.is_safe_to_generate is False
    assert check.verdict == SafetyVerdict.BLOCK_CROSS_DOMAIN_TRAP


def test_5c_end_to_end_intelligence_answer_valid(intelligence_engine):
    q = "I manufacture 5-star ceiling fans. Do I need BIS certification and what tests are required?"
    ans = intelligence_engine.process_query(q)
    assert ans.status in ("VERIFIED", "HISTORICAL_CONTEXT")
    assert ans.verdict["is_mandatory"] is True
    assert ans.verdict["standard"] == "IS 374"
    assert ans.verdict["scheme"] == "SCHEME-I"
    assert ans.certification_chain is not None
    assert ans.certification_chain.chain_status == "COMPLETE"
    assert len(ans.test_requirements) > 0
    assert len(ans.evidence_records) > 0


def test_5c_end_to_end_intelligence_answer_refusal(intelligence_engine):
    q = "What is the yield strength of packaged drinking water?"
    ans = intelligence_engine.process_query(q)
    assert ans.status == "REFUSAL"
    assert ans.verdict["verdict"] == "REFUSAL"
    assert "Regulatory Safety Notice" in ans.answer_markdown
