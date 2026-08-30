import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
METADATA_DIR = Path("data/metadata")
REGISTRY_PATH = METADATA_DIR / "source_registry.json"


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file for cryptographic provenance."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def register_acquired_document(
    source_id: str,
    raw_file_path: Path,
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registers an acquired raw document into the source registry.
    Calculates SHA-256 hash, file size, timestamp, and advances status to 'document_acquired'.
    """
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_file_path}")

    file_hash = compute_sha256(raw_file_path)
    file_size_bytes = raw_file_path.stat().st_size
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    record_found = False
    updated_record = {}

    for item in registry:
        if item["source_id"] == source_id:
            item["file_path"] = str(raw_file_path)
            item["file_sha256"] = file_hash
            item["file_size_bytes"] = file_size_bytes
            item["retrieval_date"] = retrieval_timestamp
            item["status"] = "document_acquired"
            if source_url:
                item["url"] = source_url
            if notes:
                item["notes"] = notes
            record_found = True
            updated_record = item
            break

    if not record_found:
        raise ValueError(f"Source ID '{source_id}' not found in registry {REGISTRY_PATH}")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    logger.info(
        "Registered document %s -> %s (SHA-256: %s, Size: %d bytes)",
        source_id,
        raw_file_path,
        file_hash,
        file_size_bytes,
    )

    return updated_record
