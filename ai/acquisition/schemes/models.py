"""
Conformity Assessment Schemes Data Models
Authoritative schemas for BIS certification schemes (Scheme I, Scheme II - CRS, FMCS, Hallmarking, CoC).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SchemeRecord(BaseModel):
    """Authoritative record for a BIS Conformity Assessment Scheme."""
    scheme_id: str = Field(..., description="Unique scheme ID (e.g., SCHEME-I, SCHEME-II, FMCS, HALLMARKING)")
    scheme_name: str = Field(..., description="Official title of the certification scheme")
    applicable_products: List[str] = Field(default_factory=list, description="Product categories governed by the scheme")
    applicable_standards: List[str] = Field(default_factory=list, description="Key standards governed by the scheme")
    eligibility: str = Field(..., description="Manufacturer / importer / jeweller eligibility criteria")
    certification_path: str = Field(..., description="Certification path (Factory Audit + Testing, Self-Declaration + Lab Report, Lot Inspection)")
    inspection_requirements: str = Field(..., description="Factory audit, in-house laboratory, and QC requirements")
    testing_requirements: str = Field(..., description="Independent third-party lab testing and routine SIT requirements")
    marking_requirements: str = Field(..., description="Standard Mark design, licence display, and QR/batch coding requirements")
    licence_requirements: str = Field(..., description="Prerequisites for grant and maintenance of licence")
    source_url: str = Field(..., description="Authoritative BIS portal link")
    document_id: Optional[str] = Field(None, description="Internal document identifier")
    effective_dates: str = Field(..., description="Statutory regulations enforcement date")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of ingestion")
