"""
Ingestion Manifest Manager (Step 10).
Creates, updates, and audits data/metadata/ingestion_manifest.json
to provide a persistent operational audit trail of ingestion and indexing lifecycle states.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.ingestion.status import DocumentStatus

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = ROOT_DIR / "data" / "metadata" / "ingestion_manifest.json"
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"


class IngestionManifestManager:
    """Manages data/metadata/ingestion_manifest.json tracking lifecycle state and change audits."""

    def __init__(self, manifest_path: Path = MANIFEST_PATH):
        self.manifest_path = manifest_path

    def load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "pipeline_version": "1.0.0",
                "total_documents": 0,
                "documents": {},
            }
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_manifest(self, manifest: Dict[str, Any]):
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def generate_manifest(self) -> Dict[str, Any]:
        """Scans current pipeline artifacts and generates an up-to-date ingestion manifest."""
        manifest = self.load_manifest()
        now_iso = datetime.now(timezone.utc).isoformat()
        manifest["last_run"] = now_iso

        if not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(f"Documents manifest missing: {DOCUMENTS_PATH}")

        with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
            doc_list = json.load(f)

        reg_map = {}
        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
                reg_map = {r.get("document_id"): r for r in registry if r.get("document_id")}

        doc_entries: Dict[str, Any] = {}

        for doc in doc_list:
            doc_id = doc["document_id"]
            src_id = doc["source_id"]
            std_num = doc.get("standard_or_document_number") or doc.get("title", doc_id)
            cur_hash = doc.get("file_sha256")

            # Check if chunk file exists
            chunk_file = CHUNKS_DIR / f"{doc_id}.json"
            total_chunks = 0
            if chunk_file.exists():
                try:
                    with open(chunk_file, "r", encoding="utf-8") as cf:
                        chunks_data = json.load(cf)
                        total_chunks = len(chunks_data)
                except Exception:
                    total_chunks = 0

            prev_entry = manifest.get("documents", {}).get(doc_id, {})
            prev_hash = prev_entry.get("current_hash") or cur_hash

            status = DocumentStatus.CHUNKED.value if total_chunks > 0 else DocumentStatus.NORMALIZED.value

            doc_entries[doc_id] = {
                "source_id": src_id,
                "standard_number": std_num,
                "current_hash": cur_hash,
                "previous_hash": prev_hash,
                "last_checked": now_iso,
                "status": status,
                "total_chunks": total_chunks,
                "requires_reindex": cur_hash != prev_hash,
            }

        manifest["total_documents"] = len(doc_entries)
        manifest["documents"] = doc_entries

        self.save_manifest(manifest)
        logger.info("✅ Ingestion manifest saved with %d documents -> %s", len(doc_entries), self.manifest_path)
        return manifest


def update_ingestion_manifest() -> Dict[str, Any]:
    """Convenience helper function to refresh ingestion manifest."""
    manager = IngestionManifestManager()
    return manager.generate_manifest()
