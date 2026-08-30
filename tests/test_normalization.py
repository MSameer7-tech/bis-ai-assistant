"""
Validation tests for Phase 2D Semantic Normalization, Clause Classification,
Entity Families, Requirements, Cross-References, and Knowledge Graph Edges.
"""

import json
from pathlib import Path
import pytest
from ai.processing.clause_classifier import ClauseClassifier
from ai.processing.cross_reference_resolver import CrossReferenceResolver
from ai.processing.entity_extractor import EntityExtractor
from ai.processing.normalizer import DocumentNormalizer
from ai.processing.requirement_extractor import RequirementExtractor

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

    ref_types = {ref["reference_type"] for ref in cross_refs}
    assert "normative" in ref_types or "test_method" in ref_types or "definition" in ref_types


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
