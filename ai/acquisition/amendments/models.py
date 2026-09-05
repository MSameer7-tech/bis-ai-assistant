"""
Pydantic Schemas for the Master BIS Amendments Registry.
Encapsulates versioned normative amendments, corrigenda, affected clauses, and gazette references.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AmendmentRecord(BaseModel):
    """Authoritative representation of a published BIS Amendment / Corrigendum."""
    amendment_id: str = Field(..., description="Unique amendment identifier, e.g. AMD-IS-1786-A1")
    standard_id: str = Field(..., description="Canonical standard ID, e.g. STD-IS-001786-2024")
    is_number: str = Field(..., description="Base Indian Standard number, e.g. IS 1786")
    amendment_number: int = Field(..., description="Sequential amendment number (1, 2, 3...)")
    gazette_notification_number: Optional[str] = Field(None, description="Official Gazette notification reference")
    gazette_date: Optional[str] = Field(None, description="Gazette notification publication date (YYYY-MM-DD)")
    effective_date: Optional[str] = Field(None, description="Date from which amendment comes into force")
    summary: str = Field(..., description="Summary of technical changes introduced by amendment")
    affected_clauses: List[str] = Field(default_factory=list, description="List of clauses modified/inserted by amendment")
    content_hash: Optional[str] = Field(None, description="SHA256 checksum of amendment document")
    source_url: str = Field(..., description="Authoritative BIS amendment URL")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        frozen = False
