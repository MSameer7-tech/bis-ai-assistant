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


def test_register_acquired_document(monkeypatch):
    test_bytes = b"Sample IS 16102 standard raw text content"
    expected_hash = hashlib.sha256(test_bytes).hexdigest()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_registry_file = tmp_path / "source_registry.json"
        mock_raw_file = tmp_path / "IS_16102_Sample.txt"

        mock_raw_file.write_bytes(test_bytes)
        initial_registry = [
            {
                "source_id": "SRC-TEST-001",
                "title": "Test Standard",
                "status": "document_identified",
            }
        ]
        mock_registry_file.write_text(json.dumps(initial_registry), encoding="utf-8")

        # Monkeypatch the REGISTRY_PATH in ai.ingestion.acquisition
        import ai.ingestion.acquisition as acq
        monkeypatch.setattr(acq, "REGISTRY_PATH", mock_registry_file)

        updated = register_acquired_document("SRC-TEST-001", mock_raw_file, notes="Test acquisition")

        assert updated["status"] == "document_acquired"
        assert updated["file_sha256"] == expected_hash
        assert updated["file_size_bytes"] == len(test_bytes)
        assert updated["notes"] == "Test acquisition"
