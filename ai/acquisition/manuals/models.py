"""
Product Manuals Data Models
Authoritative schemas for BIS Product Manuals, grouping guidelines, sampling, and marking.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ProductManualRecord(BaseModel):
    """Authoritative record for a BIS Product Manual."""
    manual_id: str = Field(..., description="Unique manual ID (e.g., PM-IS-374-2019)")
    product_id: Optional[str] = Field(None, description="Linked canonical product ID")
    standard_id: str = Field(..., description="Applicable Indian Standard number (e.g., IS 374)")
    scope: str = Field(..., description="Product scope covered by the manual")
    product_characteristics: List[str] = Field(default_factory=list, description="Key technical parameters/characteristics")
    sampling_requirements: str = Field(..., description="Normative sampling and lot sizing rules")
    test_equipment: List[str] = Field(default_factory=list, description="Required laboratory and in-house testing equipment")
    tests: List[str] = Field(default_factory=list, description="List of routine, type, and acceptance tests specified")
    sit_reference: str = Field(..., description="Linked Scheme of Inspection and Testing (SIT) reference ID")
    grouping_guidelines: str = Field(..., description="Guidelines for grouping product varieties for grant and scope expansion")
    marking_requirements: str = Field(..., description="Statutory ISI/CRS standard mark, labelling, and packaging rules")
    source_url: str = Field(..., description="Authoritative BIS portal link")
    document_id: Optional[str] = Field(None, description="Internal document identifier")
    effective_from: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    effective_to: Optional[str] = Field(None, description="Superseded date if applicable")
    content_hash: Optional[str] = Field(None, description="SHA256 checksum of source document")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of ingestion")
