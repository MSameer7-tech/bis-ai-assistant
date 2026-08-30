"""
Validation tests for Phase 2D Cross-References.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"


@pytest.fixture(scope="module")
def doc_001():
    assert DOC_001_PATH.exists()
    with open(DOC_001_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_referenced_standards_detected(doc_001):
    refs = doc_001.get("cross_references", [])
    assert len(refs) > 0

    target_stds = [r["target_standard"] for r in refs]
    assert any("IS 9206" in s for s in target_stds)
    assert any("IS 15885" in s for s in target_stds)
    assert any("IS 8913" in s for s in target_stds)


def test_reference_types_classified(doc_001):
    refs = doc_001.get("cross_references", [])
    types = {r["reference_type"] for r in refs}
    assert "normative" in types or "test_method" in types or "definition" in types
