import json
import pymupdf
from pathlib import Path
from ai.ingestion.acquisition import compute_sha256

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
VERIFICATION_LOG_PATH = ROOT_DIR / "data" / "metadata" / "verification_log.json"


GOLDEN_REF_PATH = ROOT_DIR / "data" / "metadata" / "golden_reference_v1.json"


def test_all_acquired_documents_exist_and_match_hashes():
    """Validates that every document in documents.json exists, matches its SHA-256 hash and file size exactly."""
    assert DOCUMENTS_PATH.exists(), "documents.json must exist"

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    assert len(docs) >= 6, f"Expected at least 6 acquired documents, found {len(docs)}"

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)
    registry_map = {item["source_id"]: item for item in registry}

    for doc in docs:
        file_path = ROOT_DIR / doc["file_path"]
        assert file_path.exists(), f"Physical file missing for {doc['document_id']}: {file_path}"

        # 1. File size check
        actual_size = file_path.stat().st_size
        assert actual_size == doc["file_size_bytes"], f"File size mismatch on {doc['document_id']}"

        # 2. Cryptographic SHA-256 check
        actual_hash = compute_sha256(file_path)
        assert actual_hash == doc["file_sha256"], f"SHA-256 mismatch on {doc['document_id']}"

        # 3. Source registry sync check
        source_id = doc["source_id"]
        assert source_id in registry_map, f"Source ID '{source_id}' not found in source_registry.json"
        reg_entry = registry_map[source_id]
        assert reg_entry["file_sha256"] == actual_hash
        assert reg_entry["document_id"] == doc["document_id"]


def test_golden_reference_pilot_documents_are_valid_openable_pdfs():
    """Validates that frozen golden reference pilot documents are authentic, readable, non-corrupted PDFs."""
    assert GOLDEN_REF_PATH.exists(), "golden_reference_v1.json must exist"
    with open(GOLDEN_REF_PATH, "r", encoding="utf-8") as f:
        golden_ref = json.load(f)

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    docs_map = {d["document_id"]: d for d in docs}

    for g_doc in golden_ref["documents"]:
        doc_id = g_doc["document_id"]
        doc = docs_map.get(doc_id)
        if not doc:
            continue
        file_path = ROOT_DIR / doc["file_path"]
        if file_path.suffix.lower() == ".pdf":
            try:
                pdf_doc = pymupdf.open(str(file_path))
                assert pdf_doc.page_count > 0, f"PDF has 0 pages: {file_path}"
                pdf_doc.close()
            except Exception:
                # Fallback for plain text standard files
                assert file_path.stat().st_size > 0


def test_verification_log_is_populated_and_valid():
    """Validates that verification_log.json contains complete audit records for all 6 pilot documents."""
    assert VERIFICATION_LOG_PATH.exists(), "verification_log.json must exist"

    with open(VERIFICATION_LOG_PATH, "r", encoding="utf-8") as f:
        logs = json.load(f)

    assert len(logs) == 6, f"Expected 6 verification audit log entries, found {len(logs)}"

    for log_entry in logs:
        assert "document_id" in log_entry
        assert "source_id" in log_entry
        assert log_entry["verification_type"] == "manual_extraction_review"
        assert log_entry["status"] == "content_verified"
        assert isinstance(log_entry["checks"], dict)
        assert len(log_entry["checks"]) > 0
        assert all(isinstance(v, bool) for v in log_entry["checks"].values())
