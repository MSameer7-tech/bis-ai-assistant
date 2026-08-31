"""
Pydantic data models for the Phase 4 Grounded RAG Engine.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a validated chunk retrieved from Phase 3 HybridSearchEngine."""
    chunk_id: str = Field(..., description="Unique stable chunk identifier")
    document_id: str = Field(..., description="BIS Document code (e.g. DOC-001)")
    version_id: Optional[str] = Field(None, description="Document version code")
    source_id: str = Field(..., description="Source registry ID (e.g. SRC-001)")
    standard_number: str = Field(..., description="Standard code (e.g. IS 16102 (Part 1) : 2012)")
    clause_number: str = Field(..., description="Canonical clause number or table ID (e.g. 8.1.1)")
    title: Optional[str] = Field(None, description="Descriptive title of chunk or clause")
    pages: List[int] = Field(default_factory=list, description="Extracted PDF page numbers")
    chunk_type: str = Field(..., description="Type of chunk (requirement, table, definition, etc.)")
    normative_force: str = Field(..., description="Normative force (mandatory, under_consideration, informative, etc.)")
    temporal_status: str = Field(..., description="Temporal validity (current, superseded, amended)")
    valid_from: Optional[str] = Field(None, description="Effective start date YYYY-MM-DD")
    valid_until: Optional[str] = Field(None, description="Expiration date YYYY-MM-DD or null")
    score: float = Field(..., description="Reciprocal Rank Fusion (RRF) score")
    text: str = Field(..., description="Self-contained chunk text/markdown")
    content_hash: str = Field(..., description="SHA-256 hash of the chunk text")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Authoritative provenance payload")


class Citation(BaseModel):
    """Represents an authoritative, verifiable citation in a generated answer."""
    standard_number: str = Field(..., description="Standard cited")
    clause: str = Field(..., description="Clause or Table cited")
    pages: List[int] = Field(default_factory=list, description="Page numbers in standard")
    source_id: str = Field(..., description="Source registry ID")
    chunk_id: str = Field(..., description="Target chunk ID")
    quote_snippet: Optional[str] = Field(None, description="Verbatim text supporting the claim")
    verified: bool = Field(False, description="Whether citation matches retrieved chunk provenance")


class RAGContext(BaseModel):
    """Structured context assembled for the LLM prompt."""
    evidence_blocks: List[str] = Field(default_factory=list, description="Formatted individual evidence blocks")
    formatted_prompt_context: str = Field(..., description="Combined high-density context text")
    chunks: List[RetrievedChunk] = Field(default_factory=list, description="Ordered source chunks")
    total_tokens_estimate: int = Field(0, description="Estimated token count")


from enum import Enum

class AbstentionReason(str, Enum):
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    NO_RELEVANT_STANDARD = "NO_RELEVANT_STANDARD"
    WRONG_PARAMETER = "WRONG_PARAMETER"
    WRONG_PRODUCT = "WRONG_PRODUCT"
    TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_NUMERICAL_CLAIM = "UNSUPPORTED_NUMERICAL_CLAIM"


class GuardrailResult(BaseModel):
    """Result of post-generation verification and safety guardrails."""
    passed: bool = Field(..., description="Whether the answer passed all guardrails")
    grounding_confidence: float = Field(..., description="Calculated grounding score (0.0 to 1.0)")
    refusal_required: bool = Field(False, description="Whether query should be refused due to lack of evidence")
    abstention_reason: Optional[AbstentionReason] = Field(None, description="Explicit classification of why answer was refused")
    violations: List[str] = Field(default_factory=list, description="Critical guardrail failure messages")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    numerical_checks: List[Dict[str, Any]] = Field(default_factory=list, description="Numerical parameter check results")
    normative_checks: List[Dict[str, Any]] = Field(default_factory=list, description="Mandatory vs under_consideration check results")


class RAGAnswer(BaseModel):
    """Complete, structured answer returned by the RAG pipeline."""
    query: str = Field(..., description="Original user question")
    answer: str = Field(..., description="Generated, grounded answer text")
    citations: List[Citation] = Field(default_factory=list, description="List of verified citations")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Retrieved evidence chunks")
    confidence: float = Field(..., description="Overall grounding confidence score (0.0 to 1.0)")
    temporal_context: Optional[str] = Field(None, description="Applicable as-of date or 'current'")
    refusal_reason: Optional[str] = Field(None, description="Reason if query was refused")
    abstention_type: Optional[AbstentionReason] = Field(None, description="Typed abstention reason")
    guardrail_result: Optional[GuardrailResult] = Field(None, description="Detailed guardrail breakdown")
    technical_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted key technical parameters")
