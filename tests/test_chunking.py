"""
Validation tests for Phase 2E Structure-Aware Semantic Chunking (Step 7 Stable IDs & Hashes).
"""

import json
from pathlib import Path
import pytest
from ai.chunking.chunker import StructureAwareChunker
from ai.chunking.schema import ChunkType, KnowledgeChunk, NormativeForce
from ai.chunking.validators import ChunkValidator

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
        chunk_path = CHUNKS_DIR / f"{doc_id}.json"
        if not chunk_path.exists():
            chunk_path = CHUNKS_DIR / f"{doc_id}.chunks.json"
        assert chunk_path.exists(), f"Chunks file missing for {doc_id}: {chunk_path}"
        with open(chunk_path, "r", encoding="utf-8") as f:
            docs.append((manifest, json.load(f)))
    return docs


def test_chunks_exist_for_all_6_documents(chunked_documents):
    """Verify that all 6 acquired documents have been chunked."""
    assert len(chunked_documents) == 6


def test_chunk_schema_conformance(chunked_documents):
    """Verify that every chunk conforms to the KnowledgeChunk Pydantic model with stable IDs and content hashes."""
    for manifest, chunks in chunked_documents:
        assert len(chunks) > 0, f"Empty chunks in {manifest['document_id']}"
        for c in chunks:
            # Validate via Pydantic
            validated = KnowledgeChunk.model_validate(c)
            assert manifest["document_id"] in validated.chunk_id
            assert "::" in validated.chunk_id
            assert validated.document_id == manifest["document_id"]
            assert validated.source_id == manifest["source_id"]
            assert len(validated.page_refs) > 0
            assert validated.provenance.pages == validated.page_refs
            assert validated.content_hash is not None and len(validated.content_hash) == 64


def test_step4_boundary_rules_atomic_units(chunked_documents):
    """Verify that requirements and conditions remain atomic and are not fragmented (Step 4)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    ir_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert ir_chunk is not None

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


def test_step7_table_chunks_structured_and_text(chunked_documents):
    """Verify that table chunks contain structured rows and textual representation (Step 7)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    table_chunks = [c for c in doc_001 if c["chunk_type"] == ChunkType.TABLE.value]
    assert len(table_chunks) >= 2

    t3_chunk = next(c for c in table_chunks if c.get("table_number") == "3")
    assert t3_chunk is not None
    assert t3_chunk["clause"]["number"] == "9.1"
    assert "Torque" in t3_chunk["clause"]["title"] or "Torque" in (t3_chunk.get("title") or "")
    assert len(t3_chunk["rows"]) >= 8

    # Verify B15d and E17 rows
    b15 = next(r for r in t3_chunk["rows"] if r["cap"] == "B15d")
    assert b15["torsion_moment"] == 1.15
    assert b15["unit"] == "Nm"

    e17 = next(r for r in t3_chunk["rows"] if r["cap"] == "E17")
    assert e17["torsion_moment"] == 1.5
    assert e17["unit"] == "Nm"

    # Verify GX53 under_consideration
    gx53 = next(r for r in t3_chunk["rows"] if r["cap"] == "GX53")
    assert gx53["torsion_moment"] == 3.0
    assert gx53["status"] == "under_consideration"

    # Verify markdown text presence
    assert "| B15d |" in t3_chunk["text"]
    assert "| E17 |" in t3_chunk["text"]
    assert "| GX53 |" in t3_chunk["text"]


def test_step8_definition_chunks_isolated(chunked_documents):
    """Verify that domain definitions are isolated as discrete searchable chunks (Step 8)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    def_chunks = [c for c in doc_001 if c["chunk_type"] == ChunkType.DEFINITION.value]
    assert len(def_chunks) >= 8

    led_def = next((c for c in def_chunks if "SELF-BALLASTED" in c.get("term", "").upper()), None)
    assert led_def is not None
    assert led_def["clause"]["number"] == "3.1"
    assert "dismantled without being permanently damaged" in led_def["definition"].lower()
    assert "Self-Ballasted LED Lamp" in led_def["text"]


def test_step9_cross_references_preservation(chunked_documents):
    """Verify that cross-standard references and relationships are preserved (Step 9)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")
    ir_chunk = next((c for c in doc_001 if c["clause"]["number"] == "8.1.1"), None)
    assert ir_chunk is not None

    refs = ir_chunk["references"]
    assert len(refs) > 0
    ref_15885 = next((r for r in refs if "15885" in r["standard"]), None)
    assert ref_15885 is not None
    assert ref_15885["relationship"] == "test_method_applies" or ref_15885["relationship"] == "requirements_apply"


def test_step10_under_consideration_preservation(chunked_documents):
    """Verify that under_consideration status is preserved across table and clause chunks (Step 10)."""
    doc_001 = next(chunks for m, chunks in chunked_documents if m["document_id"] == "DOC-001")

    # Table 3 GX53
    t3 = next(c for c in doc_001 if c.get("table_number") == "3")
    r_gx53 = next(r for r in t3["rows"] if r["cap"] == "GX53")
    assert r_gx53["status"] == "under_consideration"

    # Clause 11 pending 80C
    c11 = next((c for c in doc_001 if c["clause"]["number"] == "11"), None)
    if c11 and c11.get("requirements"):
        req_80c = next((r for r in c11["requirements"] if "80" in str(r.get("original_value", ""))), None)
        if req_80c:
            assert req_80c["status"] == "under_consideration"


def test_step11_provenance_on_every_chunk(chunked_documents):
    """Verify that every single chunk carries full provenance linking to document, clause, page (Step 11)."""
    for manifest, chunks in chunked_documents:
        for c in chunks:
            assert "provenance" in c
            prov = c["provenance"]
            assert prov["document_id"] == manifest["document_id"]
            assert prov["source_id"] == manifest["source_id"]
            assert prov["clause"]
            assert len(prov["pages"]) > 0
            assert all(isinstance(p, int) for p in prov["pages"])


def test_step12_chunk_validator_audits_all_documents(chunked_documents):
    """Verify that ChunkValidator audits all 6 chunk files with zero errors (Step 12)."""
    validator = ChunkValidator()
    for manifest, chunks in chunked_documents:
        report = validator.validate_chunks(chunks)
        assert report["is_valid"] is True, f"Validation failed for {manifest['document_id']}: {report['errors']}"
        assert report["total_chunks"] > 0
