"""
Automated Verification Suite for Hardened Phase 3: Bulk BIS Data Discovery & Acquisition.
Validates strategy-based discovery, zero-fallback canonical identity, persistent 1-to-many deduplication,
magic-byte validation, and structured relationship graph edge modeling.
"""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
CANDIDATES_PATH = ROOT_DIR / "data" / "candidates" / "candidate_documents.json"
DISCOVERY_REPORT_PATH = ROOT_DIR / "data" / "candidates" / "discovery_run_report.json"
IDENTITY_REGISTRY_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "document_identity_registry.json"
DOCS_PHASE3_DIR = ROOT_DIR / "docs" / "phase3"

from ai.acquisition.discovery_engine import DiscoveryEngine, CandidateDocument
from ai.acquisition.candidate_validator import CandidateValidator
from ai.acquisition.content_validator import ContentValidator
from ai.acquisition.identity_resolver import IdentityResolver, DeduplicationDecision, normalize_std_number, normalize_part
from ai.acquisition.relationship_discoverer import RelationshipDiscoverer, RelationshipEdge


@pytest.fixture(scope="module")
def manifest_data():
    assert MANIFEST_PATH.exists(), f"Missing acquisition manifest: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_discovery_strategies_dispatch_and_track_metrics():
    """Verifies that all registered endpoints are queried with metrics tracked."""
    engine = DiscoveryEngine()
    candidates = engine.discover_all_candidates()
    assert len(candidates) >= 50, f"Expected at least 50 candidates, got {len(candidates)}"
    assert DISCOVERY_REPORT_PATH.exists()

    with open(DISCOVERY_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["total_endpoints_queried"] == 18
    assert len(report["endpoint_metrics"]) == 18


def test_candidate_urls_are_raw_and_not_markdown():
    """Verifies that candidate URLs are pure machine-readable URLs and not Markdown links."""
    engine = DiscoveryEngine()
    candidates = engine.discover_all_candidates()
    for c in candidates:
        assert not c.source_url.startswith("["), f"Candidate URL contains Markdown: {c.source_url}"
        assert c.source_url.startswith("http://") or c.source_url.startswith("https://")


def test_zero_fallback_identity_rejection():
    """Verifies that missing critical fields return IDENTITY_INCOMPLETE rather than manufacturing fake fallback IDs."""
    resolver = IdentityResolver()

    # 1. Missing standard number
    doc_id, fam_id, err = resolver.generate_document_id(
        document_type="INDIAN_STANDARD",
        standard_number=None,
        edition_year=2024
    )
    assert doc_id is None
    assert "MANUAL_REVIEW" in err

    # 2. Missing amendment number
    doc_id, fam_id, err = resolver.generate_document_id(
        document_type="AMENDMENT",
        standard_number="IS 1234",
        amendment_number=None,
        edition_year=2024
    )
    assert doc_id is None
    assert "MANUAL_REVIEW" in err

    # 3. Missing gazette number for QCO
    doc_id, fam_id, err = resolver.generate_document_id(
        document_type="QCO_NOTIFICATION",
        ministry_acronym="MORTH",
        notification_number=None
    )
    assert doc_id is None
    assert "MANUAL_REVIEW" in err


def test_identity_resolver_normalizes_standard_part_and_edition():
    """Verifies that standard numbers and parts are normalized deterministically."""
    resolver = IdentityResolver()

    doc_id, fam_id, err = resolver.generate_document_id(
        document_type="INDIAN_STANDARD",
        standard_number="IS 16046 : 2018",
        part="Part 2",
        edition_year=2018
    )
    assert err is None
    assert doc_id == "IS-16046-P2-2018"
    assert fam_id == "IS-16046"


def test_persistent_registry_and_1_to_many_hash_aliases():
    """Verifies that multiple distinct IDs sharing the same hash are tracked in 1-to-many alias set."""
    with TemporaryDirectory() as tmp_dir:
        reg_file = Path(tmp_dir) / "test_identity_registry.json"
        resolver = IdentityResolver(registry_path=reg_file)

        # 1. Ingest document A
        d1 = resolver.resolve_deduplication("DOC-A", "FAM-A", "hash_xxx")
        assert d1.deduplication_status == "DISTINCT_DOCUMENT"

        # 2. Ingest document B with same hash -> DUPLICATE_REPRESENTATION_ALIAS
        d2 = resolver.resolve_deduplication("DOC-B", "FAM-B", "hash_xxx")
        assert d2.deduplication_status == "DUPLICATE_REPRESENTATION_ALIAS"
        assert "DOC-A" in d2.alias_of_document_ids

        # 3. Verify persistent reload
        resolver2 = IdentityResolver(registry_path=reg_file)
        assert resolver2.known_id_to_hash["DOC-A"] == "hash_xxx"
        assert resolver2.known_id_to_hash["DOC-B"] == "hash_xxx"
        assert "DOC-A" in resolver2.known_hash_to_ids["hash_xxx"]
        assert "DOC-B" in resolver2.known_hash_to_ids["hash_xxx"]


def test_deduplication_version_review_trigger():
    """Verifies that same ID + different hash triggers CONTENT_CHANGED_REQUIRES_VERSION_REVIEW."""
    with TemporaryDirectory() as tmp_dir:
        reg_file = Path(tmp_dir) / "test_identity_registry.json"
        resolver = IdentityResolver(registry_path=reg_file)

        d1 = resolver.resolve_deduplication("IS-1786-2008", "IS-1786", "hash_initial")
        assert d1.deduplication_status == "DISTINCT_DOCUMENT"

        d2 = resolver.resolve_deduplication("IS-1786-2008", "IS-1786", "hash_modified")
        assert d2.deduplication_status == "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW"


def test_exact_structured_relationship_matching():
    """Verifies that prefix string matching is eliminated and IS-1234 does NOT link to IS-12340."""
    discoverer = RelationshipDiscoverer()
    docs = [
        {
            "document": {
                "document_id": "IS-1234-2020",
                "document_family_id": "IS-1234",
                "document_type": "INDIAN_STANDARD"
            },
            "source": {"source_id": "SRC-001"}
        },
        {
            "document": {
                "document_id": "IS-12340-2019",
                "document_family_id": "IS-12340",
                "document_type": "INDIAN_STANDARD"
            },
            "source": {"source_id": "SRC-001"}
        },
        {
            "document": {
                "document_id": "PM-IS-1234-2020-V1",
                "document_family_id": "PM-IS-1234",
                "document_type": "PRODUCT_MANUAL"
            },
            "source": {"source_id": "SRC-006"}
        }
    ]

    relationships = discoverer.discover_relationships(docs)
    target_ids = {r.target_document_id for r in relationships}
    assert "IS-1234-2020" in target_ids
    assert "IS-12340-2019" not in target_ids, "False positive prefix match detected: IS-1234 matched IS-12340!"


def test_relationship_edge_model_and_evidence_payload():
    """Verifies that relationship edges contain deterministic ID, confidence, and structured evidence."""
    discoverer = RelationshipDiscoverer()
    docs = [
        {
            "document": {
                "document_id": "IS-1786-2008",
                "document_family_id": "IS-1786",
                "document_type": "INDIAN_STANDARD"
            },
            "source": {"source_id": "SRC-001"}
        },
        {
            "document": {
                "document_id": "IS-1786-2008-A1",
                "document_family_id": "IS-1786",
                "document_type": "AMENDMENT",
                "parent_document_id": "IS-1786-2008"
            },
            "source": {"source_id": "SRC-003"}
        }
    ]

    relationships = discoverer.discover_relationships(docs)
    assert len(relationships) == 1
    edge: RelationshipEdge = relationships[0]
    assert edge.relationship_id.startswith("REL-")
    assert edge.relationship_type == "AMENDS"
    assert edge.confidence == 1.0
    assert edge.evidence_type == "EXPLICIT_FIELD"
    assert edge.evidence_payload.get("field") == "parent_document_id"


def test_candidate_validator_quarantines_unauthorized_domain():
    """Verifies that candidate validator rejects external domains and logs to quarantine."""
    validator = CandidateValidator()
    bad_cand = CandidateDocument(
        candidate_id="CAND-TEST-EXTERNAL",
        source_id="SRC-001",
        source_family_id="SRCF-001",
        source_url="https://commercial-standard-reseller.com/is1786.pdf",
        discovered_from_url="https://www.bis.gov.in/",
        document_type="INDIAN_STANDARD",
        title="Commercial Reseller PDF",
        discovery_method="HTML_SEARCH"
    )
    ok, reason = validator.validate_candidate(bad_cand)
    assert ok is False
    assert "not whitelisted" in reason


def test_content_validator_magic_bytes_and_anti_masquerade():
    """Verifies that valid PDFs pass and masquerading HTML error pages fail."""
    validator = ContentValidator()
    with TemporaryDirectory() as tmp_dir:
        good_pdf = Path(tmp_dir) / "good.pdf"
        good_pdf.write_bytes(b"%PDF-1.4\n%Authoritative\n%%EOF")
        ok1, _ = validator.validate_file(good_pdf, expected_format="PDF", reported_content_type="application/pdf")
        assert ok1 is True

        fake_pdf = Path(tmp_dir) / "fake.pdf"
        fake_pdf.write_bytes(b"<!DOCTYPE html><html><body>Error 404: Not Found</body></html>")
        ok2, err2 = validator.validate_file(fake_pdf, expected_format="PDF", reported_content_type="application/pdf")
        assert ok2 is False
        assert "Masquerading" in err2 or "Invalid PDF" in err2


def test_manifest_conforms_to_3_block_provenance_schema(manifest_data):
    """Verifies that the acquisition manifest contains full 3-block provenance and valid SHA-256 checksums."""
    assert manifest_data["manifest_version"] == "1.0"
    assert "total_acquired" in manifest_data
    assert "total_relationships" in manifest_data

    for doc_entry in manifest_data["documents"]:
        assert "document" in doc_entry
        assert "source" in doc_entry
        assert "acquisition" in doc_entry

        doc = doc_entry["document"]
        assert len(doc["document_id"]) > 3
        assert len(doc["title"]) > 3

        acq = doc_entry["acquisition"]
        assert len(acq["sha256"]) == 64
        assert acq["validation_passed"] is True
        assert Path(ROOT_DIR / acq["storage_path"]).exists()


def test_documentation_artifacts_exist():
    """Verifies that all 8 required Phase 3 documentation artifacts exist in docs/phase3/."""
    expected_docs = [
        "BULK_ACQUISITION_ARCHITECTURE.md",
        "DISCOVERY_ENGINE_SPEC.md",
        "CONTENT_VALIDATION_SPEC.md",
        "DEDUPLICATION_POLICY.md",
        "RELATIONSHIP_DISCOVERY_SPEC.md",
        "ACQUISITION_MANIFEST_SCHEMA.md",
        "PHASE_3_ACCEPTANCE_CRITERIA.md",
        "PHASE_3_COMPLETION_REPORT.md"
    ]
    for doc in expected_docs:
        doc_path = DOCS_PHASE3_DIR / doc
        assert doc_path.exists(), f"Missing documentation artifact: {doc}"
        assert doc_path.stat().st_size > 150, f"Document {doc} is too short / empty"
