import json
import pytest
import os
from unittest.mock import patch, MagicMock

from ai.rag.pipeline import RAGPipeline
from ai.rag.models import RAGAnswer
from ai.retrieval.integrated_retrieval_models import IntegratedRetrievalResult, EvidenceRole
from ai.retrieval.structured_retrieval_models import RetrievalSourceType

@pytest.fixture
def test_cases():
    cases_path = os.path.join("data", "evaluation", "phase8_13_e2e_cases.json")
    with open(cases_path, "r") as f:
        return json.load(f)

@pytest.fixture
def rag_pipeline():
    # Use real pipeline but mock LLM dependency to ensure deterministic output when we need it to just return what we expect.
    # Actually, RAGPipeline has `provider="groq"`, let's patch the LLM caller.
    return RAGPipeline()

def mock_llm_generate(*args, **kwargs):
    return "Mocked Answer", [], {}

class MockedLLMResponse:
    def __init__(self, content):
        self.content = content
        self.citations = []

@pytest.mark.parametrize("case_id", ["E2E-001", "E2E-002", "E2E-003", "E2E-004", "E2E-005", "E2E-011", "E2E-012", "E2E-013"])
def test_e2e_deterministic_cases(rag_pipeline, test_cases, case_id):
    case = next((c for c in test_cases if c["case_id"] == case_id), None)
    if not case:
        pytest.skip(f"Case {case_id} not found")
        
    if case.get("expected_outcome") == "NOT_APPLICABLE":
        pytest.skip("Not applicable")

    # We mock the LLM text generation so we test just the orchestration, retrieval, intent, and evidence suffciency.
    # `answer_question` calls `_generate_answer` which we can mock or we can patch the llm directly.
    # The requirement is: "Use deterministic/mock LLM responses only where required to make assertions independent of external provider availability."
    
    with patch.object(rag_pipeline.generator, 'generate_structured_answer', return_value=MagicMock(generated_answer="Mocked Answer", citations=[])):
        ans = rag_pipeline.answer_question(case["query"])
        
        # Validate intent
        actual_intent = ans.production_payload.get("intent", {}).get("type") if ans.production_payload else None
        assert actual_intent == case["expected_intent"], f"Intent mismatch for {case_id}"
        
        is_refusal = bool(ans.refusal_reason)
        if case["expected_outcome"] == "ABSTAIN":
            assert is_refusal, f"Expected refusal for {case_id}"
            if "allowed_refusal_reasons" in case:
                # Check abstention type
                abs_type = ans.abstention_type.value if hasattr(ans.abstention_type, "value") else str(ans.abstention_type)
                assert abs_type in case["allowed_refusal_reasons"] or str(ans.refusal_reason) in case["allowed_refusal_reasons"]
        else:
            assert not is_refusal, f"Unexpected refusal for {case_id}: {ans.refusal_reason}"
            
        # Check source routing and identity
        if "expected_standard_numbers" in case and not is_refusal:
            found_stds = set()
            for chunk in ans.retrieved_chunks:
                if chunk.standard_number:
                    found_stds.add(chunk.standard_number)
            for expected in case["expected_standard_numbers"]:
                assert any(expected in found or found in expected for found in found_stds), f"Expected std {expected} not found for {case_id}"

# Fixture for Conflicting Evidence (E2E-014)
def test_e2e_conflicting_evidence(rag_pipeline, test_cases):
    case = next((c for c in test_cases if c["case_id"] == "E2E-014"), None)
    
    # We patch retrieval to return contradictory evidence
    mock_results = [
        IntegratedRetrievalResult(
            query=case["query"],
            retrieval_source_type=RetrievalSourceType.DOCUMENT_EVIDENCE,
            evidence_role=EvidenceRole.NORMATIVE_EVIDENCE,
            document_id="DOC-999", standard_number="IS 9999", title="Test",
            matched_text="The operating voltage shall be exactly 100V.", score=0.9,
            confidence=0.9, provenance={"document_id": "DOC-999"}, sha256="hash1"
        ),
        IntegratedRetrievalResult(
            query=case["query"],
            retrieval_source_type=RetrievalSourceType.DOCUMENT_EVIDENCE,
            evidence_role=EvidenceRole.NORMATIVE_EVIDENCE,
            document_id="DOC-888", standard_number="IS 8888", title="Test",
            matched_text="The operating voltage shall be exactly 200V.", score=0.9,
            confidence=0.9, provenance={"document_id": "DOC-888"}, sha256="hash2"
        )
    ]
    
    with patch('ai.retrieval.integrated_retrieval.IntegratedRetrievalOrchestrator.retrieve', return_value=mock_results):
        # mock intent to ensure parameter is set
        with patch('ai.rag.pipeline.QueryParser.parse', return_value=MagicMock(intent="TECHNICAL_VALUE", parameter="voltage")):
            ans = rag_pipeline.answer_question(case["query"])
            
            is_refusal = bool(ans.refusal_reason)
            assert is_refusal
            abs_type = ans.abstention_type.value if hasattr(ans.abstention_type, "value") else str(ans.abstention_type)
            assert abs_type == "CONTRADICTORY_EVIDENCE" or "CONTRADICTORY_EVIDENCE" in str(ans.refusal_reason)

# Fixture for Missing Evidence (E2E-015)
def test_e2e_missing_evidence(rag_pipeline, test_cases):
    case = next((c for c in test_cases if c["case_id"] == "E2E-015"), None)
    
    # Patch retrieval to return NO normative evidence
    with patch('ai.retrieval.integrated_retrieval.IntegratedRetrievalOrchestrator.retrieve', return_value=[]):
        ans = rag_pipeline.answer_question(case["query"])
        is_refusal = bool(ans.refusal_reason)
        assert is_refusal
        # Since intent is technical, missing normative evidence triggers INSUFFICIENT_EVIDENCE
        abs_type = ans.abstention_type.value if hasattr(ans.abstention_type, "value") else str(ans.abstention_type)
        assert abs_type == "INSUFFICIENT_EVIDENCE" or "Insufficient evidence" in str(ans.refusal_reason)
