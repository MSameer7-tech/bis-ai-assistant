"""
Validation tests for Phase 2D Semantic Schema and Semantic IDs.
"""

import json
from pathlib import Path
import pytest
from ai.processing.schema import (
    make_clause_id,
    make_parameter_id,
    make_requirement_id,
    make_section_id,
    make_standard_id,
    make_table_id,
    make_term_id,
    make_test_id,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"


def test_semantic_id_generators():
    """Verify semantic ID formats conform strictly to 2D-13 specifications."""
    assert make_section_id("DOC-001", "8") == "SEC-DOC001-08"
    assert make_clause_id("DOC-001", "8.1.1") == "CLAUSE-DOC001-8.1.1"
    assert make_requirement_id("DOC-001", "8.1.1", 1) == "REQ-DOC001-8.1.1-001"
    assert make_test_id("DOC-001", "8.1.1", 1) == "TEST-DOC001-8.1.1-001"
    assert make_parameter_id("insulation resistance") == "PARAM-insulation_resistance"
    assert make_standard_id("IS 15885 (Part 1)") == "STD-IS_15885_P1"
    assert make_term_id("Self-Ballasted LED Lamp") == "TERM-self_ballasted_led_lamp"
    assert make_table_id("DOC-001", "3") == "TABLE-DOC001-T03"


def test_normalized_json_contains_semantic_ids():
    """Verify that normalized DOC-001.json contains stable semantic IDs."""
    doc_path = NORMALIZED_DIR / "DOC-001.json"
    assert doc_path.exists(), f"Normalized DOC-001.json must exist at {doc_path}"

    with open(doc_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["document_metadata"]["standard_id"].startswith("STD-")
    assert any(s.get("section_id", "").startswith("SEC-DOC001-") for s in doc.get("semantic_sections", []))
    assert any(c.get("clause_id", "").startswith("CLAUSE-DOC001-") for c in doc.get("clauses", []))
    assert any(r.get("requirement_id", "").startswith("REQ-DOC001-") for r in doc.get("requirements", []))
    assert any(d.get("term_id", "").startswith("TERM-") for d in doc.get("definitions", []))
    assert any(t.get("semantic_table_id", "").startswith("TABLE-DOC001-") for t in doc.get("tables", []))
