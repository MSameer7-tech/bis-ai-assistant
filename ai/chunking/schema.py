"""
Phase 2E Chunk Schema and Typed Models.
Defines self-contained semantic knowledge chunks for standard specifications and regulations.
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


class ChunkClause(BaseModel):
    number: str
    title: str
    depth: int = 1
    parent_clause: Optional[str] = None


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
    clause: ChunkClause
    text: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    references: List[Dict[str, Any]] = Field(default_factory=list)
    table_data: Optional[Dict[str, Any]] = None
    page_refs: List[int]
    provenance: ChunkProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict)


def make_chunk_id(doc_id: str, clause_num: str, seq: int = 1, prefix: str = "C") -> str:
    """Generates standard stable chunk ID: e.g. DOC-001-C008-001"""
    doc_clean = doc_id.upper()
    c_clean = clause_num.replace(".", "_")
    return f"{doc_clean}-{prefix}_{c_clean}-{seq:03d}"
