"""
Unit tests for compliance guardrails and physical quantity normalization.
Verifies that equivalent units (1.5 kg == 1500 g, 53 MPa == 53 N/mm2, 3 bar == 300 kPa)
are accurately normalized without false positive mismatch flags.
"""
from ai.rag.guardrails import ComplianceGuardrails
from ai.rag.models import RetrievedChunk, Citation

def test_guardrail_mass_equivalence_kg_to_g():
    guardrails = ComplianceGuardrails()
    
    evidence_chunk = RetrievedChunk(
        chunk_id="DOC-026-v001::6.1::REQ-001",
        document_id="DOC-026",
        source_id="SRC-026",
        standard_number="IS 4151 : 2015",
        clause_number="6.1",
        pages=[1],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from=None,
        valid_until=None,
        text="Clause 6.1: The total mass of the helmet shall not exceed 1500 g.",
        score=0.95,
        content_hash="abc"
    )
    
    answer_text = "The total mass of the complete protective helmet shall not exceed 1500 g (1.5 kg)."
    
    result = guardrails.verify(
        query="What is the helmet mass?",
        answer_text=answer_text,
        retrieved_chunks=[evidence_chunk],
        citations=[Citation(standard_number="IS 4151 : 2015", clause="6.1", pages=[1], source_id="SRC-026", chunk_id="DOC-026-v001::6.1::REQ-001", verified=True)]
    )
    
    assert result.passed is True
    assert len(result.violations) == 0

def test_guardrail_pressure_equivalence_bar_to_kpa():
    guardrails = ComplianceGuardrails()
    
    evidence_chunk = RetrievedChunk(
        chunk_id="DOC-027-v001::8.1::REQ-001",
        document_id="DOC-027",
        source_id="SRC-027",
        standard_number="IS 2347 : 2017",
        clause_number="8.1",
        pages=[1],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from=None,
        valid_until=None,
        text="Clause 8.1: The pressure cooker shall withstand a proof pressure of 3.0 bar.",
        score=0.95,
        content_hash="abc"
    )
    
    answer_text = "The cooker body shall withstand a hydraulic proof pressure of not less than 3.0 bar (300 kPa)."
    
    result = guardrails.verify(
        query="What is the cooker pressure?",
        answer_text=answer_text,
        retrieved_chunks=[evidence_chunk],
        citations=[Citation(standard_number="IS 2347 : 2017", clause="8.1", pages=[1], source_id="SRC-027", chunk_id="DOC-027-v001::8.1::REQ-001", verified=True)]
    )
    
    assert result.passed is True
    assert len(result.violations) == 0

def test_guardrail_stress_equivalence_mpa_to_n_mm2():
    guardrails = ComplianceGuardrails()
    
    evidence_chunk = RetrievedChunk(
        chunk_id="DOC-018-v001::6.1::REQ-001",
        document_id="DOC-018",
        source_id="SRC-018",
        standard_number="IS 269 : 2015",
        clause_number="6.1",
        pages=[1],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from=None,
        valid_until=None,
        text="Clause 6.1: Compressive strength of 53 Grade OPC shall not be less than 53 MPa.",
        score=0.95,
        content_hash="abc"
    )
    
    answer_text = "The 28-day compressive strength shall not be less than 53 MPa (53 N/mm²)."
    
    result = guardrails.verify(
        query="What is the compressive strength?",
        answer_text=answer_text,
        retrieved_chunks=[evidence_chunk],
        citations=[Citation(standard_number="IS 269 : 2015", clause="6.1", pages=[1], source_id="SRC-018", chunk_id="DOC-018-v001::6.1::REQ-001", verified=True)]
    )
    
    assert result.passed is True
    assert len(result.violations) == 0
