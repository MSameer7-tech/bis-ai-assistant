from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ai.retrieval.structured_retrieval_models import RetrievalSourceType

class EvidenceRole(str, Enum):
    IDENTITY_EVIDENCE = "IDENTITY_EVIDENCE"
    RELATIONSHIP_EVIDENCE = "RELATIONSHIP_EVIDENCE"
    NORMATIVE_EVIDENCE = "NORMATIVE_EVIDENCE"
    PROCEDURAL_EVIDENCE = "PROCEDURAL_EVIDENCE"

class IntegratedRetrievalResult(BaseModel):
    """Normalized retrieval result output from the orchestrator."""
    query: str = Field(..., description="The query used for retrieval")
    retrieval_source_type: RetrievalSourceType = Field(..., description="Origin source type")
    evidence_role: EvidenceRole = Field(..., description="Role of this evidence in generation")
    document_id: Optional[str] = Field(None, description="Document ID where applicable (Phase 6)")
    standard_number: Optional[str] = Field(None, description="Standard Identity where applicable")
    internal_bis_id: Optional[str] = Field(None, description="Authoritative internal ID where applicable")
    relationship_id: Optional[str] = Field(None, description="Catalogue relationship ID where applicable")
    title: str = Field(..., description="Document or entity title")
    matched_text: str = Field(..., description="The matched content/text")
    score: float = Field(..., description="Retrieval score")
    lifecycle_status: Optional[str] = Field(None, description="Active, Withdrawn, etc.")
    ambiguity_state: Optional[str] = Field(None, description="AMBIGUOUS_MATCH, YEAR_MISMATCH, UNRESOLVED, etc.")
    confidence: float = Field(..., description="Grounding confidence / match certainty")
    
    # Provenance
    source_url: Optional[str] = Field(None, description="Origin URL")
    sha256: Optional[str] = Field(None, description="Origin hash")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Raw provenance payload")

    def to_retrieved_chunk(self) -> Any:
        """Adapts this integrated result into a Phase 7 compatible RetrievedChunk."""
        from ai.rag.models import RetrievedChunk
        
        # We embed integrated metadata into the provenance payload so EvidenceGate and ContextBuilder
        # can still access the strict distinctions (role, lifecycle, etc) without modifying the schema.
        extended_provenance = dict(self.provenance)
        extended_provenance.update({
            "retrieval_source_type": self.retrieval_source_type.value,
            "evidence_role": self.evidence_role.value,
            "internal_bis_id": self.internal_bis_id,
            "relationship_id": self.relationship_id,
            "ambiguity_state": self.ambiguity_state,
            "lifecycle_status": self.lifecycle_status,
            "integrated_confidence": self.confidence,
        })
        
        # Use chunk_type to pass the evidence role cleanly
        # Map source identifiers appropriately
        doc_id = self.document_id or self.internal_bis_id or "UNKNOWN"
        chunk_id = f"IR-{self.retrieval_source_type.value[:3]}-{self.relationship_id or self.internal_bis_id or self.document_id or hash(self.matched_text)}"
        
        return RetrievedChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            source_id="INTEGRATED_ROUTER",
            standard_number=self.standard_number or doc_id,
            clause_number="General", # Structured metadata is general identity
            title=self.title,
            pages=[],
            chunk_type=self.evidence_role.value, # Strict role transmission
            normative_force="informative" if self.evidence_role != EvidenceRole.NORMATIVE_EVIDENCE else "mandatory",
            temporal_status=self.lifecycle_status.lower() if self.lifecycle_status else "current",
            score=self.score,
            text=self.matched_text,
            content_hash=self.sha256 or "nohash",
            provenance=extended_provenance
        )
