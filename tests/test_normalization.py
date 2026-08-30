"""
Validation tests for Phase 2D Semantic Normalization, Clause Classification, and Entity Extraction.
"""

import json
from pathlib import Path
import pytest
from ai.processing.clause_classifier import ClauseClassifier
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


def test_clause_classifier_roles():
    """Verify that ClauseClassifier accurately maps clauses to semantic types."""
    classifier = ClauseClassifier()

    c_scope = {"clause_number": "1", "title": "SCOPE", "content": "This standard applies to LED lamps."}
    assert classifier.classify_clause(c_scope)["primary_type"] == "scope"

    c_mark = {"clause_number": "5.1", "title": "Marking", "content": "Lamps shall be marked with wattage."}
    assert classifier.classify_clause(c_mark)["primary_type"] == "marking_requirement"

    c_test = {"clause_number": "8.1.1", "title": "Insulation Resistance", "content": "The lamp shall be conditioned for 48 h. Resistance shall not be less than 4 MΩ."}
    res_test = classifier.classify_clause(c_test)
    assert "acceptance_criterion" in res_test["semantic_tags"] or "test_method" in res_test["semantic_tags"]


def test_requirements_conform_to_2d1_schema(normalized_documents):
    """Verify that requirement statements adhere strictly to the 2D-1 schema."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    req_insulation = next((r for r in reqs if r["requirement"] == "insulation resistance"), None)
    assert req_insulation is not None
    assert req_insulation["entity_type"] == "requirement"
    assert "conditions" in req_insulation
    assert "duration" in req_insulation["conditions"]
    assert "test" in req_insulation
    assert "voltage" in req_insulation["test"]
    assert "acceptance_criterion" in req_insulation
    assert req_insulation["acceptance_criterion"]["minimum"] == 4.0
    assert req_insulation["acceptance_criterion"]["unit"] == "MΩ"


def test_clauses_contain_semantic_classification(normalized_documents):
    """Verify that every clause in normalized JSON contains semantic_type and semantic_tags."""
    for manifest, doc in normalized_documents:
        for c in doc.get("clauses", []):
            assert "semantic_type" in c
            assert "semantic_tags" in c
            assert isinstance(c["semantic_tags"], list)
            assert len(c["semantic_tags"]) > 0
