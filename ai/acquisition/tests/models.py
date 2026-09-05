"""
Normalized Test Entity Data Models
Authoritative schemas for discrete test requirements, test methods, units, and frequencies.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TestRecord(BaseModel):
    """Authoritative record for an individual standardized test."""
    test_id: str = Field(..., description="Unique Test identifier (e.g., TEST-IS-374-AIR-DELIVERY)")
    test_name: str = Field(..., description="Official test title")
    test_method: str = Field(..., description="Prescribed normative test standard and clause")
    applicable_standard: str = Field(..., description="Parent product Indian Standard number")
    requirement: str = Field(..., description="Prescribed numerical or qualitative acceptance criteria")
    unit: Optional[str] = Field(None, description="Physical engineering unit (e.g., m3/min, N/mm2, MPa, V, deg C)")
    frequency: str = Field(..., description="Factory SIT routine or acceptance test frequency")
    source_document: str = Field(..., description="Document provenance citation")
    source_clause_page: str = Field(..., description="Specific clause, table, or section in standard/SIT")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of ingestion")
