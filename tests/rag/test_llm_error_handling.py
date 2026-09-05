"""
Phase 8.1 — LLM Error Handling, Structured Refusal, and Provider Error Semantics Tests.
Tests cover: valid answers, structured refusals, provider errors, error state semantics.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from ai.rag.pipeline import RAGPipeline
from ai.rag.generator import ProviderResponse, get_llm_provider, GroqLLMProvider
from ai.rag.models import RAGAnswer, RAGContext, RetrievedChunk, AbstentionReason
from ai.verification.claim_verifier import ClaimVerifier
from ai.rag.schema import AtomicClaim


# ---------------------------------------------------------------------------
# 1. Groq model configuration with currently supported model
# ---------------------------------------------------------------------------
def test_groq_model_configuration():
    with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_MODEL": "qwen/qwen3.8-27b"}):
        provider = get_llm_provider()
        assert isinstance(provider, GroqLLMProvider)
        assert provider.model_name == "qwen/qwen3.8-27b"


# ---------------------------------------------------------------------------
# Shared mock pipeline fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_pipeline():
    pipeline = RAGPipeline()

    # Mock retrieval
    pipeline.retriever = MagicMock()
    pipeline.retriever.retrieve.return_value = [
        RetrievedChunk(
            chunk_id="C1", document_id="D1", source_id="S1",
            standard_number="IS 123", clause_number="1",
            chunk_type="req", normative_force="mandatory",
            temporal_status="current", score=1.0,
            text="Test text about household refrigerators.",
            content_hash="hash"
        )
    ]

    # Mock context builder — must return a proper RAGContext
    pipeline.context_builder = MagicMock()
    pipeline.context_builder.build_context.return_value = RAGContext(
        formatted_prompt_context="Context",
        evidence_blocks=["Context"],
        chunks=[],
        total_tokens_estimate=10
    )

    # Mock citation extractor to avoid downstream failures on SUCCESS path
    pipeline.citation_extractor = MagicMock()
    pipeline.citation_extractor.extract_citations.return_value = []

    return pipeline


# ---------------------------------------------------------------------------
# A. Valid grounded JSON answer — successful generation follows normal pipeline
# ---------------------------------------------------------------------------
def test_valid_grounded_json_answer(mock_pipeline):
    mock_provider = MagicMock()
    mock_provider.generate_structured_answer.return_value = ProviderResponse(
        generated_answer="IS 123 specifies requirements for household refrigerators.",
        claims=[{"text": "IS 123 covers refrigerators", "standard_number": "IS 123", "clause": "1"}],
        citations=[{"standard_number": "IS 123", "clause": "1", "chunk_id": "C1"}],
        model="test", model_version="v1",
        generation_status="SUCCESS", refusal_status=False, metadata={}
    )
    mock_pipeline.generator = mock_provider
    answer = mock_pipeline.answer_question("test query")

    assert answer.abstention_type != AbstentionReason.PROVIDER_ERROR
    assert "IS 123" in answer.answer


# ---------------------------------------------------------------------------
# B. Valid insufficient-evidence JSON refusal — LLM returns structured refusal
# ---------------------------------------------------------------------------
def test_valid_insufficient_evidence_refusal(mock_pipeline):
    mock_provider = MagicMock()
    mock_provider.generate_structured_answer.return_value = ProviderResponse(
        generated_answer="I could not find sufficient information in the retrieved BIS documents.",
        claims=[], citations=[],
        model="test", model_version="v1",
        generation_status="SUCCESS", refusal_status=True,
        metadata={"raw_json": {"status": "INSUFFICIENT_EVIDENCE", "confidence": 0.0}}
    )
    mock_pipeline.generator = mock_provider
    answer = mock_pipeline.answer_question("test query")

    # LLM refusal via structured JSON is NOT a PROVIDER_ERROR
    assert answer.abstention_type != AbstentionReason.PROVIDER_ERROR


# ---------------------------------------------------------------------------
# C. Valid out-of-scope JSON refusal
# ---------------------------------------------------------------------------
def test_valid_out_of_scope_refusal(mock_pipeline):
    mock_provider = MagicMock()
    mock_provider.generate_structured_answer.return_value = ProviderResponse(
        generated_answer="This question falls outside the scope of BIS standards.",
        claims=[], citations=[],
        model="test", model_version="v1",
        generation_status="SUCCESS", refusal_status=True,
        metadata={"raw_json": {"status": "OUT_OF_SCOPE", "confidence": 0.0}}
    )
    mock_pipeline.generator = mock_provider
    answer = mock_pipeline.answer_question("test query")

    assert answer.abstention_type != AbstentionReason.PROVIDER_ERROR


# ---------------------------------------------------------------------------
# D–I. Provider errors: all must produce PROVIDER_ERROR, not OUT_OF_SCOPE
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("error_text,scenario", [
    ("Error code: 400 - json_validate_failed, model returned plain text", "D_plain_text_refusal"),
    ("json.decoder.JSONDecodeError: Expecting value", "E_malformed_json"),
    ("KeyError: 'answer' - missing required field", "F_missing_field"),
    ("Error code: 400 - model decommissioned", "G_http_400"),
    ("Error code: 401 - Unauthorized", "G_http_401"),
    ("Error code: 429 - Too Many Requests", "G_http_429"),
    ("Failed to generate JSON. json_validate_failed", "H_json_validation"),
    ("Connection timed out after 30s", "I_timeout"),
    ("Internal provider failure", "I_exception"),
])
def test_provider_errors_produce_provider_error_not_out_of_scope(mock_pipeline, error_text, scenario):
    mock_provider = MagicMock()
    mock_provider.generate_structured_answer.return_value = ProviderResponse(
        generated_answer=f"Generation failed: {error_text}",
        claims=[], citations=[],
        model="test", model_version="v1",
        generation_status="ERROR", refusal_status=True, metadata={}
    )
    mock_pipeline.generator = mock_provider

    answer = mock_pipeline.answer_question("test query")

    # PROVIDER_ERROR must be the abstention type
    assert answer.abstention_type == AbstentionReason.PROVIDER_ERROR, \
        f"Scenario {scenario}: expected PROVIDER_ERROR, got {answer.abstention_type}"

    # Provider error produces zero claims
    assert len(answer.claims) == 0, f"Scenario {scenario}: claims should be empty"

    # Provider error produces zero citations
    assert len(answer.citations) == 0, f"Scenario {scenario}: citations should be empty"

    # Provider error cannot become status="verified" — confidence must be 0
    assert answer.confidence == 0.0, f"Scenario {scenario}: confidence should be 0.0"

    # Provider error cannot pass grounding verification
    assert answer.guardrail_result is not None
    assert answer.guardrail_result.passed is False, \
        f"Scenario {scenario}: guardrail should not pass"
    assert answer.guardrail_result.refusal_required is True

    # Provider error cannot receive BIS evidence entailment
    assert answer.guardrail_result.grounding_confidence == 0.0

    # Refusal reason must be PROVIDER_ERROR, NOT OUT_OF_SCOPE
    assert answer.refusal_reason is not None
    assert "Provider Error" in answer.refusal_reason, \
        f"Scenario {scenario}: refusal_reason should contain 'Provider Error', got '{answer.refusal_reason}'"

    # Production payload must label it PROVIDER_ERROR, NOT OUT_OF_SCOPE
    if answer.production_payload:
        assert answer.production_payload.get("refusal_reason") != "OUT_OF_SCOPE", \
            f"Scenario {scenario}: production_payload must NOT label error as OUT_OF_SCOPE"
        assert answer.production_payload.get("refusal_reason") == "PROVIDER_ERROR", \
            f"Scenario {scenario}: production_payload refusal_reason should be PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# 14. Low entailment score cannot become VERIFIED
# ---------------------------------------------------------------------------
def test_low_entailment_score_not_verified():
    answer_text = "The system is red."
    chunks = [
        RetrievedChunk(
            chunk_id="C1", document_id="D1", source_id="S1",
            standard_number="IS 123", clause_number="1",
            chunk_type="req", normative_force="mandatory",
            temporal_status="current", score=1.0,
            text="The apple is blue.", content_hash="hash"
        )
    ]
    claims = ClaimVerifier.verify_claims(answer_text, chunks)
    assert len(claims) > 0
    for claim in claims:
        assert claim.verified is False


# ---------------------------------------------------------------------------
# API error strings must be excluded from claim decomposition
# ---------------------------------------------------------------------------
def test_api_error_strings_excluded_from_claims():
    error_texts = [
        "Generation failed: Error code 400 missing credentials.",
        "Generation failed: Error code: 401 - Unauthorized.",
        "Generation failed: model_decommissioned error.",
        "Provider error: missing api_key in configuration.",
    ]
    for text in error_texts:
        claims = ClaimVerifier.decompose_claims(text)
        assert len(claims) == 0, f"Error text leaked into claims: {text}"
