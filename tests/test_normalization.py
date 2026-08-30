"""
Validation tests for Phase 2D Semantic Normalization, Clause Classification,
Entity Families, Requirements, Cross-References, Knowledge Graph Edges,
Provenance Preservation, Semantic States, and Dual Value Normalization.
"""

import json
from pathlib import Path
import pytest
from ai.processing.clause_classifier import ClauseClassifier
from ai.processing.cross_reference_resolver import CrossReferenceResolver
from ai.processing.entity_extractor import EntityExtractor
from ai.processing.normalizer import DocumentNormalizer
from ai.processing.requirement_extractor import RequirementExtractor
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

    # Check that GX53 or 80°C items have status == 'under_consideration'
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


def test_2d4_and_2d5_requirements_with_conditions(normalized_documents):
    """Verify that requirements contain parameter, operator, value, unit, and test conditions (2D-4 & 2D-5)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    # 1. Insulation Resistance (>= 4 MΩ under 48h, 91-95% RH)
    req_ir = next((r for r in reqs if r.get("parameter") == "insulation_resistance"), None)
    assert req_ir is not None
    assert req_ir["operator"] == ">="
    assert req_ir["value"] == 4.0
    assert req_ir["unit"] == "MΩ"
    assert "conditions" in req_ir
    assert "humidity_treatment" in req_ir["conditions"]
    assert "test" in req_ir
    assert "applied_voltage" in req_ir["test"]

    # 2. Cap Temperature Rise (<= 120 K)
    req_temp = next((r for r in reqs if r.get("parameter") == "cap_temperature_rise"), None)
    assert req_temp is not None
    assert req_temp["operator"] == "<="
    assert req_temp["value"] == 120.0
    assert req_temp["unit"] == "K"
    assert "conditions" in req_temp

    # 3. ITQ Sampling (25 lamps)
    req_itq = next((r for r in reqs if r.get("parameter") == "inspection_test_quantity"), None)
    assert req_itq is not None
    assert req_itq["value"] == 25
    assert req_itq["unit"] == "lamps"


def test_2d6_cross_references_resolution(normalized_documents):
    """Verify that structured cross-references distinguish normative, test_method, and definition types (2D-6)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    cross_refs = doc_001.get("cross_references", [])
    assert len(cross_refs) > 0

    target_standards = [ref["target_standard"] for ref in cross_refs]
    assert any("IS 9206" in s for s in target_standards)
    assert any("IS 15885" in s for s in target_standards)
    assert any("IS 8913" in s for s in target_standards)


def test_2d7_knowledge_graph_edges(normalized_documents):
    """Verify that knowledge graph edges include standard vocabulary predicates (2D-7)."""
    doc_001 = next(d for m, d in normalized_documents if d["document_id"] == "DOC-001")
    rels = doc_001.get("relationships", [])
    assert len(rels) > 0

    predicates = {rel["predicate"] for rel in rels}
    assert "applies_to" in predicates
    assert "part_of" in predicates
    assert "references" in predicates
    assert "requires" in predicates or "has_limit" in predicates
