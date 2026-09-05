"""
Comprehensive Pydantic data models for Evidence Completion & Provenance Binding (Phase 4 Batch F).
Incorporates multi-authority provenance, locator types, evidence versioning, and strict 6-level taxonomy.
"""
import hashlib
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class EvidentiaryStrength(str, Enum):
    """
    Strict 6-level taxonomy defining evidentiary reliability and temporal validity.
    """
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"                    # Current authoritative evidence with exact locator
    EVIDENCE_PARTIAL = "EVIDENCE_PARTIAL"                      # Authoritative source verified, deep locator incomplete
    SOURCE_FOUND_NOT_EXTRACTED = "SOURCE_FOUND_NOT_EXTRACTED"  # Source exists and fingerprinted but extraction incomplete
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"                      # Expected primary source unavailable
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"              # Multiple authoritative sources conflict
    STALE_EVIDENCE = "STALE_EVIDENCE"                          # Authoritative for historical state, invalid for current normative claim


class SourceAuthority(str, Enum):
    """Official government or institutional publishing authority."""
    BIS = "BIS"                                               # Bureau of Indian Standards
    DPIIT = "DPIIT"                                           # Dept for Promotion of Industry and Internal Trade
    MEITY = "MEITY"                                           # Ministry of Electronics and Information Technology
    MINISTRY_OF_STEEL = "MINISTRY_OF_STEEL"                   # Ministry of Steel
    MINISTRY_OF_HEAVY_INDUSTRIES = "MINISTRY_OF_HEAVY_IND"   # Ministry of Heavy Industries
    MINISTRY_OF_CONSUMER_AFFAIRS = "MINISTRY_OF_CA"           # Ministry of Consumer Affairs, Food & Public Distribution
    MINISTRY_OF_CHEMICALS = "MINISTRY_OF_CHEMICALS"           # Ministry of Chemicals and Fertilizers
    MINISTRY_OF_TEXTILES = "MINISTRY_OF_TEXTILES"             # Ministry of Textiles
    MINISTRY_OF_MINES = "MINISTRY_OF_MINES"                   # Ministry of Mines
    NABL = "NABL"                                             # National Accreditation Board for Testing and Calibration Labs
    CCPA = "CCPA"                                             # Central Consumer Protection Authority


class SourceType(str, Enum):
    """Nature of the physical or digital source medium."""
    STANDARD_PDF = "STANDARD_PDF"
    GAZETTE_NOTIFICATION = "GAZETTE_NOTIFICATION"
    QCO_ORDER = "QCO_ORDER"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"
    SIT_SCHEDULE = "SIT_SCHEDULE"
    PORTAL_RECORD = "PORTAL_RECORD"
    LAB_ACCREDITATION = "LAB_ACCREDITATION"
    LICENCE_CERTIFICATE = "LICENCE_CERTIFICATE"
    CRS_REGISTRATION_RECORD = "CRS_REGISTRATION_RECORD"
    AHC_RECOGNITION = "AHC_RECOGNITION"
    BIS_ACT_STATUTE = "BIS_ACT_STATUTE"
    REGULATION = "REGULATION"


class LocatorType(str, Enum):
    """Specific locator mechanism used to isolate the evidence snippet."""
    PDF_PAGE = "PDF_PAGE"
    PDF_CLAUSE = "PDF_CLAUSE"
    PDF_TABLE = "PDF_TABLE"
    PDF_FIGURE = "PDF_FIGURE"
    GAZETTE_PAGE = "GAZETTE_PAGE"
    PORTAL_URL = "PORTAL_URL"
    CERTIFICATE_NUMBER = "CERTIFICATE_NUMBER"
    DATABASE_RECORD = "DATABASE_RECORD"
    ACT_SECTION = "ACT_SECTION"


class SourceReliabilityTier(str, Enum):
    """Primary vs secondary source distinction."""
    PRIMARY_NORMATIVE = "PRIMARY_NORMATIVE"          # Official Gazette, Normative Standard PDF, Statutory Act
    PRIMARY_PORTAL_RECORD = "PRIMARY_PORTAL_RECORD"  # Authoritative Manakonline / e-BIS public portal database
    SECONDARY_REFERENCE = "SECONDARY_REFERENCE"      # Press release, secondary directory index, committee minutes


class ValidationStatus(str, Enum):
    """Audit validation state."""
    VALID = "VALID"
    REQUIRES_REVALIDATION = "REQUIRES_REVALIDATION"
    REPAIRED = "REPAIRED"
    FLAGGED = "FLAGGED"


