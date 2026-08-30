"""
Validation tests for Phase 2E Structure-Aware Semantic Chunking.
"""

import json
from pathlib import Path
import pytest
from ai.chunking.chunker import StructureAwareChunker
from ai.chunking.schema import ChunkType, KnowledgeChunk

ROOT_DIR = Path(__file__).resolve().parent.parent
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"


@pytest.fixture(scope="module")
def chunked_documents():
    """Loads all chunked document JSON artifacts."""
    assert DOCUMENTS_PATH.exists(), "documents.json must exist"
    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        doc_manifests = json.load(f)

    docs = []
    for manifest in doc_manifests:
        doc_id = manifest["document_id"]
        chunk_path = CHUNKS_DIR / f"{doc_id}.chunks.json"
        assert chunk_path.exists(), f"Chunks file missing for {doc_id}: {chunk_path}"
        with open(chunk_path, "r", encoding="utf-8") as f:
            docs.append((manifest, json.load(f)))
    return docs


def test_chunks_exist_for_all_6_documents(chunked_documents):
    """Verify that all 6 acquired documents have been chunked."""
    assert len(chunked_documents) == 6


def test_chunk_schema_conformance(chunked_documents):
    """Verify that every chunk conforms to the KnowledgeChunk Pydantic model."""
    for manifest, chunks in chunked_documents:
        assert len(chunks) > 0, f"Empty chunks in {manifest['document_id']}"
        for c in chunks:
            # Validate via Pydantic
            validated = KnowledgeChunk.model_validate(c)
            assert validated.chunk_id.startswith(manifest["document_id"])
            assert validated.document_id == manifest["document_id"]
            assert validated.source_id == manifest["source_id"]
            assert len(validated.page_refs) > 0
            assert validated.provenance.pages == validated.page_refs


def test_chunk_types_distribution_doc001(chunked_documents):
    """Verify that DOC-001 has definitions, tables, requirements, sampling, and annex chunks."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    types = {c["chunk_type"] for c in doc_001}

    assert ChunkType.SCOPE.value in types
    assert ChunkType.DEFINITION.value in types
    assert ChunkType.REQUIREMENT.value in types
    assert ChunkType.TABLE.value in types
    assert ChunkType.SAMPLING.value in types
    assert ChunkType.ANNEX.value in types


def test_requirement_chunk_contains_context_and_limits(chunked_documents):
    """Verify that requirement chunks contain embedded requirements, conditions, and references."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    req_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert req_chunk is not None

    assert req_chunk["chunk_type"] == ChunkType.REQUIREMENT.value
    assert len(req_chunk["requirements"]) > 0
    assert len(req_chunk["conditions"]) > 0
    assert req_chunk["page_refs"] == [9]

    # Verify embedded requirement data
    req_item = req_chunk["requirements"][0]
    assert req_item["parameter"] == "insulation_resistance"
    assert req_item["operator"] == ">="
    assert req_item["value"] == 4.0
    assert req_item["unit"] == "MΩ"


def test_table_chunks_contain_structured_data(chunked_documents):
    """Verify that table chunks contain structured row records and units."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    table_chunks = [c for c in doc_001 if c["chunk_type"] == ChunkType.TABLE.value]
    assert len(table_chunks) >= 2

    t3_chunk = next(c for c in table_chunks if "Torque" in c["clause"]["title"] or "TABLE-003" in str(c["metadata"]))
    assert t3_chunk["table_data"] is not None
    assert len(t3_chunk["table_data"]["rows"]) >= 8
