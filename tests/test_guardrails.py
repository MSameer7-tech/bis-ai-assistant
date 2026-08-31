"""
Tests for Phase 4 Batch 5: guardrails.py
"""
import pytest
from ai.rag.models import RetrievedChunk, Citation
from ai.rag.guardrails import ComplianceGuardrails


@pytest.fixture
def insulation_chunk():
    return RetrievedChunk(
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
        text="The insulation resistance shall not be less than 4 MΩ when tested at 500 V DC.",
        content_hash="abc123hash",
        provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
    )


@pytest.fixture
def provisional_chunk():
    return RetrievedChunk(
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


def test_guardrail_passes_valid_answer(insulation_chunk):
    guard = ComplianceGuardrails()
    answer_text = "The minimum insulation resistance is 4 MΩ when tested at 500 V DC."
    citations = [
        Citation(
            standard_number="IS 16102 (Part 1) : 2012",
            clause="8.1.1",
            pages=[9],
            source_id="SRC-001",
            chunk_id="DOC-001-v001::8.1.1::REQ-001",
            verified=True
        )
    ]
    res = guard.verify("insulation", answer_text, [insulation_chunk], citations)
    assert res.passed is True
    assert res.grounding_confidence >= 0.9
    assert len(res.violations) == 0


def test_guardrail_detects_numerical_hallucination(insulation_chunk):
    guard = ComplianceGuardrails()
    # Deliberate numerical mismatch: 5 MΩ instead of 4 MΩ
    hallucinated_answer = "The minimum insulation resistance is 5 MΩ when tested at 500 V DC."
    citations = [
        Citation(
            standard_number="IS 16102 (Part 1) : 2012",
            clause="8.1.1",
            pages=[9],
            source_id="SRC-001",
            chunk_id="DOC-001-v001::8.1.1::REQ-001",
            verified=True
        )
    ]
    res = guard.verify("insulation", hallucinated_answer, [insulation_chunk], citations)
    assert res.passed is False
    assert any("Numerical mismatch" in v for v in res.violations)
    assert res.grounding_confidence <= 0.3


def test_guardrail_detects_mandatory_claim_on_provisional_requirement(provisional_chunk):
    guard = ComplianceGuardrails()
    bad_answer = "The standard strictly requires GX53 caps to withstand a mandatory requirement of 3.0 Nm."
    citations = [
        Citation(
            standard_number="IS 16102 (Part 1) : 2012",
            clause="9.1",
            pages=[11],
            source_id="SRC-001",
            chunk_id="DOC-001-v001::Table_3::TAB-001",
            verified=True
        )
    ]
    res = guard.verify("gx53 torque", bad_answer, [provisional_chunk], citations)
    assert res.passed is False
    assert any("Normative violation" in v for v in res.violations)
