"""
Validation tests for Phase 2D Entity Extraction across 7 core domain families.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"


@pytest.fixture(scope="module")
def doc_001():
    assert DOC_001_PATH.exists(), f"DOC-001.json missing: {DOC_001_PATH}"
    with open(DOC_001_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_definitions_extracted(doc_001):
    defs = doc_001.get("definitions", [])
    assert len(defs) > 0
    terms = [d["term"].upper() for d in defs]
    assert any("SELF-BALLASTED" in t for t in terms)
    assert any("LIVE PART" in t for t in terms)
    assert any("TYPE TEST" in t for t in terms)


def test_all_7_entity_families_extracted(doc_001):
    entities = doc_001.get("entities", [])
    types = {e["entity_type"] for e in entities}

    # Family A: Standards
    assert "standard" in types or "referenced_standard" in types
    # Family B: Products & Components
    assert "product" in types
    assert "lamp_cap" in types
    # Family C & D: Parameters, Values & Units
    assert "value_and_unit" in types
    # Family F: Tests
    assert "test" in types
    # Family G: Authorities
    assert "authority" in types


def test_lamp_caps_extracted(doc_001):
    entities = doc_001.get("entities", [])
    caps = [e["name"].upper() for e in entities if e["entity_type"] == "lamp_cap"]
    assert "B15D" in caps or "B22D" in caps or "E27" in caps
