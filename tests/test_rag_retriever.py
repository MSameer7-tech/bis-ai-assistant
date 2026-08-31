"""
Tests for Phase 4 Batch 1: models.py and retriever.py
"""
import pytest
from ai.rag.models import RetrievedChunk, Citation, RAGContext, GuardrailResult, RAGAnswer
from ai.rag.retriever import RAGRetriever


def test_retrieved_chunk_model_validation():
    chunk = RetrievedChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="8.1.1",
        pages=[9],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2012-08-01",
        score=0.032,
        text="Insulation resistance shall not be less than 4 MΩ.",
        content_hash="abc123hash",
        provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
    )
    assert chunk.document_id == "DOC-001"
    assert chunk.pages == [9]
    assert chunk.normative_force == "mandatory"


def test_rag_retriever_returns_validated_chunks():
    retriever = RAGRetriever()
    chunks = retriever.retrieve("What is the minimum insulation resistance?", top_k=3)
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, RetrievedChunk)
        assert chunk.document_id.startswith("DOC-")
        assert chunk.source_id.startswith("SRC-")
        assert len(chunk.content_hash) > 0
        assert chunk.score > 0.0
