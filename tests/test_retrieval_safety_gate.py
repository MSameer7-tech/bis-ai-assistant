"""
Pytest Test Suite for Retrieval Safety Gate, Entity Compatibility,
Tier 0 Explicit Standard Resolution, Normative Force Preservation, and Entailment (Phase 3).
"""
import pytest
from ai.retrieval.query_parser import QueryParser
from ai.retrieval.product_resolver import ProductResolver, resolve_product
from ai.vectorstore.hybrid_search import HybridSearchEngine
from ai.rag.pipeline import RAGPipeline
from ai.rag.models import AbstentionReason


@pytest.fixture(scope="module")
def pipeline():
    return RAGPipeline()


@pytest.fixture(scope="module")
def resolver():
    return ProductResolver()


class TestTier0ExplicitStandardPrecedence:
    """Tests that explicit IS identifiers strictly override generic phrases."""

    def test_fifth_revision_of_is1786(self, resolver):
        res = resolver.resolve_candidates("What does the fifth revision of IS 1786 specify?")
        assert len(res) > 0
        assert res[0]["standard_number"].startswith("IS 1786")
        assert not any("IS 4246" in r["standard_number"] for r in res)

    def test_is4246_fifth_revision(self, resolver):
        res = resolver.resolve_candidates("What does IS 4246 fifth revision specify?")
        assert len(res) > 0
        assert res[0]["standard_number"].startswith("IS 4246")
        assert not any("IS 1786" in r["standard_number"] for r in res)

    def test_query_parser_explicit_is_code(self):
        sq = QueryParser.parse("What does the fifth revision of IS 1786 specify?")
        assert sq.standard_code == "IS 1786"
        assert sq.revision == "Fifth"


class TestMaterialEntityCompatibilityGate:
    """Tests that unsupported materials (titanium, kevlar, inconel, etc.) trigger hard abstention."""

    def test_titanium_alloy_grade5(self, pipeline):
        ans = pipeline.answer_question("What is the minimum yield strength of titanium alloy Grade 5?")
        assert ans.guardrail_result.refusal_required is True
        assert ans.abstention_type in (AbstentionReason.INCOMPATIBLE_ENTITY, AbstentionReason.INSUFFICIENT_EVIDENCE, AbstentionReason.OUT_OF_SCOPE)
        assert not any("IS 1786" in c.standard_number for c in ans.citations)

    def test_kevlar_tensile_strength(self, pipeline):
        ans = pipeline.answer_question("What is the tensile strength requirement for Kevlar body armor?")
        assert ans.guardrail_result.refusal_required is True
        assert ans.abstention_type in (AbstentionReason.INCOMPATIBLE_ENTITY, AbstentionReason.INSUFFICIENT_EVIDENCE, AbstentionReason.OUT_OF_SCOPE)

    def test_inconel_yield_strength(self, pipeline):
        ans = pipeline.answer_question("What is the yield strength requirement for Inconel 718 aerospace alloy?")
        assert ans.guardrail_result.refusal_required is True
        assert ans.abstention_type in (AbstentionReason.INCOMPATIBLE_ENTITY, AbstentionReason.INSUFFICIENT_EVIDENCE, AbstentionReason.OUT_OF_SCOPE)


class TestCrossDomainTrapGate:
    """Tests that cross-domain mismatches (e.g. air delivery of rebar) trigger abstention."""

    def test_air_delivery_of_rebar(self, pipeline):
        ans = pipeline.answer_question("What is the required air delivery of Fe 500D steel rebar?")
        assert ans.guardrail_result.refusal_required is True

    def test_yield_strength_of_water(self, pipeline):
        ans = pipeline.answer_question("What is the minimum yield strength of packaged drinking water?")
        assert ans.guardrail_result.refusal_required is True

    def test_ph_of_steel_rebar(self, pipeline):
        ans = pipeline.answer_question("What is the pH requirement of steel reinforcement bars?")
        assert ans.guardrail_result.refusal_required is True


class TestNormativeProvenancePreservation:
    """Tests that normative force in chunk flows verbatim into answer."""

    def test_fe500d_normative_informative(self, pipeline):
        ans = pipeline.answer_question("What is the minimum yield strength of Fe 500D?")
        assert ans.production_payload["status"] == "verified"
        assert "- **Normative Status**: INFORMATIVE" in ans.answer
        assert "- **Normative Status**: Mandatory" not in ans.answer


class TestAtomicClaimEntailment:
    """Tests that atomic claims are properly extracted and verified."""

    def test_atomic_claims_verified(self, pipeline):
        ans = pipeline.answer_question("What is the minimum yield strength of Fe 500D?")
        assert len(ans.claims) > 0
        for cl in ans.claims:
            assert cl["verified"] is True
            assert cl["entailment_score"] > 0.0
            assert cl["text"] != "None"
