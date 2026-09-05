"""
Expanded Typed Refusal Classification (Phase 7E).
Provides structured, safe refusal responses when evidence is missing, out-of-scope, or contradictory.
"""
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ai.rag.schema import ProductionAnswerPayload, IntentPayload, AnswerBody, GuardrailPayload


class RefusalReasonType(str, Enum):
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    DOCUMENT_UNAVAILABLE = "DOCUMENT_UNAVAILABLE"
    UNSUPPORTED_NUMERICAL_CLAIM = "UNSUPPORTED_NUMERICAL_CLAIM"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"
    STALE_INFORMATION = "STALE_INFORMATION"
    PROVIDER_ERROR = "PROVIDER_ERROR"


REFUSAL_MESSAGES = {
    RefusalReasonType.OUT_OF_SCOPE: "I could not find sufficient information in the retrieved BIS standards corpus to answer this question. This question falls outside the technical scope of the Bureau of Indian Standards (BIS) specifications, product certification, and mandatory Quality Control Orders.",
    RefusalReasonType.INSUFFICIENT_EVIDENCE: "I could not find sufficient information in the retrieved BIS standards corpus to answer this question.",
    RefusalReasonType.CONTRADICTORY_EVIDENCE: "The retrieved BIS standards contain contradictory or conflicting requirements across editions without a definitive precedence rule.",
    RefusalReasonType.DOCUMENT_UNAVAILABLE: "The authoritative BIS standard or technical manual for this product is recognized in the catalog but the document is not currently available.",
    RefusalReasonType.UNSUPPORTED_NUMERICAL_CLAIM: "The requested technical parameter or numerical limit cannot be verified with 100% confidence against the authoritative clause evidence.",
    RefusalReasonType.AMBIGUOUS_QUERY: "The query does not specify sufficient technical context (such as product type, grade, or application) to identify the specific BIS standard.",
    RefusalReasonType.UNVERIFIED_SOURCE: "The information requested is not backed by an authoritative BIS gazette notification, scheme of testing, or sectional committee specification.",
    RefusalReasonType.STALE_INFORMATION: "The cited historical standard has been superseded by a newer edition and the requested parameter is no longer valid.",
    RefusalReasonType.PROVIDER_ERROR: "The answer generation service encountered a technical error. The retrieved evidence may still be valid but an answer could not be generated at this time."
}


class RefusalBuilder:
    """
    Constructs clean, auditable refusal responses.
    """

    @classmethod
    def build_refusal_payload(
        cls,
        request_id: str,
        query: str,
        reason_type: RefusalReasonType,
        custom_explanation: Optional[str] = None,
        intent_type: str = "OUT_OF_SCOPE",
        temporal_context: str = "Current Enforced Editions"
    ) -> ProductionAnswerPayload:
        explanation = custom_explanation or REFUSAL_MESSAGES.get(reason_type, "Refusal required due to lack of verified BIS evidence.")

        return ProductionAnswerPayload(
            request_id=request_id,
            status="refusal",
            query=query,
            temporal_context=temporal_context,
            intent=IntentPayload(type=intent_type, confidence=1.0),
            entities=[],
            answer=AnswerBody(
                text=explanation,
                summary=f"Refusal: {reason_type.value}"
            ),
            claims=[],
            citations=[],
            numerical_verifications=[],
            evidence_confidence=1.0,
            guardrail=GuardrailPayload(
                passed=True,
                warnings=[f"Query safely refused: {reason_type.value}"]
            ),
            refusal_reason=reason_type.value
        )
