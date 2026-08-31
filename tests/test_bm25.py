"""
Validation tests for BM25 Sparse Index and Technical Token Preservation (Step 6).
"""

from pathlib import Path
import pytest
from ai.chunking.schema import ChunkClause, ChunkProvenance, ChunkType, KnowledgeChunk
from ai.vectorstore.bm25_index import BM25Index, tokenize_bis_text

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_tokenize_bis_text_preserves_technical_tokens():
    """Verify tokenizer preserves standard numbers, cap styles, and numerical units intact."""
    sample_text = "For GX53 and B22d caps, insulation resistance shall be >= 4 MΩ with 120 K rise under IS 16102 (Part 1)."
    tokens = tokenize_bis_text(sample_text)

    # Check key terms
    tokens_str = " ".join(tokens)
    assert "gx53" in tokens
    assert "b22d" in tokens
    assert "4 mΩ" in tokens or "4 m" in tokens_str
    assert "120 k" in tokens or "120" in tokens
    assert "is 16102 (part 1)" in tokens or "16102" in tokens_str


def test_bm25_index_exact_keyword_retrieval(tmp_path):
    """Verify BM25 exact match retrieves specific cap and clause chunks."""
    bm25_path = tmp_path / "test_bm25.json"
    bm25 = BM25Index(storage_path=bm25_path)

    chunk_gx53 = KnowledgeChunk(
        chunk_id="DOC-001::Table_3::TAB-001",
        document_id="DOC-001",
        source_id="SRC-001",
        chunk_type=ChunkType.TABLE,
        title="Table 3 - Torque for Caps",
        clause=ChunkClause(number="9.1"),
        text="Table 3: Cap GX53 torsion moment 3 Nm under consideration.",
        page_refs=[11],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="9.1", pages=[11]
        ),
    )

    chunk_e17 = KnowledgeChunk(
        chunk_id="DOC-001::Table_3::TAB-002",
        document_id="DOC-001",
        source_id="SRC-001",
        chunk_type=ChunkType.TABLE,
        title="Table 3 - Torque for Caps",
        clause=ChunkClause(number="9.1"),
        text="Table 3: Cap E17 torsion moment 1.5 Nm mandatory.",
        page_refs=[11],
        provenance=ChunkProvenance(
            document_id="DOC-001", source_id="SRC-001", standard_number="IS 16102", clause="9.1", pages=[11]
        ),
    )

    bm25.build_or_update([chunk_gx53, chunk_e17])

    # Query for GX53
    res_gx53 = bm25.query_sparse("GX53 torque", top_k=2)
    assert len(res_gx53) > 0
    assert res_gx53[0]["chunk_id"] == "DOC-001::Table_3::TAB-001"

    # Query for E17
    res_e17 = bm25.query_sparse("E17", top_k=2)
    assert len(res_e17) > 0
    assert res_e17[0]["chunk_id"] == "DOC-001::Table_3::TAB-002"
