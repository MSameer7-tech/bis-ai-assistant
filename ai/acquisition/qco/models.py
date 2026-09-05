"""
Quality Control Orders (QCO) Data Models
Authoritative schemas for statutory quality control orders, ministries, effective dates, and exemptions.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class QCOStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DRAFT = "DRAFT"
    WITHDRAWN = "WITHDRAWN"


class MandatoryStatus(str, Enum):
    MANDATORY_QCO = "MANDATORY_QCO"
    MANDATORY_CRS = "MANDATORY_CRS"
    MANDATORY_HALLMARKING = "MANDATORY_HALLMARKING"
    VOLUNTARY = "VOLUNTARY"


class QCORecord(BaseModel):
    """Authoritative record for a statutory Quality Control Order (QCO)."""
    qco_id: str = Field(..., description="Unique QCO identifier (e.g., QCO-STEEL-2024-01)")
    title: str = Field(..., description="Official title of the Quality Control Order")
    notification_number: str = Field(..., description="Statutory notification number (e.g., S.O. 1245(E))")
    issuing_authority: str = Field(..., description="Issuing Central Ministry / Department (e.g., Ministry of Steel, DPIIT, MeitY)")
    publication_date: str = Field(..., description="Date of publication in The Gazette of India (YYYY-MM-DD)")
    effective_date: str = Field(..., description="Date when compliance becomes legally mandatory (YYYY-MM-DD)")
    status: QCOStatus = Field(default=QCOStatus.ACTIVE, description="Current legal status")
    products: List[str] = Field(default_factory=list, description="Canonical product names / terms covered by the order")
    standards: List[str] = Field(default_factory=list, description="List of Indian Standard numbers mandated by the order")
    scheme: str = Field(default="SCHEME-I", description="Conformity Assessment Scheme under which licence/registration is mandated")
    mandatory_status: MandatoryStatus = Field(default=MandatoryStatus.MANDATORY_QCO, description="Explicit mandatory certification type")
    exemptions: List[str] = Field(default_factory=list, description="Statutory exemptions (e.g., export goods, R&D, captive consumption)")
    amendments: List[str] = Field(default_factory=list, description="List of amendment notification numbers modifying this QCO")
    source_url: str = Field(..., description="Authoritative e-Gazette or Ministry URL")
    document_id: Optional[str] = Field(None, description="Internal document identifier if PDF acquired")
    content_hash: Optional[str] = Field(None, description="SHA256 checksum of the statutory order document")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of retrieval")
    evidence_source: str = Field(..., description="Specific Gazette citation and legal provenance")
