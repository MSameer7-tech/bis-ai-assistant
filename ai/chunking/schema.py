"""
Phase 2E Chunk Schema and Typed Models (Step 7).
Defines self-contained semantic knowledge chunks with immutable stable identities,
version lineage (DOC-001-v001::8.1.1::REQ-001), content hashes, clause hierarchies,
normative modal keywords, structured tables, definitions, and cross-references.
"""

import hashlib
from enum import Enum
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
    PROHIBITION = "prohibition"
    UNDER_CONSIDERATION = "under_consideration"
    RECOMMENDATION = "recommendation"
    INFORMATIVE = "informative"


class ChunkClause(BaseModel):
    number: str
    title: str
    depth: int = 1
    parent_clause: Optional[str] = None
    hierarchy_path: List[str] = Field(default_factory=list)
    section_number: Optional[str] = None
    section_title: Optional[str] = None


class NormativeContext(BaseModel):
    normative_force: NormativeForce = NormativeForce.MANDATORY
    modal_keywords: List[str] = Field(default_factory=list)
    verbatim_normative_statements: List[str] = Field(default_factory=list)
    compliance_verification_method: Optional[str] = None


class ChunkCrossReference(BaseModel):
    standard: str
    target_location: Optional[str] = None
    relationship: str = "normative_reference"
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
    chunk_id: str
    document_id: str
    version_id: Optional[str] = None
    source_id: str
    chunk_type: ChunkType
    title: Optional[str] = None
    clause: ChunkClause
    normative_context: NormativeContext = Field(default_factory=NormativeContext)
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
    page_refs: List[int]
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
