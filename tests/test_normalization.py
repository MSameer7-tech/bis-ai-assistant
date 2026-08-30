"""
Validation tests for Phase 2D Semantic Normalization and Knowledge Entity Extraction.
Verifies entity extraction, machine-readable requirements, semantic relationships,
table normalization, and cryptographic provenance preservation.
"""

import json
from pathlib import Path
import pytest
from ai.processing.normalizer import DocumentNormalizer

ROOT_DIR = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"


@pytest.fixture(scope="module")
def normalized_documents():
    """Loads all normalized document JSON artifacts."""
    assert DOCUMENTS_PATH.exists(), "documents.json must exist"
    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        doc_manifests = json.load(f)

    docs = []
    for manifest in doc_manifests:
        doc_id = manifest["document_id"]
        norm_path = NORMALIZED_DIR / f"{doc_id}.normalized.json"
        assert norm_path.exists(), f"Normalized JSON missing for {doc_id}: {norm_path}"
        with open(norm_path, "r", encoding="utf-8") as f:
            docs.append((manifest, json.load(f)))
    return docs


def test_normalized_documents_exist_for_all_acquired(normalized_documents):
    """Verify that all 6 pilot documents have been normalized into data/normalized/."""
    assert len(normalized_documents) == 6


def test_provenance_and_sha256_preserved(normalized_documents):
    """Verify that SHA-256 and source lineage are retained in normalized documents."""
    for manifest, doc in normalized_documents:
        assert doc["document_id"] == manifest["document_id"]
        assert doc["source_id"] == manifest["source_id"]
        assert doc["document_metadata"]["sha256"] == manifest["file_sha256"]
        assert doc["provenance"]["sha256"] == manifest["file_sha256"]
        assert len(doc["provenance"]["sha256"]) == 64


def test_entities_contain_provenance(normalized_documents):
    """Verify that extracted entities have valid types and source page provenance."""
    for manifest, doc in normalized_documents:
        for ent in doc.get("entities", []):
            assert "entity_id" in ent
            assert "entity_type" in ent
            assert "name" in ent
            assert "source_clause" in ent
            assert "source_pages" in ent
            assert isinstance(ent["source_pages"], list)
            assert len(ent["source_pages"]) > 0


def test_requirements_contain_typed_properties(normalized_documents):
    """Verify that requirement statements have operators, properties, and conditions."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    for req in reqs:
        assert "requirement_id" in req
        assert "clause" in req
        assert "subject" in req
        assert "property" in req
        assert "operator" in req
        assert "source_pages" in req
        assert isinstance(req["source_pages"], list)


def test_relationships_are_valid_triples(normalized_documents):
    """Verify that relationships form valid subject-predicate-object triples with provenance."""
    for manifest, doc in normalized_documents:
        for rel in doc.get("relationships", []):
            assert "subject" in rel
            assert "predicate" in rel
            assert "object" in rel
            assert "source_pages" in rel
            assert isinstance(rel["source_pages"], list)


def test_tables_are_typed_and_normalized(normalized_documents):
    """Verify that tables are normalized into structured dictionaries with column keys."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    tables = doc_001.get("tables", [])
    assert len(tables) > 0

    for tab in tables:
        assert "table_id" in tab
        assert "title" in tab
        assert "headers" in tab
        assert "normalized_headers" in tab
        assert "rows" in tab
        if tab["rows"]:
            assert isinstance(tab["rows"][0], dict)
