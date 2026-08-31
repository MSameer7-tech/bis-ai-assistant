"""
Validation tests for Embeddings Providers and Content-Hash Caching Manager (Phase 3).
"""

from pathlib import Path
import pytest
from ai.chunking.schema import ChunkClause, ChunkProvenance, ChunkType, KnowledgeChunk
from ai.embeddings.manager import EmbeddingManager
from ai.embeddings.provider import DeterministicEmbeddingProvider, SentenceTransformerEmbeddingProvider, get_embedding_provider

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_deterministic_provider_dimensions_and_normalization():
    """Verify deterministic embedding dimensions and unit length."""
    provider = DeterministicEmbeddingProvider(dimension=384)
    assert provider.dimension == 384
    assert provider.model_name == "deterministic-v1"

    texts = ["Insulation resistance shall be not less than 4 MΩ.", "Cap temperature rise limit is 120 K."]
    vecs = provider.embed_texts(texts)
    assert len(vecs) == 2
    assert len(vecs[0]) == 384

    # Verify unit length L2 norm
    norm = sum(v * v for v in vecs[0])
    assert pytest.approx(norm, 0.01) == 1.0


def test_sentence_transformer_provider_or_fallback():
    """Verify SentenceTransformerEmbeddingProvider returns consistent dimensions."""
    provider = SentenceTransformerEmbeddingProvider(model_name="all-MiniLM-L6-v2")
    assert provider.dimension == 384
    vec = provider.embed_query("Insulation resistance")
    assert len(vec) == 384


def test_embedding_manager_content_hash_caching(tmp_path):
    """Verify embedding manager reuses cached vectors for identical content hashes."""
    cache_file = tmp_path / "test_cache.json"
    provider = DeterministicEmbeddingProvider(dimension=64)
    manager = EmbeddingManager(provider=provider, cache_path=cache_file)

    chunk1 = KnowledgeChunk(
        chunk_id="DOC-001::8.1.1::REQ-001",
        document_id="DOC-001",
        source_id="SRC-001",
        chunk_type=ChunkType.REQUIREMENT,
        title="Insulation Resistance",
        clause=ChunkClause(number="8.1.1"),
        text="Insulation resistance shall not be less than 4 MΩ.",
        content_hash="hash_alpha_123",
        page_refs=[9],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="8.1.1", pages=[9]
        ),
    )

    # First run -> generates 1 embedding
    vecs1, metrics1 = manager.get_or_create_embeddings([chunk1])
    assert metrics1["generated"] == 1
    assert metrics1["reused"] == 0

    # Second run with same content_hash -> reuses 1 embedding
    vecs2, metrics2 = manager.get_or_create_embeddings([chunk1])
    assert metrics2["generated"] == 0
    assert metrics2["reused"] == 1
    assert vecs1[0] == vecs2[0]
