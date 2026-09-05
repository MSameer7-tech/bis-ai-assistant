"""
Pydantic Schemas for the Master BIS Statutory Gazette Registry.
Encapsulates official Ministry Gazette Notifications, order titles, and associated standard references.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class GazetteRecord(BaseModel):
    """Authoritative representation of a Ministry / BIS Gazette Notification."""
    gazette_id: str = Field(..., description="Unique gazette record identifier, e.g. GAZ-2024-GSR-542")
    ministry: str = Field("Ministry of Consumer Affairs, Food & Public Distribution", description="Issuing Central Ministry")
    order_title: str = Field(..., description="Official Title of the Gazette Notification")
    order_number: str = Field(..., description="Official S.O. / G.S.R. Order Number")
    gazette_type: str = Field("EXTRAORDINARY", description="Gazette Type (EXTRAORDINARY, WEEKLY, ORDINARY)")
    publication_date: str = Field("2024-01-15", description="Date of publication in The Gazette of India (YYYY-MM-DD)")
    enforcement_date: str = Field("2024-07-15", description="Date when statutory requirements become mandatory")
    related_standards: List[str] = Field(default_factory=list, description="List of Indian Standards mandated/referenced")
    is_mandatory_qco: bool = Field(True, description="Whether this notification enforces mandatory QCO / ISI mark")
    source_url: str = Field(..., description="Official URL on egazette.nic.in / bis.gov.in")
    content_hash: Optional[str] = Field(None, description="SHA256 checksum of gazette notification PDF")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        frozen = False
