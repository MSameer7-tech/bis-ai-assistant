"""
Discovery and Crawler Data Models for BIS Automated Acquisition.
Defines clean contracts for discovered standards and regulatory notifications.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from ai.acquisition.url_normalizer import normalize_url
from ai.taxonomy.validator import get_taxonomy_validator


class DiscoveryDocumentType(str, Enum):
    STANDARD = "standard"
    AMENDMENT = "amendment"
    GAZETTE_NOTIFICATION = "gazette_notification"
    QCO = "qco"
    ORDER = "order"
    GUIDELINE = "guideline"


def normalize_standard_number(std_num: str) -> str:
    """
    Normalizes BIS standard number formatting (e.g. 'IS1786:2024' -> 'IS 1786 : 2024').
    """
    if not std_num:
        return ""
    clean = std_num.strip()
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r"\s*:\s*", " : ", clean)
    clean = re.sub(r"^IS(?!\s)", "IS ", clean, flags=re.IGNORECASE)
    return clean


class DiscoveredStandard(BaseModel):
    """Clean data contract for an authoritative standard discovered by the crawler."""

    standard_number: str = Field(..., description="Canonical standard code, e.g. 'IS 1786 : 2024'")
    title: str = Field(..., description="Full official title of the standard")
    edition: Optional[str] = Field(None, description="Edition or revision label, e.g. '2024' or 'Fifth Revision'")
    document_type: DiscoveryDocumentType = Field(default=DiscoveryDocumentType.STANDARD, description="Type of standard artifact")
    domain: str = Field(..., description="Controlled BIS product domain from taxonomy")
    category: Optional[str] = Field(None, description="Sub-category under domain")
    product_type: Optional[str] = Field(None, description="Specific product type identifier")
    source_url: str = Field(..., description="Official BIS portal/gazette source page URL")
    pdf_url: Optional[str] = Field(None, description="Direct download URL for document PDF")
    authority: str = Field(default="Bureau of Indian Standards", description="Issuing technical committee or ministry")
    pub_date: Optional[str] = Field(None, description="Publication date in YYYY-MM-DD format")
    valid_from: Optional[str] = Field(None, description="Effective start date in YYYY-MM-DD format")
    valid_until: Optional[str] = Field(None, description="Superseded date in YYYY-MM-DD format, or None if current")
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when the crawler discovered this record"
    )
    content_summary: Optional[str] = Field(None, description="Brief scope or clause summary if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional crawler metadata")

    @field_validator("standard_number")
    @classmethod
    def validate_and_normalize_standard_number(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("standard_number cannot be empty")
        normalized = normalize_standard_number(v)
        if not normalized.upper().startswith("IS ") and not normalized.upper().startswith("QCO"):
            raise ValueError(f"standard_number '{v}' must begin with 'IS ' or regulatory prefix 'QCO'")
        return normalized

    @field_validator("source_url", "pdf_url")
    @classmethod
    def validate_and_normalize_urls(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = normalize_url(v)
        if not cleaned:
            return None
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError(f"Invalid URL protocol: '{cleaned}'. Must start with http:// or https://")
        return cleaned

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("domain cannot be empty")
        domain_clean = v.strip().lower()
        if domain_clean == "unknown":
            return domain_clean
        validator = get_taxonomy_validator()
        valid_domains = validator.get_valid_domains()
        if domain_clean not in valid_domains:
            raise ValueError(
                f"Domain '{v}' is invalid. Must be one of controlled taxonomy domains: {valid_domains} or 'unknown'"
            )
        return domain_clean

    @field_validator("pub_date", "valid_from", "valid_until")
    @classmethod
    def validate_iso_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        val = str(v).strip().split("T")[0]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
            try:
                datetime.fromisoformat(val)
                return val
            except ValueError as e:
                raise ValueError(f"Invalid calendar date '{v}': {e}")
        elif re.fullmatch(r"\d{4}", val):
            return f"{val}-01-01"
        else:
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD or YYYY format")


class DiscoveryBatchReport(BaseModel):
    """Summary report produced by a crawl or discovery run."""

    discovered_count: int = 0
    new_count: int = 0
    modified_count: int = 0
    unchanged_count: int = 0
    invalid_count: int = 0
    items: List[DiscoveredStandard] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
