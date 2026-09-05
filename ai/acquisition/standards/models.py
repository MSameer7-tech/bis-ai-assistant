"""
Pydantic Schemas for the Master BIS Standards Registry.
Encapsulates versioned, immutable standard records with complete temporal provenance,
explicit acquisition dispositions, and failure tracking.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class StandardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    DRAFT = "DRAFT"


class AcquisitionStatus(str, Enum):
    ACQUIRED = "ACQUIRED"
    CATALOG_ONLY = "CATALOG_ONLY"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    ACQUISITION_FAILED = "ACQUISITION_FAILED"


class AcquisitionFailureReason(str, Enum):
    NONE = "NONE"
    DOCUMENT_NOT_AVAILABLE = "DOCUMENT_NOT_AVAILABLE"
    METADATA_ONLY = "METADATA_ONLY"
    PAYWALL_RESTRICTED = "PAYWALL_RESTRICTED"
    CORRUPT_PAYLOAD = "CORRUPT_PAYLOAD"
    UNRESOLVED_TITLE = "UNRESOLVED_TITLE"
    SUPERSEDED_HISTORICAL = "SUPERSEDED_HISTORICAL"


class AspectType(str, Enum):
    PRODUCT_SPECIFICATION = "Product Specification"
    METHOD_OF_TEST = "Method of Test"
    CODE_OF_PRACTICE = "Code of Practice"
    TERMINOLOGY = "Terminology & Glossary"
    DIMENSIONS = "Dimensions & Tolerances"
    SAFETY_REQUIREMENTS = "Safety Requirements"
    GENERAL = "General Standard"


class StandardRecord(BaseModel):
    """Authoritative representation of an Indian Standard edition/revision."""
    standard_id: str = Field(..., description="Unique canonical identifier, e.g. STD-IS-001786-2024")
    is_number: str = Field(..., description="Base Indian Standard number, e.g. IS 1786")
    title: str = Field(..., description="Full normative title of the standard")
    edition: str = Field("First Edition", description="Edition name, e.g. Fifth Revision, Third Revision")
    revision: Optional[str] = Field(None, description="Revision code, e.g. Rev 5, Rev 0")
    status: StandardStatus = Field(StandardStatus.ACTIVE, description="Current regulatory lifecycle status")
    acquisition_status: AcquisitionStatus = Field(AcquisitionStatus.CATALOG_ONLY, description="Physical acquisition status")
    failure_reason: AcquisitionFailureReason = Field(AcquisitionFailureReason.NONE, description="Explicit failure reason if not acquired")
    reaffirmation_year: Optional[int] = Field(None, description="Year of latest reaffirmation by BIS")
    amendment_count: int = Field(0, description="Total number of published amendments")
    technical_department: Optional[str] = Field("CMD", description="BIS Technical Department (e.g. CED, ETD, MTD, FAD, TXD, CHD)")
    technical_committee: Optional[str] = Field(None, description="Sectional Committee (e.g. MTD 04, CED 02)")
    aspect: AspectType = Field(AspectType.PRODUCT_SPECIFICATION, description="Standard aspect type")
    language: str = Field("English", description="Publication language")
    source_url: str = Field(..., description="Authoritative BIS standards portal URL")
    document_id: Optional[str] = Field(None, description="Mapped processed document ID if ingested (e.g. DOC-034)")
    effective_from: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    effective_to: Optional[str] = Field("9999-12-31", description="Retirement / supersession date")
    supersedes: List[str] = Field(default_factory=list, description="List of standard_ids superseded by this edition")
    superseded_by: Optional[str] = Field(None, description="standard_id that supersedes this edition, if any")
    content_hash: Optional[str] = Field(None, description="SHA256 checksum of raw normative document")
    file_size_bytes: Optional[int] = Field(None, description="Size in bytes of the acquired document")
    parser_version: Optional[str] = Field(None, description="Parser version used to extract text")
    normalizer_version: Optional[str] = Field(None, description="Normalizer version used to structure content")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        frozen = False
