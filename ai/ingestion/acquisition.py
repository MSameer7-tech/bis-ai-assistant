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


def register_source(
    source_id: str,
    standard_or_document_number: str,
    title: str,
    product_domain: str,
    category: Optional[str] = None,
    product_type: Optional[str] = None,
    issuing_authority: Optional[str] = None,
    version_edition: Optional[str] = None,
    publication_date: Optional[str] = None,
    valid_from: Optional[str] = None,
    valid_until: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Registers a new source entry in source_registry.json."""
    if not REGISTRY_PATH.exists():
        registry = []
    else:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            try:
                registry = json.load(f)
            except json.JSONDecodeError:
                registry = []

    source_entry = next((s for s in registry if s["source_id"] == source_id), None)
    if source_entry is None:
        now_iso = datetime.now(timezone.utc).isoformat()
        v_id = f"{source_id}-v001"
        source_entry = {
            "source_id": source_id,
            "domain": "Standards",
            "product_domain": product_domain,
            "category": category,
            "product_type": product_type,
            "source_type": "standard_document",
            "issuing_authority": issuing_authority or "Bureau of Indian Standards",
            "authority_level": "Tier 1B - Normative",
            "title": title,
            "standard_or_document_number": standard_or_document_number,
            "version_edition": version_edition or "First Edition",
            "publication_date": publication_date,
            "effective_date": valid_from,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "url": url,
            "retrieval_date": now_iso,
            "status": "REGISTERED",
            "notes": notes or "Discovered BIS Standard source",
            "current_version": {
                "version_id": v_id,
                "sha256": None,
                "file_size": None,
                "last_modified": now_iso,
                "publication_date": publication_date,
                "etag": None,
            },
            "history": [
                {
                    "version_id": v_id,
                    "sha256": None,
                    "file_size": None,
                    "detected_at": now_iso,
                    "change_type": "initial_registration",
                    "version_label": standard_or_document_number,
                }
            ],
        }
        registry.append(source_entry)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    return source_entry


def register_acquired_document(
    document_id: str,
    source_id: str,
    raw_file_path: Path,
    title: Optional[str] = None,
    document_number: Optional[str] = None,
    version_edition: Optional[str] = None,
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
    product_domain: Optional[str] = None,
    category: Optional[str] = None,
    product_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registers an acquired raw document artifact into documents.json
    and synchronizes provenance to source_registry.json.
    Strictly verifies that raw_file_path exists.
    """
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Raw document file not found: {raw_file_path}")

    if not REGISTRY_PATH.exists():
        registry = []
    else:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)

    # Validate or create source_id in registry
    source_match = next((item for item in registry if item["source_id"] == source_id), None)
    if source_match is None:
        source_match = {
            "source_id": source_id,
            "domain": "Standards",
            "product_domain": product_domain or "electrical",
            "category": category,
            "product_type": product_type,
            "source_type": "standard_document",
            "issuing_authority": "Bureau of Indian Standards",
            "authority_level": "Tier 1B - Normative",
            "title": title or document_number,
            "standard_or_document_number": document_number or title,
            "version_edition": version_edition or "First Edition",
            "publication_date": None,
            "effective_date": None,
            "url": source_url,
            "retrieval_date": datetime.now(timezone.utc).isoformat(),
            "status": "document_acquired",
            "notes": notes or "Official Indian Standard PDF acquired",
        }
        registry.append(source_match)

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
        "title": title or source_match.get("title"),
        "standard_or_document_number": document_number or source_match.get("standard_or_document_number"),
        "version_edition": version_edition or source_match.get("version_edition"),
        "acquired_date": retrieval_timestamp,
        "status": "document_acquired",
        "notes": notes or source_match.get("notes"),
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
    source_match["document_id"] = document_id
    source_match["file_path"] = rel_path
    source_match["file_sha256"] = file_hash
    source_match["file_size_bytes"] = file_size_bytes
    source_match["retrieval_date"] = retrieval_timestamp
    source_match["status"] = "document_acquired"
    if source_url:
        source_match["url"] = source_url
    if notes:
        source_match["notes"] = notes

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
