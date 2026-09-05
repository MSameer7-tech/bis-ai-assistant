"""
Automated Source Registry & Endpoint Verification Suite for Phase 2B.
Validates the 15 architectural, security, and integrity requirements for official BIS and statutory endpoints.
"""
import json
import pytest
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "sources" / "source_registry.json"
FAMILIES_PATH = ROOT_DIR / "data" / "sources" / "source_families.json"
ACCESS_METHODS_PATH = ROOT_DIR / "data" / "sources" / "source_access_methods.json"
AUTH_LEVELS_PATH = ROOT_DIR / "data" / "sources" / "source_authority_levels.json"
VERSION_RULES_PATH = ROOT_DIR / "data" / "sources" / "source_version_rules.json"
METADATA_SCHEMA_PATH = ROOT_DIR / "data" / "sources" / "document_metadata_schema.json"
DOCS_PHASE2_DIR = ROOT_DIR / "docs" / "phase2"

from ai.acquisition.source_gate import (
    AUTHORIZED_GOV_DOMAINS,
    VALID_VERIFICATION_STATUSES,
    is_domain_authorized,
    is_source_acquisition_eligible
)


@pytest.fixture(scope="module")
def registry_data():
    assert REGISTRY_PATH.exists(), f"Missing source registry: {REGISTRY_PATH}"
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def families_data():
    assert FAMILIES_PATH.exists(), f"Missing source families catalog: {FAMILIES_PATH}"
    with open(FAMILIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def access_methods_data():
    assert ACCESS_METHODS_PATH.exists(), f"Missing access methods: {ACCESS_METHODS_PATH}"
    with open(ACCESS_METHODS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def auth_levels_data():
    assert AUTH_LEVELS_PATH.exists(), f"Missing authority levels: {AUTH_LEVELS_PATH}"
    with open(AUTH_LEVELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def version_rules_data():
    assert VERSION_RULES_PATH.exists(), f"Missing version rules: {VERSION_RULES_PATH}"
    with open(VERSION_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def metadata_schema_data():
    assert METADATA_SCHEMA_PATH.exists(), f"Missing metadata schema: {METADATA_SCHEMA_PATH}"
    with open(METADATA_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Test 1: Every source has a unique source_id
def test_every_source_has_unique_id(registry_data):
    sources = registry_data.get("sources", [])
    assert len(sources) >= 12, f"Expected at least 12 registered sources, found {len(sources)}"
    source_ids = [s["source_id"] for s in sources]
    assert len(source_ids) == len(set(source_ids)), "Duplicate source_id detected in registry"


# Test 2: Every source references an existing source_family_id
def test_every_source_references_existing_family(registry_data, families_data):
    valid_family_ids = {f["source_family_id"] for f in families_data.get("source_families", [])}
    for s in registry_data.get("sources", []):
        fam_id = s.get("source_family_id")
        assert fam_id in valid_family_ids, f"Source {s['source_id']} references invalid family {fam_id}"


# Test 3: Every source has a valid canonical_url
def test_every_source_has_canonical_url(registry_data):
    for s in registry_data.get("sources", []):
        url = s.get("canonical_url")
        assert url and isinstance(url, str), f"Source {s['source_id']} missing canonical_url"
        parsed = urlparse(url)
        assert parsed.scheme in {"http", "https"}, f"Source {s['source_id']} has invalid URL scheme: {url}"


# Test 4: Every URL uses an authorized domain
def test_every_url_uses_authorized_domain(registry_data):
    for s in registry_data.get("sources", []):
        url = s.get("canonical_url", "")
        assert is_domain_authorized(url), f"Source {s['source_id']} uses non-authorized domain: {url}"


# Test 5: Source ownership is valid
def test_source_ownership_is_valid(registry_data):
    valid_ownerships = {"BIS_PUBLISHED", "BIS_OPERATED", "STATUTORY_EXTERNAL"}
    for s in registry_data.get("sources", []):
        ownership = s.get("source_ownership")
        assert ownership in valid_ownerships, f"Source {s['source_id']} has invalid ownership: {ownership}"


# Test 6: Authority class is valid
def test_authority_class_is_valid(registry_data, auth_levels_data):
    valid_classes = {lvl["code"] for lvl in auth_levels_data.get("authority_levels", [])}
    for s in registry_data.get("sources", []):
        auth_class = s.get("authority_class")
        assert auth_class in valid_classes, f"Source {s['source_id']} has invalid authority_class: {auth_class}"


# Test 7: Source type is valid
def test_source_type_is_valid(registry_data):
    valid_types = {"PORTAL", "CATALOG", "DATABASE_REGISTER", "STATUTORY_GAZETTE", "SEARCH_ENGINE"}
    for s in registry_data.get("sources", []):
        stype = s.get("source_type")
        assert stype in valid_types, f"Source {s['source_id']} has invalid source_type: {stype}"


# Test 8: Discovery method / access method is valid
def test_access_method_is_valid(registry_data, access_methods_data):
    valid_methods = {m["method_code"] for m in access_methods_data.get("access_methods", [])}
    for s in registry_data.get("sources", []):
        method = s.get("access_method")
        assert method in valid_methods, f"Source {s['source_id']} has invalid access_method: {method}"


# Test 9: Content types are valid
def test_content_types_are_valid(registry_data):
    allowed_types = {"HTML", "PDF", "JSON"}
    for s in registry_data.get("sources", []):
        ctypes = s.get("content_types", [])
        assert len(ctypes) > 0, f"Source {s['source_id']} has empty content_types"
        for ct in ctypes:
            assert ct in allowed_types, f"Source {s['source_id']} has unknown content_type: {ct}"


# Test 10: No duplicate canonical URLs
def test_no_duplicate_canonical_urls(registry_data):
    urls = [s["canonical_url"].strip().rstrip("/") for s in registry_data.get("sources", [])]
    assert len(urls) == len(set(urls)), "Duplicate canonical URLs found across distinct source endpoints"


# Test 11: Every PS-required source family has >= 1 registered source
def test_every_family_has_registered_source(registry_data, families_data):
    registered_family_ids = {s["source_family_id"] for s in registry_data.get("sources", [])}
    for fam in families_data.get("source_families", []):
        fam_id = fam["source_family_id"]
        assert fam_id in registered_family_ids, f"Source family {fam_id} has no registered source endpoint"


# Test 12: Unified verification metadata schema is valid
def test_verification_metadata_schema_valid(registry_data):
    required_keys = {
        "verification_status",
        "verification_mode",
        "verified_at",
        "http_status",
        "final_url",
        "content_type",
        "content_type_valid",
        "title_match",
        "domain_whitelisted",
        "redirect_chain",
        "tls_verified",
        "acquisition_eligible"
    }
    for s in registry_data.get("sources", []):
        vmeta = s.get("verification_metadata")
        assert vmeta is not None, f"Source {s['source_id']} missing verification_metadata"
        assert set(vmeta.keys()) == required_keys, f"Source {s['source_id']} verification keys mismatch"
        assert vmeta["verification_status"] in VALID_VERIFICATION_STATUSES
        assert vmeta["verification_mode"] in {"LIVE", "OFFLINE"}


# Test 13: Authoritative acquisition gate function enforcement
def test_acquisition_gate_enforcement(registry_data):
    for s in registry_data.get("sources", []):
        eligible = is_source_acquisition_eligible(s)
        if s.get("status") == "ACTIVE":
            assert eligible is True, f"Valid active source {s['source_id']} failed acquisition gate"
        else:
            assert eligible is False, f"Non-active source {s['source_id']} was unexpectedly marked eligible"

    # Test rejection of deactivated or invalid sources
    dummy_inactive = {
        "status": "INACTIVE",
        "canonical_url": "https://www.bis.gov.in/test",
        "verification_metadata": {"verification_status": "OFFLINE_RULES_VALID", "acquisition_eligible": True}
    }
    assert is_source_acquisition_eligible(dummy_inactive) is False

    dummy_bad_status = {
        "status": "ACTIVE",
        "canonical_url": "https://www.bis.gov.in/test",
        "verification_metadata": {"verification_status": "NETWORK_FAILURE", "acquisition_eligible": False}
    }
    assert is_source_acquisition_eligible(dummy_bad_status) is False

    dummy_redirect_outside = {
        "status": "ACTIVE",
        "canonical_url": "https://www.bis.gov.in/test",
        "verification_metadata": {
            "verification_status": "REDIRECT_OUTSIDE_AUTHORIZED_DOMAIN",
            "final_url": "https://unauthorized-external-site.com",
            "acquisition_eligible": False
        }
    }
    assert is_source_acquisition_eligible(dummy_redirect_outside) is False


# Test 14: Structured identity models and hash review rules
def test_structured_identity_and_version_rules(version_rules_data):
    models = version_rules_data.get("document_identity_models", {})
    assert "standard_specification" in models
    assert "standard_amendment" in models
    assert "gazette_qco" in models

    std_model = models["standard_specification"]
    assert "structured_fields" in std_model
    assert "document_family_id" in std_model["structured_fields"]
    assert "part" in std_model["structured_fields"]

    hash_rules = version_rules_data.get("content_hash_rules", {}).get("deduplication_logic", {})
    assert hash_rules.get("same_id_different_hash") == "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW"


# Test 15: Source registry documentation and metadata schema separation
def test_documentation_and_metadata_schema_separation(metadata_schema_data):
    props = metadata_schema_data.get("properties", {})
    assert "document" in props, "Metadata schema missing 'document' block"
    assert "source" in props, "Metadata schema missing 'source' block"
    assert "acquisition" in props, "Metadata schema missing 'acquisition' block"

    expected_docs = [
        "BIS_SOURCE_ARCHITECTURE.md",
        "SOURCE_FAMILY_CATALOG.md",
        "SOURCE_DISCOVERY_PROTOCOL.md",
        "SOURCE_ACCESS_MATRIX.md",
        "SOURCE_VERSIONING_POLICY.md",
        "SOURCE_PROVENANCE_POLICY.md",
        "DOCUMENT_ACQUISITION_CONTRACT.md",
        "SOURCE_PRIORITY_POLICY.md",
        "PHASE_2_ACCEPTANCE_CRITERIA.md",
        "PHASE_2_COMPLETION_REPORT.md"
    ]
    for doc in expected_docs:
        doc_path = DOCS_PHASE2_DIR / doc
        assert doc_path.exists(), f"Missing documentation artifact: {doc}"
        assert doc_path.stat().st_size > 150, f"Document {doc} is too short / empty"
