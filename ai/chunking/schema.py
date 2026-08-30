"""
Phase 2E Chunk Schema and Typed Models.
Defines self-contained semantic knowledge chunks for standard specifications and regulations
with explicit clause hierarchy, normative modal keywords, structured tables, definitions,
and cross-standard relationship references.
"""

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
    source_id: str
    chunk_type: ChunkType
    title: Optional[str] = None
    clause: ChunkClause
    normative_context: NormativeContext = Field(default_factory=NormativeContext)
    text: str
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


def make_chunk_id(doc_id: str, clause_num: str, seq: int = 1, prefix: str = "C") -> str:
    """Generates standard stable chunk ID: e.g. DOC-001-C_8_1_1-001"""
    doc_clean = doc_id.upper()
    c_clean = str(clause_num).replace(".", "_")
    return f"{doc_clean}-{prefix}_{c_clean}-{seq:03d}"
