"""
Phase 2E Structure-Aware Semantic Chunking Subpackage.
Produces self-contained, typed knowledge chunks preserving clause hierarchy,
machine-readable requirements, conditions, references, and exact page provenance.
"""

from ai.chunking.chunker import StructureAwareChunker, chunk_all_documents, chunk_document
from ai.chunking.rules import extract_normative_context
from ai.chunking.schema import (
    ChunkClause,
    ChunkCrossReference,
    ChunkProvenance,
    ChunkType,
    KnowledgeChunk,
    NormativeContext,
    NormativeForce,
    make_chunk_id,
)
from ai.chunking.table_chunker import TableChunker
from ai.chunking.validators import ChunkValidator, validate_chunks

__all__ = [
    "ChunkType",
    "ChunkClause",
    "ChunkCrossReference",
    "ChunkProvenance",
    "KnowledgeChunk",
    "NormativeContext",
    "NormativeForce",
    "make_chunk_id",
    "extract_normative_context",
    "TableChunker",
    "ChunkValidator",
    "validate_chunks",
    "StructureAwareChunker",
    "chunk_document",
    "chunk_all_documents",
]
