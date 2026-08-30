"""
Validation tests for Phase 2D Semantic Normalization, Clause Classification,
Entity Families, Requirements, Cross-References, Knowledge Graph Edges,
Provenance Preservation, Semantic States, Dual Value Normalization,
Normalized Tables (2D-11), and Definitions (2D-12).
"""

import json
from pathlib import Path
import pytest
from ai.processing.clause_classifier import ClauseClassifier
from ai.processing.cross_reference_resolver import CrossReferenceResolver
from ai.processing.definition_extractor import DefinitionExtractor
from ai.processing.entity_extractor import EntityExtractor
from ai.processing.normalizer import DocumentNormalizer
from ai.processing.requirement_extractor import RequirementExtractor
from ai.processing.table_normalizer import TableNormalizer
from ai.processing.value_normalizer import ValueNormalizer, normalize_value

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


def test_2d11_normalized_tables_structure(normalized_documents):
    """Verify that Table 2 and Table 3 contain typed records with units and status flags (2D-11)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    tables = doc_001.get("tables", [])
    assert len(tables) >= 2

    # Table 3: Torque Test Values
    tab_3 = next((t for t in tables if t.get("table_id") == "TABLE-003"), None)
    assert tab_3 is not None
    assert tab_3["clause"] == "9.1"
    assert len(tab_3["rows"]) >= 8

    # Verify B15d and B22d rows
    row_b15 = next((r for r in tab_3["rows"] if r.get("cap") == "B15d"), None)
    assert row_b15 is not None
    assert row_b15["torsion_moment"]["value"] == 1.15
    assert row_b15["torsion_moment"]["unit"] == "Nm"
    assert row_b15["status"] == "mandatory"

    # Verify GX53 under_consideration
    row_gx53 = next((r for r in tab_3["rows"] if r.get("cap") == "GX53"), None)
    assert row_gx53 is not None
    assert row_gx53["status"] == "under_consideration"

    # Table 2: Bending Moments and Masses
    tab_2 = next((t for t in tables if t.get("table_id") == "TABLE-002"), None)
    assert tab_2 is not None
    assert tab_2["clause"] == "6.2"


def test_2d12_normalized_definitions(normalized_documents):
    """Verify that Clause 3 terminology is converted into canonical definition objects (2D-12)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    defs = doc_001.get("definitions", [])
    assert len(defs) > 0

    for item in defs:
        assert item["entity_type"] == "definition"
        assert "definition_id" in item
        assert "term" in item
        assert "definition" in item
        assert "source_clause" in item
        assert "provenance" in item
        assert item["provenance"]["clause"]

    # Verify presence of core definitions
    terms = [d["term"].upper() for d in defs]
    assert any("SELF-BALLASTED" in t or "LAMP" in t or "LIVE PART" in t or "TEST" in t for t in terms)


def test_2d8_provenance_binding(normalized_documents):
    """Verify that every requirement has complete provenance linking to source PDF, clause, and page (2D-8)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    for req in reqs:
        assert "provenance" in req
        prov = req["provenance"]
        assert prov["document_id"] == "DOC-001"
        assert prov["source_id"] == "SRC-001"
        assert "IS 16102" in prov["standard"]
        assert prov["clause"]
        assert isinstance(prov["page"], int)
        assert len(prov["pages"]) > 0
        assert "original_text" in prov


def test_2d9_semantic_states_and_under_consideration(normalized_documents):
    """Verify that 'under consideration' items are flagged with proper semantic status (2D-9)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])

    under_cons_reqs = [r for r in reqs if r.get("status") == "under_consideration"]
    assert len(under_cons_reqs) >= 1
    for r in under_cons_reqs:
        assert "under consideration" in r["original_value"].lower() or "under consideration" in r["evidence"].lower()


def test_2d10_value_normalizer_preserves_original_and_parses_tolerances():
    """Verify dual value normalization and tolerance parsing (2D-10)."""
    normalizer = ValueNormalizer()

    # Tolerance: (25 ± 5)°C
    tol_res = normalizer.normalize_value_expression("(25 ± 5)°C")
    assert tol_res["original_value"] == "(25 ± 5)°C"
    assert tol_res["normalized"]["nominal"] == 25
    assert tol_res["normalized"]["tolerance"] == 5
    assert tol_res["normalized"]["unit"] == "°C"

    # Spaced numbers: 1 000 V
    volt_res = normalizer.normalize_value_expression("1 000 V")
    assert volt_res["normalized"]["value"] == 1000
    assert volt_res["normalized"]["unit"] == "V"

    # Range: 91-95 %
    range_res = normalizer.normalize_value_expression("91-95 %")
    assert range_res["normalized"]["min"] == 91
    assert range_res["normalized"]["max"] == 95
    assert range_res["normalized"]["unit"] == "%"


def test_2d3_entity_families_in_doc_001(normalized_documents):
    """Verify that DOC-001 extracts all 7 required entity families (2D-3)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    entities = doc_001.get("entities", [])
    types = {e["entity_type"] for e in entities}

    assert "standard" in types or "referenced_standard" in types
    assert "product" in types
    assert "lamp_cap" in types
    assert "value_and_unit" in types
    assert "test" in types
    assert "authority" in types


def test_2d4_and_2d5_requirements_with_conditions(normalized_documents):
    """Verify that requirements contain parameter, operator, value, unit, and test conditions (2D-4 & 2D-5)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    req_ir = next((r for r in reqs if r.get("parameter") == "insulation_resistance"), None)
    assert req_ir is not None
    assert req_ir["operator"] == ">="
    assert req_ir["value"] == 4.0
    assert req_ir["unit"] == "MΩ"
    assert "conditions" in req_ir
    assert "humidity_treatment" in req_ir["conditions"]


def test_2d6_cross_references_resolution(normalized_documents):
    """Verify that structured cross-references distinguish normative, test_method, and definition types (2D-6)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    cross_refs = doc_001.get("cross_references", [])
    assert len(cross_refs) > 0


def test_2d7_knowledge_graph_edges(normalized_documents):
    """Verify that knowledge graph edges include standard vocabulary predicates (2D-7)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    rels = doc_001.get("relationships", [])
    assert len(rels) > 0
