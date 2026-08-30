import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
METADATA_DIR = ROOT_DIR / "data" / "metadata"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"
DOCUMENTS_PATH = METADATA_DIR / "documents.json"


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file for cryptographic provenance."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def register_acquired_document(
    document_id: str,
    source_id: str,
    raw_file_path: Path,
    title: Optional[str] = None,
    document_number: Optional[str] = None,
    version_edition: Optional[str] = None,
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registers an acquired raw document artifact into documents.json
    and synchronizes provenance to source_registry.json.
    """
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Raw document file not found: {raw_file_path}")

    file_hash = compute_sha256(raw_file_path)
    file_size_bytes = raw_file_path.stat().st_size
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()
    try:
        rel_path = str(raw_file_path.relative_to(ROOT_DIR))
    except ValueError:
        rel_path = str(raw_file_path)

    # 1. Update documents.json
    documents: List[Dict[str, Any]] = []
    if DOCUMENTS_PATH.exists():
        try:
            with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
                documents = json.load(f)
        except json.JSONDecodeError:
            documents = []

    doc_record = {
        "document_id": document_id,
        "source_id": source_id,
        "file_name": raw_file_path.name,
        "file_path": rel_path,
        "file_sha256": file_hash,
        "file_size_bytes": file_size_bytes,
        "title": title,
        "standard_or_document_number": document_number,
        "version_edition": version_edition,
        "acquired_date": retrieval_timestamp,
        "status": "document_acquired",
        "notes": notes,
    }

    # Upsert in documents list
    doc_index = next((i for i, d in enumerate(documents) if d["document_id"] == document_id), -1)
    if doc_index >= 0:
        documents[doc_index] = doc_record
    else:
        documents.append(doc_record)

    with open(DOCUMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    # 2. Update source_registry.json
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)

        for item in registry:
            if item["source_id"] == source_id:
                item["document_id"] = document_id
                item["file_path"] = rel_path
                item["file_sha256"] = file_hash
                item["file_size_bytes"] = file_size_bytes
                item["retrieval_date"] = retrieval_timestamp
                item["status"] = "document_acquired"
                if source_url:
                    item["url"] = source_url
                if notes:
                    item["notes"] = notes
                break

        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    logger.info(
        "✅ Registered %s (Linked to %s): %s (SHA-256: %s...)",
        document_id,
        source_id,
        rel_path,
        file_hash[:16],
    )

    return doc_record
