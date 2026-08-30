import hashlib
import tempfile
from pathlib import Path
from ai.ingestion.acquisition import compute_sha256


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
