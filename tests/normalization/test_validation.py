"""
Validation tests for Phase 2D Safety, Accuracy, and Under Consideration Guards.
"""

import json
from pathlib import Path
import pytest
from ai.processing.validator import SemanticValidator

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"
VERIFICATION_LOG_PATH = ROOT_DIR / "data" / "metadata" / "normalization_verification_log.json"


@pytest.fixture(scope="module")
def doc_001():
    assert DOC_001_PATH.exists()
    with open(DOC_001_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_semantic_validator_audits_doc_001(doc_001):
    validator = SemanticValidator()
    report = validator.validate_normalized_document(doc_001)

    assert report["is_valid"] is True
    assert report["checks"]["safety_under_consideration_guarded"] is True
    assert report["checks"]["requirements_structure_valid"] is True
    assert report["checks"]["provenance_binding_valid"] is True


def test_safety_under_consideration_not_mandatory(doc_001):
    reqs = doc_001.get("requirements", [])
    for r in reqs:
        if "under consideration" in r.get("original_value", "").lower() or "under consideration" in r.get("evidence", "").lower():
            assert r.get("status") == "under_consideration"
            assert r.get("status") != "mandatory"


def test_normalization_verification_log_is_semantic_verified():
    """Verify that normalization_verification_log.json contains a passed audit matrix for DOC-001."""
    assert VERIFICATION_LOG_PATH.exists(), f"Log missing: {VERIFICATION_LOG_PATH}"
    with open(VERIFICATION_LOG_PATH, "r", encoding="utf-8") as f:
        logs = json.load(f)

    entry = next((l for l in logs if l["document_id"] == "DOC-001"), None)
    assert entry is not None
    assert entry["status"] == "semantic_verified"
    assert entry["checks"]["metadata"] == "passed"
    assert entry["checks"]["requirements"] == "passed"
    assert entry["checks"]["tables"] == "passed"
    assert entry["checks"]["under_consideration"] == "passed"
    assert entry["checks"]["question_based_validation"] == "passed"
