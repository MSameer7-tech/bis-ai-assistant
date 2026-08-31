"""
Phase 4 Batch 8: Comprehensive Adversarial, Hallucination & Robustness Test Suite.
Verifies that the RAG engine refuses ungrounded questions and detects numerical/citation/normative attacks.
"""
import pytest
from ai.rag.pipeline import RAGPipeline
from ai.rag.models import RAGAnswer, RetrievedChunk
from ai.rag.generator import DeterministicGroundedGenerator
from ai.rag.guardrails import ComplianceGuardrails
from ai.rag.citation import CitationExtractor
from ai.rag.context_builder import ContextBuilder


@pytest.fixture
def rag_pipeline():
    return RAGPipeline()


# Step 18: Adversarial Unknown / Out-of-Scope Questions
@pytest.mark.parametrize("adversarial_query", [
    "What is the manufacturing cost and retail market price of an IS 16102 compliant lamp?",
    "What is the average expected lifetime and warranty of self-ballasted lamps?",
    "Who is the current director general of the Bureau of Indian Standards?",
    "What are the quarterly sales numbers and corporate revenue for BIS certified lamp manufacturers?"
])
def test_adversarial_unknown_questions_refused(rag_pipeline, adversarial_query):
    ans: RAGAnswer = rag_pipeline.answer_question(adversarial_query)
    assert "could not find sufficient information" in ans.answer.lower()
    assert ans.refusal_reason is not None
    assert ans.confidence == 1.0


# Step 19: Numerical Hallucination Attack Detection
@pytest.mark.parametrize("fake_text,expected_violation", [
    ("The minimum insulation resistance is 5 MΩ.", "5 MΩ"),
    ("The cap temperature rise must not exceed 125 K.", "125 K"),
    ("The compliance test batch requires 30 lamps.", "30 lamps"),
    ("The test voltage is 1000 V DC.", "1000 V DC"),
    ("The torsion moment for E17 is 3.0 Nm.", "3.0 Nm")
])
def test_numerical_hallucination_attacks_caught_by_guardrails(fake_text, expected_violation):
    guard = ComplianceGuardrails()
    chunk = RetrievedChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="8.1.1",
        pages=[9],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2012-08-01",
        score=0.032,
        text="The insulation resistance shall not be less than 4 MΩ when tested with 500 V DC. Temperature 120 K. Batch 25 lamps. E17 torque 1.5 Nm.",
        content_hash="abc123hash",
        provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
    )

    res = guard.verify(
        query="test query",
        answer_text=fake_text,
        retrieved_chunks=[chunk],
        citations=[]
    )
    assert res.passed is False
    assert any("Numerical mismatch" in v for v in res.violations)
    assert res.grounding_confidence <= 0.3


# Step 20: Citation Hallucination Attack Detection
def test_citation_hallucination_attack_caught():
    extractor = CitationExtractor()
    chunk = RetrievedChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="8.1.1",
        pages=[9],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2012-08-01",
        score=0.032,
        text="Insulation resistance shall not be less than 4 MΩ.",
        content_hash="abc123hash",
        provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
    )

    fake_answer = (
        "Insulation resistance is 4 MΩ.\n\n"
        "### Citations & Provenance\n"
        "- IS 99999 : 2099, Clause 99.9, Page(s) 999 (Document ID: DOC-999)"
    )

    citations = extractor.extract_citations(fake_answer, [chunk])
    assert len(citations) == 1
    assert citations[0].verified is False

    guard = ComplianceGuardrails()
    res = guard.verify("insulation", fake_answer, [chunk], citations)
    assert res.passed is False
    assert any("Citation violation" in v for v in res.violations)


# Step 21: Mandatory Conversion on Provisional Requirement
def test_provisional_requirement_preserved():
    guard = ComplianceGuardrails()
    provisional_chunk = RetrievedChunk(
        chunk_id="DOC-001-v001::Table_3::TAB-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="9.1",
        pages=[11],
        chunk_type="table",
        normative_force="under_consideration",
        temporal_status="current",
        valid_from="2012-08-01",
        score=0.030,
        text="Table 3: GX53 | 3.0 Nm | under_consideration",
        content_hash="def456hash",
        provenance={"document_id": "DOC-001", "clause": "9.1", "pages": [11]}
    )

    # Attack: converting under_consideration to mandatory requirement
    attack_answer = "GX53 cap has a mandatory requirement of 3.0 Nm torque."
    res = guard.verify("gx53", attack_answer, [provisional_chunk], [])
    assert res.passed is False
    assert any("Normative violation" in v for v in res.violations)

    # Compliant: explicit provisional clarification
    good_answer = "The GX53 torque value is 3.0 Nm, but this value is under consideration and is not a mandatory requirement."
    res_good = guard.verify("gx53", good_answer, [provisional_chunk], [])
    assert res_good.passed is True
