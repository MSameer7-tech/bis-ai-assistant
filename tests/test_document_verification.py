import json
import pymupdf
from pathlib import Path
from ai.ingestion.acquisition import compute_sha256

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"


def test_all_acquired_documents_exist_and_match_hashes():
    """Validates that every document in documents.json exists, matches its SHA-256 hash and file size exactly."""
    assert DOCUMENTS_PATH.exists(), "documents.json must exist"

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    assert len(docs) == 6, f"Expected 6 acquired pilot documents, found {len(docs)}"

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
        assert reg_entry["status"] == "document_acquired"
        assert reg_entry["file_sha256"] == actual_hash
        assert reg_entry["document_id"] == doc["document_id"]


def test_all_acquired_documents_are_valid_openable_pdfs():
    """Validates that every acquired document is an authentic, readable, non-corrupted PDF."""
    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    for doc in docs:
        file_path = ROOT_DIR / doc["file_path"]
        pdf_doc = pymupdf.open(str(file_path))
        try:
            assert pdf_doc.page_count > 0, f"PDF has 0 pages: {file_path}"
            page1 = pdf_doc[0]
            text = page1.get_text()
            # Verify the page contains actual extractable text
            assert len(text.strip()) > 20, f"Page 1 has insufficient or unreadable text in {file_path}"
        finally:
            pdf_doc.close()
