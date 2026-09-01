import pytest
from ai.verification.claim_verifier import ClaimVerifier
from ai.rag.models import RetrievedChunk


def test_decompose_claims():
    answer_text = """### Direct Answer
Industrial safety helmets are specified by IS 2925 : 1984. The maximum transmitted force in the shock absorption test shall not exceed 5.0 kN.

### Technical Details & Parameters
- **Parameter**: Transmitted Shock Force
- **Value & Limits**: <= 5.0 kN
"""
    claims = ClaimVerifier.decompose_claims(answer_text)
    assert len(claims) >= 2
    assert any("IS 2925" in c for c in claims)
    assert any("5.0 kN" in c for c in claims)


def test_verify_claims_with_evidence():
    answer_text = "The minimum yield strength for Fe 500D is 500 N/mm² under IS 1786 : 2024."
    chunk = RetrievedChunk(
        chunk_id="CHK-034",
        document_id="DOC-034",
        source_id="SRC-001",
        standard_number="IS 1786 : 2024",
        clause_number="7.2.1",
        title="Yield Strength Requirements",
        pages=[18],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        score=0.95,
        text="Clause 7.2.1: The minimum yield strength for Fe 500D shall be 500 N/mm².",
        content_hash="hash1786"
    )
    atomic_claims = ClaimVerifier.verify_claims(answer_text, [chunk])
    assert len(atomic_claims) == 1
    assert atomic_claims[0].claim_id == "CLM-001"
    assert atomic_claims[0].verified is True
    assert atomic_claims[0].entailment_score >= 0.70
    assert len(atomic_claims[0].evidence) == 1
    assert atomic_claims[0].evidence[0].clause == "7.2.1"
    assert atomic_claims[0].evidence[0].page == 18
