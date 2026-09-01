import pytest
from ai.rag.schema import (
    ProductionAnswerPayload,
    IntentPayload,
    AnswerBody,
    EntityReference,
    EntityType,
    AtomicClaim,
    Citation,
    NumericalVerification,
    GuardrailPayload
)
from ai.rag.answer_validator import AnswerValidator


def test_production_answer_payload_serialization():
    payload = ProductionAnswerPayload(
        request_id="REQ-001",
        status="verified",
        query="What is the yield strength for Fe 500D?",
        temporal_context="Current Enforced Editions",
        intent=IntentPayload(type="EXACT_TECHNICAL_VALUES", confidence=0.99),
        entities=[
            EntityReference(
                entity_type=EntityType.STANDARD,
                id="STD-IS-1786-2024",
                name="IS 1786:2024 (High Strength Deformed Steel Bars)",
                domain="construction_civil",
                mandatory_certification=True
            )
        ],
        answer=AnswerBody(
            text="The minimum yield strength for Fe 500D is 500 N/mm² under IS 1786:2024, Clause 7.2.1, Page 18.",
            summary="Minimum yield strength is 500 N/mm²."
        ),
        claims=[
            AtomicClaim(
                claim_id="CLM-001",
                text="The minimum yield strength for Fe 500D is 500 N/mm².",
                verified=True,
                entailment_score=1.0
            )
        ],
        citations=[
            Citation(
                standard="IS 1786:2024",
                clause="7.2.1",
                page=18,
                chunk_id="CHK-IS1786-C7.2.1",
                verified=True
            )
        ],
        numerical_verifications=[
            NumericalVerification(
                parameter="yield_strength",
                claim_value=500.0,
                claim_unit="N/mm²",
                source_value=500.0,
                source_unit="N/mm²",
                passed=True,
                tolerance_error=0.0
            )
        ],
        evidence_confidence=0.98,
        guardrail=GuardrailPayload(passed=True)
    )

    is_valid, errors = AnswerValidator.validate_payload(payload)
    assert is_valid is True
    assert len(errors) == 0

    json_str = payload.model_dump_json()
    assert "REQ-001" in json_str
    assert "500.0" in json_str


def test_validator_catches_failed_numerical_check():
    payload = ProductionAnswerPayload(
        request_id="REQ-002",
        status="verified",
        query="What is the yield strength for Fe 500D?",
        temporal_context="Current Enforced Editions",
        intent=IntentPayload(type="EXACT_TECHNICAL_VALUES", confidence=0.99),
        answer=AnswerBody(text="Yield strength is 450 N/mm²."),
        citations=[
            Citation(standard="IS 1786:2024", clause="7.2.1", page=18, chunk_id="CHK-001", verified=True)
        ],
        numerical_verifications=[
            NumericalVerification(
                parameter="yield_strength",
                claim_value=450.0,
                claim_unit="N/mm²",
                source_value=500.0,
                source_unit="N/mm²",
                passed=False,
                tolerance_error=50.0
            )
        ],
        evidence_confidence=0.5,
        guardrail=GuardrailPayload(passed=False, violations=["Numerical mismatch"])
    )

    is_valid, errors = AnswerValidator.validate_payload(payload)
    assert is_valid is False
    assert any("Numerical check failed" in err for err in errors)
