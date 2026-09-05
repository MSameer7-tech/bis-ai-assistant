"""
Automated Requirements Verification Suite for Phase 1.
Validates the engineering requirements derived from the SIH Problem Statement,
including their traceability, knowledge-domain coverage, query-intent coverage,
and Phase 1 scope boundaries.
"""
import json
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REQ_JSON_PATH = ROOT_DIR / "data" / "requirements" / "sih_requirements.json"
DK_JSON_PATH = ROOT_DIR / "data" / "requirements" / "bis_domain_knowledge_specs.json"
KD_JSON_PATH = ROOT_DIR / "data" / "requirements" / "bis_knowledge_domains.json"
INTENTS_JSON_PATH = ROOT_DIR / "data" / "requirements" / "query_intents.json"
DOCS_DIR = ROOT_DIR / "docs" / "phase1"


@pytest.fixture(scope="module")
def requirements_data():
    assert REQ_JSON_PATH.exists(), f"Missing requirements file: {REQ_JSON_PATH}"
    with open(REQ_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def domain_knowledge_data():
    assert DK_JSON_PATH.exists(), f"Missing domain knowledge file: {DK_JSON_PATH}"
    with open(DK_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def knowledge_domains_data():
    assert KD_JSON_PATH.exists(), f"Missing knowledge domains file: {KD_JSON_PATH}"
    with open(KD_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def query_intents_data():
    assert INTENTS_JSON_PATH.exists(), f"Missing query intents file: {INTENTS_JSON_PATH}"
    with open(INTENTS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_10_ps_requirements_exist(requirements_data):
    """Verifies that the Phase 1 engineering requirements derived from the PS
    are defined with MUST priority and have traceability/evaluation metadata."""
    reqs = requirements_data.get("requirements", [])
    assert len(reqs) == 10, f"Expected 10 derived requirements, found {len(reqs)}"

    expected_ids = {f"RQ-{i:03d}" for i in range(1, 11)}
    found_ids = {r["id"] for r in reqs}
    assert found_ids == expected_ids, f"Missing requirements: {expected_ids - found_ids}"

    for r in reqs:
        assert r["priority"] == "MUST", f"Requirement {r['id']} must have priority 'MUST'"
        assert r["source_basis"] in {"PS_EXPLICIT", "ENGINEERING_DERIVED"}, f"Requirement {r['id']} invalid source_basis"
        assert len(r["system_components"]) > 0, f"Requirement {r['id']} missing system components"
        assert len(r["evaluation_methods"]) > 0, f"Requirement {r['id']} missing evaluation methods"
        assert len(r["description"]) > 20, f"Requirement {r['id']} has insufficient description"
        assert "engineering_interpretation" in r, f"Requirement {r['id']} missing engineering_interpretation"


def test_requirements_classification_and_basis(requirements_data, domain_knowledge_data):
    """Verifies separation between PS-explicit capabilities and dynamic domain knowledge specifications."""
    reqs = requirements_data.get("requirements", [])
    for r in reqs:
        assert r["source_basis"] == "PS_EXPLICIT", f"Core capability {r['id']} should be marked PS_EXPLICIT"

    elements = domain_knowledge_data.get("domain_elements", [])
    assert len(elements) >= 8, f"Expected at least 8 domain knowledge specifications, found {len(elements)}"
    for elem in elements:
        assert "element_id" in elem
        assert "concept" in elem
        assert "authoritative_source_family" in elem
        assert "satisfies_capability" in elem


def test_knowledge_domains_complete_mapping(knowledge_domains_data, requirements_data):
    """Verifies that engineering knowledge domains KD-001 through KD-006 cover the required requirements."""
    domains = knowledge_domains_data.get("domains", [])
    assert len(domains) >= 6, f"Expected at least 6 knowledge domains, found {len(domains)}"

    expected_kd_ids = {f"KD-{i:03d}" for i in range(1, 7)}
    found_kd_ids = {d["id"] for d in domains}
    assert expected_kd_ids.issubset(found_kd_ids), f"Missing knowledge domains: {expected_kd_ids - found_kd_ids}"

    all_req_ids = {r["id"] for r in requirements_data.get("requirements", [])}
    covered_reqs = set()
    for d in domains:
        covered_reqs.update(d.get("required_for", []))

    assert all_req_ids.issubset(covered_reqs), f"Requirements not covered in knowledge domains: {all_req_ids - covered_reqs}"


def test_query_intents_cover_requirements(query_intents_data, requirements_data):
    """Verifies that engineering query intents are established, map to valid RQ IDs via lists, and separate states."""
    intents = query_intents_data.get("domain_intents", [])
    assert len(intents) >= 15, f"Expected at least 15 domain query intents, found {len(intents)}"

    states = query_intents_data.get("query_states", [])
    assert len(states) >= 5, f"Expected at least 5 query states, found {len(states)}"

    all_req_ids = {r["id"] for r in requirements_data.get("requirements", [])}
    for item in intents:
        assert "intent" in item
        assert "description" in item
        assert isinstance(item.get("maps_to_requirements"), list), f"Intent {item['intent']} maps_to_requirements must be a list"
        assert len(item["maps_to_requirements"]) > 0, f"Intent {item['intent']} maps_to_requirements cannot be empty"
        for rq_id in item["maps_to_requirements"]:
            assert rq_id in all_req_ids, f"Intent {item['intent']} maps to unknown requirement {rq_id}"


def test_phase1_documentation_artifacts_exist():
    """Verifies that all required Phase 1 documentation artifacts exist in docs/phase1/."""
    expected_docs = [
        "SIH_PS_REQUIREMENTS.md",
        "PS_SCOPE_BOUNDARIES.md",
        "PS_TRACEABILITY_MATRIX.md",
        "ANSWER_GROUNDING_POLICY.md",
        "EVALUATION_POLICY.md",
        "PHASE_1_COMPLETION_REPORT.md"
    ]
    for doc in expected_docs:
        doc_path = DOCS_DIR / doc
        assert doc_path.exists(), f"Missing documentation artifact: {doc_path}"
        assert doc_path.stat().st_size > 200, f"Documentation artifact {doc} is too small / empty"
