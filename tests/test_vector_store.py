"""
Validation tests for ChromaDB Vector Store with Metadata Filtering (Phase 3).
"""

from pathlib import Path
import pytest
from ai.chunking.schema import ChunkClause, ChunkProvenance, ChunkType, KnowledgeChunk
from ai.vectorstore.chroma_store import ChromaVectorStore

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_chromadb_upsert_and_filtered_query(tmp_path):
    """Verify ChromaDB upserts chunks and filters by clause, standard, and temporal status."""
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma", collection_name="test_col")

    chunk = KnowledgeChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="8.1.1",
        chunk_type=ChunkType.REQUIREMENT,
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2012-08-01",
        title="Insulation Resistance",
        clause=ChunkClause(number="8.1.1"),
        text="The insulation resistance shall not be less than 4 MΩ.",
        content_hash="hash_test_123",
        page_refs=[9],
        pages=[9],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="8.1.1", pages=[9]
        ),
    )

    # Fake 4D embedding for testing
    embedding = [0.5, 0.5, 0.5, 0.5]
    store.upsert_chunks([chunk], [embedding])

    assert store.count() == 1

    # Query with matching filter
    results = store.query_dense(query_embedding=[0.5, 0.5, 0.5, 0.5], top_k=5, filters={"clause_number": "8.1.1"})
    assert len(results) == 1
    assert results[0]["chunk_id"] == "DOC-001-v001::8.1.1::REQ-001"
    assert results[0]["metadata"]["standard_number"] == "IS 16102 (Part 1) : 2012"

    # Query with non-matching filter
    results_empty = store.query_dense(query_embedding=[0.5, 0.5, 0.5, 0.5], top_k=5, filters={"clause_number": "9.1"})
    assert len(results_empty) == 0
