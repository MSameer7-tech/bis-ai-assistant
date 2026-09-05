"""
Pydantic Schemas for the Master BIS Products & Scope Registry.
Encapsulates canonical products, deduplicated aliases, domain classifications,
and explicit evidence-backed regulatory certification metadata.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class CertificationStatus(str, Enum):
    MANDATORY_QCO = "MANDATORY_QCO"
    MANDATORY_CRS = "MANDATORY_CRS"
    MANDATORY_HALLMARKING = "MANDATORY_HALLMARKING"
    VOLUNTARY = "VOLUNTARY"
    SCHEME_DEPENDENT = "SCHEME_DEPENDENT"


class ProductRecord(BaseModel):
    """Authoritative representation of a BIS-governed product entity."""
    product_id: str = Field(..., description="Unique product identifier, e.g. PRD-0001")
    canonical_name: str = Field(..., description="Canonical product name derived from standard title/scope")
    term: str = Field(..., description="Search query term or alias representation")
    normalized_name: str = Field(..., description="Normalized clean name for matching")
    aliases: List[str] = Field(default_factory=list, description="Verified synonyms and common trade names")
    domain: str = Field("General", description="Product domain sector")
    department: Optional[str] = Field("CMD", description="BIS technical department")
    standard_number: str = Field(..., description="Primary governing Indian Standard")
    current_edition: Optional[str] = Field("2024", description="Current effective edition/revision")
    certification_status: CertificationStatus = Field(CertificationStatus.VOLUNTARY, description="Regulatory certification status")
    mandatory_certification: bool = Field(False, description="Whether BIS mark is mandated by statutory QCO/CRS")
    certification_evidence: str = Field(..., description="Authoritative statutory evidence backing the status")
    qco_id: Optional[str] = Field(None, description="Linked QCO identifier if mandated")
    scheme_id: Optional[str] = Field("SCHEME-I", description="Applicable BIS conformity assessment scheme")
    document_available: bool = Field(True, description="Whether normative standard text is in corpus")
    confidence: float = Field(1.0, description="Mapping confidence score")
    evidence_source: str = Field(..., description="Primary provenance source document or gazette")
    indexed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        frozen = False
