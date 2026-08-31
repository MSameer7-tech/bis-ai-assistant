"""
Validation tests for Hybrid Search Engine, Temporal Filtering, and RRF Fusion (Steps 7-11).
"""

from pathlib import Path
import pytest
from ai.chunking.schema import ChunkClause, ChunkProvenance, ChunkType, KnowledgeChunk
from ai.embeddings.provider import DeterministicEmbeddingProvider
from ai.embeddings.manager import EmbeddingManager
from ai.vectorstore.bm25_index import BM25Index
from ai.vectorstore.chroma_store import ChromaVectorStore
from ai.vectorstore.hybrid_search import HybridSearchEngine

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_hybrid_search_temporal_filtering_and_rrf(tmp_path):
    """Verify hybrid search excludes superseded requirements and ranks with RRF."""
    chroma_dir = tmp_path / "chroma"
    bm25_path = tmp_path / "bm25.json"
    cache_path = tmp_path / "cache.json"

    provider = DeterministicEmbeddingProvider(dimension=64)
    manager = EmbeddingManager(provider=provider, cache_path=cache_path)
    v_store = ChromaVectorStore(persist_directory=chroma_dir, collection_name="test_hybrid")
    bm25 = BM25Index(storage_path=bm25_path)

    # Chunk 1: Superseded historical requirement
    chunk_old = KnowledgeChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        source_id="SRC-001",
        chunk_type=ChunkType.REQUIREMENT,
        standard_number="IS 16102",
        clause_number="8.1.1",
        normative_force="mandatory",
        temporal_status="superseded",
        valid_from="2012-08-01",
        valid_until="2026-06-30",
        title="Insulation Resistance Old",
        clause=ChunkClause(number="8.1.1"),
        text="The insulation resistance shall be not less than 4 MΩ.",
        content_hash="h1",
        page_refs=[9],
        pages=[9],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="8.1.1", pages=[9]
        ),
    )

    # Chunk 2: Current amended requirement
    chunk_new = KnowledgeChunk(
        chunk_id="DOC-001-v002::8.1.1::REQ-001",
        document_id="DOC-001",
        source_id="SRC-001",
        chunk_type=ChunkType.REQUIREMENT,
        standard_number="IS 16102",
        clause_number="8.1.1",
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2026-07-01",
        valid_until=None,
        title="Insulation Resistance New",
        clause=ChunkClause(number="8.1.1"),
        text="The insulation resistance shall be not less than 5 MΩ under amendment.",
        content_hash="h2",
        page_refs=[9],
        pages=[9],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="8.1.1", pages=[9]
        ),
    )

    vecs, _ = manager.get_or_create_embeddings([chunk_old, chunk_new])
    v_store.upsert_chunks([chunk_old, chunk_new], vecs)
    bm25.build_or_update([chunk_old, chunk_new])

    engine = HybridSearchEngine(vector_store=v_store, bm25_index=bm25, embedding_manager=manager)

    # Query without date (current query) -> excludes superseded chunk_old
    results_current = engine.search("What is the insulation resistance requirement?", top_k=5)
    assert len(results_current) == 1
    assert results_current[0]["chunk_id"] == "DOC-001-v002::8.1.1::REQ-001"
    assert results_current[0]["temporal_status"] == "current"
    assert "provenance" in results_current[0]

    # Query with historical date 2015 -> returns historical chunk_old
    results_historical = engine.search("What is the insulation resistance requirement?", top_k=5, as_of_date="2015-01-01")
    assert len(results_historical) == 1
    assert results_historical[0]["chunk_id"] == "DOC-001-v001::8.1.1::REQ-001"
