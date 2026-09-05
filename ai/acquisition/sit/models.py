"""
Scheme of Inspection and Testing (SIT) Data Models
Authoritative schemas for BIS factory testing frequencies, sample sizes, test methods, and pass/fail limits.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SITRecord(BaseModel):
    """Authoritative record for a BIS Scheme of Inspection and Testing (SIT)."""
    sit_id: str = Field(..., description="Unique SIT ID (e.g., SIT-IS-374-2019)")
    standard_id: str = Field(..., description="Applicable Indian Standard number")
    product_id: Optional[str] = Field(None, description="Linked product ID")
    test_id: str = Field(..., description="Normalized test identifier (e.g., TEST-IS-374-AIR-DELIVERY)")
    test_name: str = Field(..., description="Official test name")
    requirement: str = Field(..., description="Exact numerical / physical requirement and limit")
    test_method: str = Field(..., description="Normative test method and standard clause")
    frequency: str = Field(..., description="Testing frequency (e.g., 1 per batch, 1 per 500 units, continuous)")
    sample_size: str = Field(..., description="Sample size required for testing")
    sampling_method: str = Field(..., description="Statistical or random sampling method")
    record_requirement: str = Field(..., description="Quality log / test record retention requirement")
    source_document: str = Field(..., description="Document citation from which SIT was extracted")
    source_url: str = Field(..., description="Authoritative source URL")
    document_id: Optional[str] = Field(None, description="Internal document identifier")
    effective_from: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    effective_to: Optional[str] = Field(None, description="Superseded date if applicable")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of ingestion")
