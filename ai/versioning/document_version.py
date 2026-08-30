"""
Document Versioning Models and Manifest Management for BIS Standards (Step 6 & 7).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentVersion(BaseModel):
    version_id: str
    document_id: str
    version_number: int = 1
    version_label: str
    standard_edition: Optional[str] = None
    sha256: str
    file_size_bytes: int = 0
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    status: str = "active"  # "active", "superseded", "provisional", "draft"
    superseded_by: Optional[str] = None
    change_summary: Optional[str] = None
    local_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def make_version_id(document_id: str, version_seq: int = 1) -> str:
    """Generates standardized version ID: e.g. DOC-001-v001"""
    return f"{document_id.upper()}-v{version_seq:03d}"
