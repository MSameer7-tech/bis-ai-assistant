"""
Validation tests for Phase 2D Provenance Binding.
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


def test_every_entity_and_requirement_has_provenance(doc_001):
    entities = doc_001.get("entities", [])
    for ent in entities:
        assert "provenance" in ent
        prov = ent["provenance"]
        assert prov["document_id"] == "DOC-001"
        assert prov["source_id"] == "SRC-001"
        assert prov["clause"]
        assert isinstance(prov["page"], int)

    reqs = doc_001.get("requirements", [])
    for req in reqs:
        assert "provenance" in req
        prov = req["provenance"]
        assert prov["document_id"] == "DOC-001"
        assert prov["source_id"] == "SRC-001"
        assert "IS 16102" in prov["standard"]
        assert prov["clause"]
        assert isinstance(prov["page"], int)
        assert "original_text" in prov
