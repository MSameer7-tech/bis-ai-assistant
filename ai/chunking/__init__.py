"""
Phase 2E Structure-Aware Semantic Chunking Subpackage.
Produces self-contained, typed knowledge chunks preserving clause hierarchy,
machine-readable requirements, conditions, references, and exact page provenance.
"""

from ai.chunking.chunker import StructureAwareChunker, chunk_all_documents, chunk_document
from ai.chunking.schema import (
    ChunkClause,
    ChunkProvenance,
    ChunkType,
    KnowledgeChunk,
    make_chunk_id,
)

__all__ = [
    "ChunkType",
    "ChunkClause",
    "ChunkProvenance",
    "KnowledgeChunk",
    "make_chunk_id",
    "StructureAwareChunker",
    "chunk_document",
    "chunk_all_documents",
]
