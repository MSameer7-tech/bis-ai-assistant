import pytest
from ai.verification.numerical_verifier import NumericalVerifier
from ai.rag.models import RetrievedChunk


def test_unit_normalization():
    assert NumericalVerifier.normalize_unit("n/mm2") == "N/mm²"
    assert NumericalVerifier.normalize_unit("N/mm²") == "N/mm²"
    assert NumericalVerifier.normalize_unit("m3/min") == "m³/min"
    assert NumericalVerifier.normalize_unit("percent") == "%"
    assert NumericalVerifier.normalize_unit("deg c") == "°C"
    assert NumericalVerifier.normalize_unit("mohm") == "MΩ"
    assert NumericalVerifier.normalize_unit("nm") == "Nm"


def test_extract_quantities_with_table():
    table_text = """
| Cap Style | Torsion Moment (Torque) | Unit | Status |
|---|---|---|---|
| E17 | 1.5 | Nm | mandatory |
| GX53 | 3.0 | Nm | under_consideration |
"""
    quantities = NumericalVerifier.extract_quantities(table_text)
    assert len(quantities) >= 2
    assert (1.5, "Nm") in quantities or any(q[0] == 1.5 for q in quantities)
    assert (3.0, "Nm") in quantities or any(q[0] == 3.0 for q in quantities)


def test_verify_quantities_table_chunk():
    answer_text = "The torque requirement for E17 cap is 1.5 Nm."
    chunk = RetrievedChunk(
        chunk_id="CHK-TAB-001",
        document_id="DOC-001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="9.1",
        title="Torque Test Values",
        pages=[11],
        chunk_type="table",
        normative_force="mandatory",
        temporal_status="current",
        score=0.95,
        text="""Torque Test Values for Unused Lamps:
| Cap Style | Torsion Moment | Unit | Status |
| E17 | 1.5 | Nm | mandatory |
| GX53 | 3.0 | Nm | under_consideration |
""",
        content_hash="tabhash"
    )
    verifications = NumericalVerifier.verify_quantities_in_evidence(
        answer_text=answer_text,
        evidence_chunks=[chunk],
        parameter_hint="torque_moment"
    )
    assert len(verifications) == 1
    assert verifications[0].passed is True
    assert verifications[0].claim_value == 1.5
