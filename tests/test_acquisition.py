import hashlib
import json
import tempfile
from pathlib import Path
from ai.ingestion.acquisition import compute_sha256, register_acquired_document


def test_compute_sha256():
    test_bytes = b"Bureau of Indian Standards Test Content"
    expected_hash = hashlib.sha256(test_bytes).hexdigest()

    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(test_bytes)
        tmp_path = Path(tmp.name)

    try:
        calculated_hash = compute_sha256(tmp_path)
        assert len(calculated_hash) == 64
        assert calculated_hash == expected_hash
    finally:
        tmp_path.unlink()


def test_register_acquired_document_linking(monkeypatch):
    test_bytes = b"Sample IS 16102 standard raw text content"
    expected_hash = hashlib.sha256(test_bytes).hexdigest()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_registry_file = tmp_path / "source_registry.json"
        mock_docs_file = tmp_path / "documents.json"
        mock_raw_file = tmp_path / "IS_16102_Sample.pdf"

        mock_raw_file.write_bytes(test_bytes)
        initial_registry = [
            {
                "source_id": "SRC-TEST-001",
                "title": "Test Standard",
                "status": "document_identified",
            }
        ]
        mock_registry_file.write_text(json.dumps(initial_registry), encoding="utf-8")
        mock_docs_file.write_text(json.dumps([]), encoding="utf-8")

        import ai.ingestion.acquisition as acq
        monkeypatch.setattr(acq, "REGISTRY_PATH", mock_registry_file)
        monkeypatch.setattr(acq, "DOCUMENTS_PATH", mock_docs_file)

        doc_record = register_acquired_document(
            document_id="DOC-001",
            source_id="SRC-TEST-001",
            raw_file_path=mock_raw_file,
            title="Self-Ballasted LED Lamps Safety",
            document_number="IS 16102 (Part 1) : 2012",
            notes="Initial pilot acquisition",
        )

        assert doc_record["document_id"] == "DOC-001"
        assert doc_record["source_id"] == "SRC-TEST-001"
        assert doc_record["file_sha256"] == expected_hash
        assert doc_record["status"] == "document_acquired"

        # Check documents.json
        with open(mock_docs_file, "r") as f:
            docs = json.load(f)
        assert len(docs) == 1
        assert docs[0]["document_id"] == "DOC-001"

        # Check source_registry.json
        with open(mock_registry_file, "r") as f:
            reg = json.load(f)
        assert reg[0]["document_id"] == "DOC-001"
        assert reg[0]["status"] == "document_acquired"
