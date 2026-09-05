"""
Phase 2A Automated Source Architecture & Source Family Verification Suite.
Validates that official BIS and statutory source families (SRCF-001 to SRCF-012),
source ownership classifications, authority tiers, laboratory status categories, and hallmarking subfamilies
are structurally defined, conform to schemas, and strictly bound to approved government domain namespaces.
"""
import json
import pytest
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SOURCE_FAMILIES_PATH = ROOT_DIR / "data" / "sources" / "source_families.json"
REQ_JSON_PATH = ROOT_DIR / "data" / "requirements" / "sih_requirements.json"
DOCS_PHASE2_DIR = ROOT_DIR / "docs" / "phase2"

# Official government and BIS domain namespaces
AUTHORIZED_GOV_DOMAINS = {
    "bis.gov.in",
    "www.bis.gov.in",
    "egazette.gov.in",
    "www.egazette.gov.in",
    "manakonline.in",
    "www.manakonline.in",
    "crsbis.in",
    "www.crsbis.in",
    "standardsbis.bsbedge.com"
}


@pytest.fixture(scope="module")
def source_families_data():
    assert SOURCE_FAMILIES_PATH.exists(), f"Missing source families catalog: {SOURCE_FAMILIES_PATH}"
    with open(SOURCE_FAMILIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def requirements_data():
    assert REQ_JSON_PATH.exists(), f"Missing requirements specification: {REQ_JSON_PATH}"
    with open(REQ_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_source_families_catalog_integrity(source_families_data):
    """Verifies that all 12 BIS and statutory source families SRCF-001 through SRCF-012 exist with complete metadata."""
    families = source_families_data.get("source_families", [])
    assert len(families) == 12, f"Expected exactly 12 source families, found {len(families)}"

    expected_ids = {f"SRCF-{i:03d}" for i in range(1, 13)}
    found_ids = {f["source_family_id"] for f in families}
    assert found_ids == expected_ids, f"Missing source family IDs: {expected_ids - found_ids}"

    valid_ownerships = set(source_families_data.get("source_ownership_types", {}).keys())
    assert valid_ownerships == {"BIS_PUBLISHED", "BIS_OPERATED", "STATUTORY_EXTERNAL"}

    for fam in families:
        assert fam["status"] == "ACTIVE", f"Source family {fam['source_family_id']} must be ACTIVE"
        assert len(fam["name"]) > 3, f"Source family {fam['source_family_id']} has invalid name"
        assert fam["source_ownership"] in valid_ownerships, f"Source family {fam['source_family_id']} invalid ownership"
        assert len(fam["issuing_authority"]) > 2, f"Source family {fam['source_family_id']} missing issuing authority"
        assert len(fam["primary_purpose"]) > 10, f"Source family {fam['source_family_id']} missing purpose"
        assert len(fam["knowledge_types"]) > 0, f"Source family {fam['source_family_id']} missing knowledge types"
        assert len(fam["official_entry_urls"]) > 0, f"Source family {fam['source_family_id']} missing entry URLs"
        assert len(fam["possible_claim_roles"]) > 0, f"Source family {fam['source_family_id']} missing claim roles"


def test_source_families_cover_all_ps_requirements(source_families_data, requirements_data):
    """Verifies that every PS requirement RQ-001 through RQ-010 is covered by at least one official source family."""
    all_req_ids = {r["id"] for r in requirements_data.get("requirements", [])}
    covered_req_ids = set()

    for fam in source_families_data.get("source_families", []):
        covered_req_ids.update(fam.get("ps_requirements", []))

    missing_reqs = all_req_ids - covered_req_ids
    assert len(missing_reqs) == 0, f"PS requirements not covered by any source family: {missing_reqs}"


def test_authority_classes_validity(source_families_data):
    """Verifies that every source family uses a defined, valid default authority class."""
    valid_classes = set(source_families_data.get("authority_classes", {}).keys())
    assert len(valid_classes) == 4, "Expected exactly 4 authority classes defined"

    for fam in source_families_data.get("source_families", []):
        auth_class = fam.get("default_authority_class")
        assert auth_class in valid_classes, (
            f"Source family {fam['source_family_id']} has invalid default authority class: {auth_class}"
        )


def test_laboratory_and_hallmarking_modeling(source_families_data):
    """Verifies that laboratory status types and hallmarking subfamilies are explicitly structured."""
    families_by_id = {f["source_family_id"]: f for f in source_families_data.get("source_families", [])}

    # Test Laboratory status types in SRCF-008
    lab_fam = families_by_id["SRCF-008"]
    assert "laboratory_status_categories" in lab_fam
    assert set(lab_fam["laboratory_status_categories"]) == {
        "BIS_OWNED", "BIS_RECOGNIZED", "BIS_EMPANELLED", "NABL_ACCREDITED", "OTHER_RECOGNIZED"
    }

    # Test Hallmarking subfamilies in SRCF-009
    hallmark_fam = families_by_id["SRCF-009"]
    assert "subfamilies" in hallmark_fam
    subfamily_ids = {sub["subfamily_id"] for sub in hallmark_fam["subfamilies"]}
    expected_subfamily_ids = {"SRCF-009A", "SRCF-009B", "SRCF-009C", "SRCF-009D", "SRCF-009E", "SRCF-009F"}
    assert subfamily_ids == expected_subfamily_ids


def test_official_portals_are_authorized_gov_domains(source_families_data):
    """Verifies that all listed official entry URLs resolve to authorized government/BIS domain namespaces."""
    for fam in source_families_data.get("source_families", []):
        for portal_url in fam.get("official_entry_urls", []):
            parsed = urlparse(portal_url)
            domain = parsed.netloc.lower()
            assert domain in AUTHORIZED_GOV_DOMAINS, (
                f"Source family {fam['source_family_id']} contains non-whitelisted portal domain: {domain}"
            )


def test_untrusted_and_commercial_domain_rejection():
    """Verifies that arbitrary external, commercial, or app store URLs are strictly rejected from trusted namespaces."""
    untrusted_urls = [
        "https://random-standards-blog.com/is-1786.pdf",
        "http://commercial-spec-seller.in/specs",
        "https://forum.engineering-talk.com/threads/bis-qco",
        "https://unofficial-bis-guide.org/download",
        "https://play.google.com/store/apps/details?id=com.bis.mobile"
    ]
    for url in untrusted_urls:
        domain = urlparse(url).netloc.lower()
        assert domain not in AUTHORIZED_GOV_DOMAINS, f"Untrusted domain {domain} was erroneously recognized as gov domain"


def test_phase2a_documentation_exists():
    """Verifies that Phase 2A documentation artifacts exist and detail all 12 source families."""
    catalog_path = DOCS_PHASE2_DIR / "SOURCE_FAMILY_CATALOG.md"
    assert catalog_path.exists(), f"Missing catalog document: {catalog_path}"
    content = catalog_path.read_text(encoding="utf-8")

    for i in range(1, 13):
        src_id = f"SRCF-{i:03d}"
        assert src_id in content, f"Catalog missing documentation for {src_id}"