class SourceFamily(str, Enum):
    """15 BIS Knowledge Dimensions."""
    STANDARDS = "STANDARDS"
    PRODUCTS = "PRODUCTS"
    AMENDMENTS = "AMENDMENTS"
    GAZETTE = "GAZETTE"
    QCO = "QCO"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"
    SIT = "SIT"
    TESTS = "TESTS"
    SCHEMES = "SCHEMES"
    PROCEDURES = "PROCEDURES"
    LABORATORIES = "LABORATORIES"
    LICENCES = "LICENCES"
    CRS = "CRS"
    HALLMARKING = "HALLMARKING"
    CONSUMER = "CONSUMER"


class EvidenceRecord(BaseModel):
    """
    Authoritative, retrievable, citation-level evidence record backing an entity, claim, or graph edge.
    """
    model_config = ConfigDict(populate_by_name=True)

    evidence_id: str = Field(..., description="Unique canonical evidence identifier e.g. EVID-STD-IS-1786-2008-CL-8-1")
    entity_id: str = Field(..., description="Target entity ID or relationship edge key")
    source_family: SourceFamily = Field(..., description="BIS Source Dimension")
    source_authority: SourceAuthority = Field(default=SourceAuthority.BIS, description="Publishing government authority")
    source_type: SourceType = Field(default=SourceType.STANDARD_PDF, description="Source format / medium")
    reliability_tier: SourceReliabilityTier = Field(default=SourceReliabilityTier.PRIMARY_NORMATIVE, description="Primary vs secondary tier")
    
    # Document Identification
    document_id: Optional[str] = Field(None, description="Physical/processed document identifier")
    citation_title: str = Field(..., description="Official standard title, QCO order name, or gazette title")
    
    # Exact Locator Coordinates
    locator_type: LocatorType = Field(default=LocatorType.PDF_CLAUSE, description="Locator mechanism")
    locator_value: str = Field(..., description="Exact locator coordinate e.g. Clause 8.1, Table 3, Page 4, CM/L-8100123")
    clause_number: Optional[str] = Field(None, description="Normative clause number")
    page_number: Optional[int] = Field(None, description="1-indexed PDF page number")
    table_or_figure: Optional[str] = Field(None, description="Table or Figure reference")
    verbatim_quote: Optional[str] = Field(None, description="Exact extracted textual snippet grounding the claim")
    
    # Cryptographic Fingerprints
    document_sha256: Optional[str] = Field(None, description="SHA-256 hash of the complete source document")
    content_sha256: Optional[str] = Field(None, description="SHA-256 hash of the extracted evidence text snippet")
    
    # Temporal & Gazette Metadata
    effective_date: Optional[str] = Field(None, description="Effective publication/enforcement date YYYY-MM-DD")
    gazette_notification_number: Optional[str] = Field(None, description="Gazette S.O. / G.S.R. number")
    amendment_reference: Optional[str] = Field(None, description="Amendment slip reference if applicable")
    
    # Classification & Lifecycle
    evidentiary_strength: EvidentiaryStrength = Field(default=EvidentiaryStrength.EVIDENCE_VERIFIED, description="6-level taxonomy classification")
    is_current_normative: bool = Field(default=True, description="True if valid for current normative claims; False if historical only")
    supersedes_evidence_id: Optional[str] = Field(None, description="Evidence ID of previous edition/order this record replaces")
    superseded_by_evidence_id: Optional[str] = Field(None, description="Evidence ID of newer edition/order replacing this record")
    validation_status: ValidationStatus = Field(default=ValidationStatus.VALID, description="Audit validation status")
    
    # Provenance & Audit Trails
    provenance_url: Optional[str] = Field(None, description="Official government/BIS portal URL")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Acquisition timestamp")
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Verification timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional technical metadata")

    @classmethod
    def compute_sha256(cls, text: str) -> str:
        """Computes SHA-256 cryptographic hash of text string."""
        if not text:
            return ""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def format_citation(self) -> str:
        """Generates clean human-readable and RAG-friendly citation string."""
        parts = [self.citation_title]
        if self.locator_value:
            parts.append(self.locator_value)
        if self.page_number and self.locator_type != LocatorType.PDF_PAGE:
            parts.append(f"Page {self.page_number}")
        if self.amendment_reference:
            parts.append(f"[{self.amendment_reference}]")
        if self.evidentiary_strength == EvidentiaryStrength.STALE_EVIDENCE:
            parts.append("(HISTORICAL STATE - SUPERSEDED)")
        return ", ".join(parts)
