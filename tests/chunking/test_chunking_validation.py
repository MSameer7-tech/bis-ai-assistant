"""
Comprehensive Automated Validation Test Suite for Phase 2E Chunking (Step 14 & 16).
Validates all 15 critical requirements and audit log conformance:
1. Every important clause represented
2. Every requirement represented
3. Every definition represented
4. Every table represented
5. Every annex represented
6. No requirement lost
7. No requirement duplicated accidentally
8. Page references preserved
9. Clause hierarchy preserved
10. References preserved
11. Units preserved
12. Numeric operators preserved
13. Normative language preserved
14. Under-consideration status preserved
15. Provenance exists on every chunk
16. Chunking verification log status
"""

import json
from pathlib import Path
import pytest
from ai.chunking.schema import ChunkType, KnowledgeChunk, NormativeForce

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DOC_001_CHUNKS_PATH = CHUNKS_DIR / "DOC-001.json"
DOC_001_NORM_PATH = NORMALIZED_DIR / "DOC-001.json"
VERIFICATION_LOG_PATH = ROOT_DIR / "data" / "metadata" / "chunking_verification_log.json"


@pytest.fixture(scope="module")
def doc_001_data():
    assert DOC_001_CHUNKS_PATH.exists(), f"Chunks file missing: {DOC_001_CHUNKS_PATH}"
    assert DOC_001_NORM_PATH.exists(), f"Normalized file missing: {DOC_001_NORM_PATH}"

    with open(DOC_001_CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(DOC_001_NORM_PATH, "r", encoding="utf-8") as f:
        norm_doc = json.load(f)

    return chunks, norm_doc


def test_1_every_important_clause_represented(doc_001_data):
    chunks, norm_doc = doc_001_data
    clauses_in_chunks = {c["clause"]["number"] for c in chunks}

    important_clauses = ["1", "2", "3.1", "5", "6", "8.1.1", "9.1", "10", "11", "12", "13", "15", "16", "17"]
    for c_num in important_clauses:
        assert any(c_num in num for num in clauses_in_chunks), f"Important clause {c_num} missing from chunks!"


def test_2_every_requirement_represented(doc_001_data):
    chunks, norm_doc = doc_001_data
    norm_req_ids = {r["requirement_id"] for r in norm_doc.get("requirements", [])}
    chunk_req_ids = {r["requirement_id"] for c in chunks for r in c.get("requirements", [])}

    assert len(norm_req_ids) > 0
    assert norm_req_ids.issubset(chunk_req_ids), f"Missing requirements: {norm_req_ids - chunk_req_ids}"


def test_3_every_definition_represented(doc_001_data):
    chunks, norm_doc = doc_001_data
    def_chunks = [c for c in chunks if c["chunk_type"] == ChunkType.DEFINITION.value]
    norm_defs = norm_doc.get("definitions", [])

    assert len(def_chunks) == len(norm_defs)
    chunk_terms = {c.get("term", "").upper() for c in def_chunks}
    for d in norm_defs:
        assert d["term"].upper() in chunk_terms


def test_4_every_table_represented(doc_001_data):
    chunks, norm_doc = doc_001_data
    tab_chunks = [c for c in chunks if c["chunk_type"] == ChunkType.TABLE.value]
    assert len(tab_chunks) >= len(norm_doc.get("tables", []))

    tab_numbers = {c.get("table_number") for c in tab_chunks}
    assert "2" in tab_numbers
    assert "3" in tab_numbers


def test_5_every_annex_represented(doc_001_data):
    chunks, norm_doc = doc_001_data
    annex_chunks = [c for c in chunks if c["chunk_type"] == ChunkType.ANNEX.value]
    assert len(annex_chunks) >= len(norm_doc.get("annexes", []))


def test_6_no_requirement_lost(doc_001_data):
    chunks, norm_doc = doc_001_data
    norm_req_ids = {r["requirement_id"] for r in norm_doc.get("requirements", [])}
    chunk_req_ids = {r["requirement_id"] for c in chunks for r in c.get("requirements", [])}
    assert norm_req_ids == chunk_req_ids


def test_7_no_requirement_duplicated_accidentally(doc_001_data):
    chunks, norm_doc = doc_001_data
    all_chunk_req_ids = [r["requirement_id"] for c in chunks for r in c.get("requirements", [])]
    assert len(all_chunk_req_ids) == len(set(all_chunk_req_ids)), "Duplicate requirement IDs detected across chunks!"


def test_8_page_references_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    for c in chunks:
        assert len(c["page_refs"]) > 0
        assert all(isinstance(p, int) and p >= 1 for p in c["page_refs"])


def test_9_clause_hierarchy_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    ir_chunk = next(c for c in chunks if c["clause"]["number"] == "8.1.1")
    assert ir_chunk["clause"]["hierarchy_path"] == ["8", "8.1", "8.1.1"]
    assert ir_chunk["clause"]["depth"] == 3
    assert ir_chunk["clause"]["parent_clause"] == "8.1"


def test_10_references_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    ir_chunk = next(c for c in chunks if c["clause"]["number"] == "8.1.1")
    assert len(ir_chunk["references"]) > 0
    assert any("15885" in r["standard"] for r in ir_chunk["references"])


def test_11_units_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    ir_chunk = next(c for c in chunks if c["clause"]["number"] == "8.1.1")
    assert ir_chunk["requirements"][0]["unit"] == "MΩ"


def test_12_numeric_operators_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    ir_chunk = next(c for c in chunks if c["clause"]["number"] == "8.1.1")
    assert ir_chunk["requirements"][0]["operator"] == ">="
    assert ir_chunk["requirements"][0]["value"] == 4.0


def test_13_normative_language_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    ir_chunk = next(c for c in chunks if c["clause"]["number"] == "8.1.1")
    assert "shall" in ir_chunk["normative_context"]["modal_keywords"]
    assert ir_chunk["normative_context"]["normative_force"] == NormativeForce.MANDATORY.value


def test_14_under_consideration_status_preserved(doc_001_data):
    chunks, norm_doc = doc_001_data
    t3_chunk = next(c for c in chunks if c.get("table_number") == "3")
    row_gx53 = next(r for r in t3_chunk["rows"] if r["cap"] == "GX53")
    assert row_gx53["status"] == "under_consideration"
    assert row_gx53["torsion_moment"] == 3.0


def test_15_provenance_exists_on_every_chunk(doc_001_data):
    chunks, norm_doc = doc_001_data
    for c in chunks:
        prov = c.get("provenance")
        assert prov is not None
        assert prov["document_id"] == "DOC-001"
        assert prov["source_id"] == "SRC-001"
        assert prov["clause"]
        assert len(prov["pages"]) > 0


def test_16_chunking_verification_log_status():
    """Verify that chunking_verification_log.json is populated with chunking_verified status and Step 16 checks."""
    assert VERIFICATION_LOG_PATH.exists(), f"Log missing: {VERIFICATION_LOG_PATH}"
    with open(VERIFICATION_LOG_PATH, "r", encoding="utf-8") as f:
        logs = json.load(f)
    entry = next((l for l in logs if l["document_id"] == "DOC-001"), None)
    assert entry is not None
    assert entry["status"] == "chunking_verified"
    checks = entry["checks"]
    assert checks["clause_coverage"] == "passed"
    assert checks["requirement_coverage"] == "passed"
    assert checks["definition_coverage"] == "passed"
    assert checks["table_preservation"] == "passed"
    assert checks["annex_preservation"] == "passed"
    assert checks["provenance"] == "passed"
    assert checks["normative_language"] == "passed"
    assert checks["under_consideration"] == "passed"
    assert checks["cross_references"] == "passed"
