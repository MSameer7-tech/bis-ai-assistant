"""
Validation tests for Phase 2E Structure-Aware Semantic Chunking.
"""

import json
from pathlib import Path
import pytest
from ai.chunking.chunker import StructureAwareChunker
from ai.chunking.schema import ChunkType, KnowledgeChunk, NormativeForce

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


def test_step4_boundary_rules_atomic_units(chunked_documents):
    """Verify that requirements and conditions remain atomic and are not fragmented (Step 4)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    ir_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert ir_chunk is not None

    # Condition & Test are bundled together with requirement
    assert len(ir_chunk["conditions"]) > 0
    assert "humidity_treatment" in ir_chunk["conditions"][0]
    assert "48 h" in ir_chunk["text"]
    assert "91" in ir_chunk["text"] and "95" in ir_chunk["text"]


def test_step5_hierarchy_preservation(chunked_documents):
    """Verify that clause hierarchy lineage (path, parent, depth) is preserved (Step 5)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    ir_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert ir_chunk is not None

    c_meta = ir_chunk["clause"]
    assert c_meta["number"] == "8.1.1"
    assert c_meta["parent_clause"] == "8.1"
    assert c_meta["hierarchy_path"] == ["8", "8.1", "8.1.1"]
    assert c_meta["depth"] == 3


def test_step6_normative_meaning_and_modals_preservation(chunked_documents):
    """Verify that modal auxiliary verbs and normative force are preserved (Step 6)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    ir_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert ir_chunk is not None

    norm = ir_chunk["normative_context"]
    assert "shall" in norm["modal_keywords"]
    assert norm["normative_force"] == NormativeForce.MANDATORY.value
    assert any("shall be not less than" in s.lower() or "shall be conditioned" in s.lower() for s in norm["verbatim_normative_statements"])


def test_table_chunks_contain_structured_data(chunked_documents):
    """Verify that table chunks contain structured row records and units."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    table_chunks = [c for c in doc_001 if c["chunk_type"] == ChunkType.TABLE.value]
    assert len(table_chunks) >= 2

    t3_chunk = next(c for c in table_chunks if "Torque" in c["clause"]["title"] or "TABLE-003" in str(c["metadata"]))
    assert t3_chunk["table_data"] is not None
    assert len(t3_chunk["table_data"]["rows"]) >= 8
