"""
Source Registry Freshness Extender.
Enhances data/metadata/source_registry.json with structured current_version,
file metadata, and historical change audit logs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"


def upgrade_source_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    doc_map = {d["document_id"]: d for d in documents}

    for item in registry:
        doc_id = item.get("document_id")
        doc_info = doc_map.get(doc_id, {}) if doc_id else {}

        file_path = item.get("file_path") or doc_info.get("file_path")
        sha256 = item.get("file_sha256") or doc_info.get("file_sha256")
        file_size = item.get("file_size_bytes") or doc_info.get("file_size_bytes", 0)
        pub_date = item.get("publication_date")
        ret_date = item.get("retrieval_date") or datetime.now(timezone.utc).isoformat()

        # Build current_version block
        item["current_version"] = {
            "sha256": sha256,
            "file_size": file_size,
            "last_modified": ret_date,
            "publication_date": pub_date,
            "etag": None,
        }

        # Build history audit trail
        if "history" not in item or not item["history"]:
            item["history"] = [
                {
                    "sha256": sha256,
                    "detected_at": ret_date,
                    "change_type": "initial_ingestion",
                }
            ]

        # Standardize local_path
        if file_path:
            item["local_path"] = file_path

        # Standardize standard_number
        if "standard_or_document_number" in item and "standard_number" not in item:
            item["standard_number"] = item["standard_or_document_number"]

        if "url" in item and "source_url" not in item:
            item["source_url"] = item["url"]

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✅ Source registry upgraded with version & freshness metadata for {len(registry)} sources.")


if __name__ == "__main__":
    upgrade_source_registry()
