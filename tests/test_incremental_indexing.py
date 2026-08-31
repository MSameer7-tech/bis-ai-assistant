"""
Validation tests for Incremental Indexing and Vector Reuse (Step 13).
"""

from pathlib import Path
import pytest
from ai.chunking.schema import ChunkClause, ChunkProvenance, ChunkType, KnowledgeChunk
from ai.embeddings.manager import EmbeddingManager
from ai.embeddings.provider import DeterministicEmbeddingProvider
from ai.ingestion.manifest import IngestionManifestManager
from ai.vectorstore.bm25_index import BM25Index
from ai.vectorstore.chroma_store import ChromaVectorStore
from ai.vectorstore.indexer import IncrementalIndexer

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_incremental_indexing_cycle_a_b_c(tmp_path):
    """
    Validates the 3-stage incremental indexing lifecycle:
    Test A: Index 5 chunks -> 5 generated, 0 reused.
    Test B: Re-index without changes -> 0 generated, 5 reused.
    Test C: Modify 1 chunk -> 1 generated, 4 reused.
    """
    chroma_dir = tmp_path / "chroma"
    bm25_path = tmp_path / "bm25.json"
    cache_path = tmp_path / "cache.json"
    manifest_path = tmp_path / "manifest.json"

    provider = DeterministicEmbeddingProvider(dimension=64)
    manager = EmbeddingManager(provider=provider, cache_path=cache_path)
    v_store = ChromaVectorStore(persist_directory=chroma_dir, collection_name="test_inc")
    bm25 = BM25Index(storage_path=bm25_path)
    manifest = IngestionManifestManager(manifest_path=manifest_path)

    indexer = IncrementalIndexer(
        vector_store=v_store,
        bm25_index=bm25,
        embedding_manager=manager,
        manifest_manager=manifest,
    )

    chunks = [
        KnowledgeChunk(
            chunk_id=f"DOC-001::clause_{i}::REQ-001",
            document_id="DOC-001",
            source_id="SRC-001",
            chunk_type=ChunkType.REQUIREMENT,
            clause_number=f"{i}.1",
            title=f"Clause {i}.1",
            clause=ChunkClause(number=f"{i}.1"),
            text=f"Requirement text for clause {i}.1 with limit {i}0 MΩ.",
            content_hash=f"hash_{i}",
            page_refs=[i],
            provenance=ChunkProvenance(
                document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause=f"{i}.1", pages=[i]
            ),
        )
        for i in range(1, 6)
    ]

    # --- Test A: Initial Indexing ---
    metrics_a = indexer.index_chunks(chunks)
    assert metrics_a["total_chunks"] == 5
    assert metrics_a["added_count"] == 5
    assert metrics_a["unchanged_count"] == 0
    assert metrics_a["embeddings_generated"] == 5
    assert metrics_a["embeddings_reused"] == 0

    # --- Test B: Re-index without changes ---
    metrics_b = indexer.index_chunks(chunks)
    assert metrics_b["total_chunks"] == 5
    assert metrics_b["added_count"] == 0
    assert metrics_b["modified_count"] == 0
    assert metrics_b["unchanged_count"] == 5
    assert metrics_b["embeddings_generated"] == 0
    assert metrics_b["embeddings_reused"] == 5

    # --- Test C: Modify exactly one chunk ---
    modified_chunks = [c.model_copy(deep=True) for c in chunks]
    modified_chunks[2].text = "Requirement text for clause 3.1 with MODIFIED limit 99 MΩ."
    modified_chunks[2].content_hash = "hash_MODIFIED_99"

    metrics_c = indexer.index_chunks(modified_chunks)
    assert metrics_c["total_chunks"] == 5
    assert metrics_c["added_count"] == 0
    assert metrics_c["modified_count"] == 1
    assert metrics_c["unchanged_count"] == 4
    assert metrics_c["embeddings_generated"] == 1
    assert metrics_c["embeddings_reused"] == 4

    # --- Test D: Delete exactly one chunk (Step 11) ---
    subset_chunks = [modified_chunks[0], modified_chunks[1], modified_chunks[3], modified_chunks[4]]  # deleted chunk 2
    metrics_d = indexer.index_chunks(subset_chunks)
    assert metrics_d["total_chunks"] == 4
    assert metrics_d["deleted_count"] == 1
    assert metrics_d["unchanged_count"] == 4
    assert metrics_d["vector_store_count"] == 4
    assert v_store.get_chunk("DOC-001::clause_3::REQ-001") is None
