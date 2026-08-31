"""
Structure-Aware Semantic Chunking Schema and Contracts for Phase 2E and Phase 3.
Freezes the chunk contract for Vector Database indexing and Hybrid Retrieval.
"""

from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    SCOPE = "scope"
    DEFINITION = "definition"
    REFERENCE = "reference"
    REQUIREMENT = "requirement"
    TEST_METHOD = "test_method"
    CONDITION = "condition"
    TABLE = "table"
    SAMPLING = "sampling"
    COMPLIANCE = "compliance"
    ANNEX = "annex"
    NOTE = "note"
    GENERAL_PROVISION = "general_provision"


class NormativeForce(str, Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    RECOMMENDATION = "recommended"
    PERMITTED = "permitted"
    PROHIBITED = "prohibited"
    PROHIBITION = "prohibited"
    UNDER_CONSIDERATION = "under_consideration"
    INFORMATIVE = "informative"


class NormativeContext(BaseModel):
    normative_force: NormativeForce = NormativeForce.INFORMATIVE
    modal_keywords: List[str] = Field(default_factory=list)
    verbatim_normative_statements: List[str] = Field(default_factory=list)
    compliance_verification_method: Optional[str] = None


class ChunkClause(BaseModel):
    number: str
    title: Optional[str] = None
    depth: int = 1
    parent_clause: Optional[str] = None
    hierarchy_path: List[str] = Field(default_factory=list)
    section_number: Optional[str] = None
    section_title: Optional[str] = None


class ChunkCrossReference(BaseModel):
    standard: str
    target_location: Optional[str] = None
    relationship: str = "references"
    reference_type: str = "normative"
    context_snippet: Optional[str] = None


class ChunkProvenance(BaseModel):
    document_id: str
    source_id: str
    standard_number: str
    clause: str
    pages: List[int]
    section: Optional[str] = None
    original_text_snippet: Optional[str] = None


class KnowledgeChunk(BaseModel):
    """
    Frozen Chunk Contract for BIS Knowledge Retrieval (Step 1).
    Guarantees consistent schema across all pilot and production standards.
    """
    chunk_id: str
    document_id: str
    version_id: Optional[str] = None
    source_id: str
    standard_number: Optional[str] = None
    clause_number: Optional[str] = None
    parent_clause: Optional[str] = None
    section_number: Optional[str] = None
    chunk_type: ChunkType
    title: Optional[str] = None
    clause: ChunkClause
    normative_context: NormativeContext = Field(default_factory=NormativeContext)
    normative_force: str = "informative"
    text: str
    content_hash: Optional[str] = None
    term: Optional[str] = None
    definition: Optional[str] = None
    table_number: Optional[str] = None
    table_data: Optional[Dict[str, Any]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    references: List[ChunkCrossReference] = Field(default_factory=list)
    pages: List[int] = Field(default_factory=list)
    page_refs: List[int] = Field(default_factory=list)
    temporal_status: str = "current"  # "current", "superseded", "provisional"
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    provenance: ChunkProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict)


def compute_chunk_content_hash(text: str, structured_data: Optional[Dict[str, Any]] = None) -> str:
    """Computes deterministic SHA-256 hash of chunk content for change detection."""
    hasher = hashlib.sha256()
    hasher.update(text.strip().encode("utf-8"))
    if structured_data:
        hasher.update(str(sorted(structured_data.items())).encode("utf-8"))
    return hasher.hexdigest()


def make_chunk_id(doc_or_version_id: str, clause_num: str, seq: int = 1, prefix: str = "REQ") -> str:
    """Generates standard stable chunk ID: e.g. DOC-001-v001::8.1.1::REQ-001"""
    d_clean = str(doc_or_version_id).strip()
    c_clean = str(clause_num).strip()
    p_clean = str(prefix).strip().upper()
    return f"{d_clean}::{c_clean}::{p_clean}-{seq:03d}"
