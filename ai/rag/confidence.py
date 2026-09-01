"""
Deterministic Evidence Confidence Calculator (Phase 7E).
Computes grounding confidence score exclusively from measurable signals.
"""
from typing import List
from ai.rag.models import RetrievedChunk
from ai.rag.schema import Citation, AtomicClaim, NumericalVerification


class ConfidenceCalculator:
    """
    Computes factual grounding confidence deterministically:
    Confidence = 0.30 * CitationMatch + 0.25 * NumericalPass + 0.25 * ClaimEntailment + 0.10 * RRF + 0.10 * Authority
    """

    @classmethod
    def calculate_confidence(
        cls,
        evidence_chunks: List[RetrievedChunk],
        citations: List[Citation],
        claims: List[AtomicClaim],
        numerical_checks: List[NumericalVerification]
    ) -> float:
        if not evidence_chunks:
            return 0.0

        # 1. RRF Retrieval Signal
        max_rrf = max((c.score for c in evidence_chunks), default=0.0)
        rrf_signal = min(1.0, max(0.5, max_rrf / 0.50)) if max_rrf > 0 else 0.5

        # 2. Source Authority Signal
        mandatory_count = sum(1 for c in evidence_chunks if c.normative_force in ("mandatory", "requirement", "table"))
        authority_signal = min(1.0, max(0.6, mandatory_count / max(1, len(evidence_chunks))))

        # 3. Citation Verification Signal
        if citations:
            verified_citations = sum(1 for c in citations if c.verified)
            citation_signal = verified_citations / len(citations)
        else:
            citation_signal = 0.5

        # 4. Claim Entailment Signal
        if claims:
            verified_claims = sum(1 for cl in claims if cl.verified)
            claim_signal = verified_claims / len(claims)
        else:
            claim_signal = 0.5

        # 5. Numerical Pass Signal
        if numerical_checks:
            passed_checks = sum(1 for n in numerical_checks if n.passed)
            numerical_signal = passed_checks / len(numerical_checks)
        else:
            numerical_signal = 1.0  # No numerical claims to fail

        # Weighted Composition (heavily weighted towards verified facts)
        confidence = (
            0.30 * citation_signal +
            0.25 * numerical_signal +
            0.25 * claim_signal +
            0.10 * rrf_signal +
            0.10 * authority_signal
        )

        return round(min(1.0, max(0.0, confidence)), 2)
