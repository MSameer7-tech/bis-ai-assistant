"""
Production Grounded Answer & Atomic Claim Schemas (Phase 7B).
Defines the strict, strongly-typed machine schema for all judge-facing and API outputs.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EntityType(str, Enum):
    STANDARD = "standard"
    PRODUCT = "product"
    QCO = "qco"
    LABORATORY = "laboratory"
    COMMITTEE = "committee"
    SCHEME = "scheme"


class EntityReference(BaseModel):
    """Reference to a verified entity in the BIS catalog / Knowledge Graph."""
    entity_type: EntityType = Field(..., description="Classification of entity")
    id: str = Field(..., description="Canonical ID (e.g. STD-IS-1786-2024, PRD-000001)")
    name: str = Field(..., description="Human-readable title or product name")
    domain: Optional[str] = Field(None, description="Department or industrial domain")
    mandatory_certification: Optional[bool] = Field(None, description="Whether statutory ISI / CRS mark is compulsory")


class EvidenceRef(BaseModel):
    """Exact grounding location for an atomic claim."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Document code (DOC-034)")
    standard_number: str = Field(..., description="Standard code (IS 1786:2024)")
    clause: str = Field(..., description="Clause or Table number (e.g. 7.2.1)")
    page: Optional[int] = Field(None, description="PDF page number")
    quote: Optional[str] = Field(None, description="Verbatim text quote from source chunk")


class AtomicClaim(BaseModel):
    """Individual factual statement extracted from answer with explicit evidence support."""
    claim_id: str = Field(..., description="Stable claim ID (e.g. CLM-001)")
    text: str = Field(..., description="Atomic claim statement")
    evidence: List[EvidenceRef] = Field(default_factory=list, description="Grounding evidence chunks")
    verified: bool = Field(False, description="Whether claim is verified by evidence")
    entailment_score: float = Field(0.0, description="Evidence support confidence (0.0 to 1.0)")


class Citation(BaseModel):
    """Standard-clause-page citation."""
    standard: str = Field(..., description="Standard cited (e.g. IS 1786:2024)")
    clause: str = Field(..., description="Clause or Table (e.g. 7.2.1)")
    page: Optional[int] = Field(None, description="Page number")
    chunk_id: Optional[str] = Field(None, description="Source chunk ID")
    quote_snippet: Optional[str] = Field(None, description="Verbatim quote snippet")
    verified: bool = Field(False, description="Whether citation physically matches chunk in evidence")


from ai.verification.models import NumericalVerification


class IntentPayload(BaseModel):
    """Query intent classification."""
    type: str = Field(..., description="Intent route identifier")
    confidence: float = Field(1.0, description="Classification confidence")


class GuardrailPayload(BaseModel):
    """Compliance and grounding guardrail report."""
    passed: bool = Field(..., description="Whether answer passed all safety gates")
    violations: List[str] = Field(default_factory=list, description="List of critical violations if blocked")
    warnings: List[str] = Field(default_factory=list, description="Non-critical advisory warnings")


class AnswerBody(BaseModel):
    """Body of the answer text."""
    text: str = Field(..., description="Full formatted markdown answer")
    summary: Optional[str] = Field(None, description="1-sentence direct answer")


class ProductionAnswerPayload(BaseModel):
    """
    Unified Production Output Schema for BIS AI Technical Assistant.
    Provides complete end-to-end provenance, structured claims, verified citations, and numerical checks.
    """
    request_id: str = Field(..., description="Unique request UUID")
    status: str = Field("verified", description="'verified', 'refusal', 'guardrail_blocked'")
    query: str = Field(..., description="Original user query")
    temporal_context: str = Field("Current Enforced Editions", description="As-of date context")
    intent: IntentPayload = Field(..., description="Classified query intent")
    entities: List[EntityReference] = Field(default_factory=list, description="Resolved BIS standards / entities")
    answer: AnswerBody = Field(..., description="Answer content")
    claims: List[AtomicClaim] = Field(default_factory=list, description="Atomic verified claims")
    citations: List[Citation] = Field(default_factory=list, description="Authoritative citations")
    numerical_verifications: List[NumericalVerification] = Field(default_factory=list, description="Numerical audits")
    evidence_confidence: float = Field(..., description="Deterministically computed grounding confidence (0.0-1.0)")
    guardrail: GuardrailPayload = Field(..., description="Guardrail audit result")
    refusal_reason: Optional[str] = Field(None, description="Explicit refusal explanation if unanswerable")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp")
