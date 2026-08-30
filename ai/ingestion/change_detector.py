"""
Data Freshness and Change Detection Gate for BIS Ingestion Pipeline.
Detects modifications, version increments, and hash changes across acquired documents
to trigger selective, incremental re-processing (2C -> 2D -> 2E) without unnecessary retraining.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ChangeDetector:
    """Detects content modifications, new editions, and hash discrepancies across source documents."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path

    def _load_registry(self) -> List[Dict[str, Any]]:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Source registry missing: {self.registry_path}")
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_registry(self, registry: List[Dict[str, Any]]):
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    def check_document_change(
        self,
        document_id: str,
        current_file_path: Optional[Path] = None,
        update_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Checks if a specific document's physical file has changed against registry metadata.
        Returns a change report dict.
        """
        registry = self._load_registry()
        item = next((s for s in registry if s.get("document_id") == document_id), None)

        if not item:
            return {
                "document_id": document_id,
                "has_changed": True,
                "change_type": "unregistered_document",
                "action_required": "register_and_process",
            }

        cur_ver = item.get("current_version", {})
        known_hash = cur_ver.get("sha256") or item.get("file_sha256")

        target_path = current_file_path or (ROOT_DIR / item.get("local_path", ""))
        if not target_path or not target_path.exists():
            return {
                "document_id": document_id,
                "has_changed": False,
                "status": "file_missing",
                "action_required": "acquire_file",
            }

        actual_hash = compute_sha256(target_path)
        actual_size = target_path.stat().st_size

        if actual_hash == known_hash:
            logger.info("Document %s is unchanged (SHA-256: %s...)", document_id, actual_hash[:12])
            return {
                "document_id": document_id,
                "source_id": item.get("source_id"),
                "has_changed": False,
                "change_type": "identical",
                "current_hash": actual_hash,
                "previous_hash": known_hash,
                "action_required": "none",
            }

        # Document has changed!
        logger.warning(
            "⚠️ Change detected in %s! Known hash: %s... vs Actual: %s...",
            document_id,
            str(known_hash)[:12],
            actual_hash[:12],
        )

        if update_history:
            now_iso = datetime.now(timezone.utc).isoformat()
            if "history" not in item:
                item["history"] = []

            item["history"].append({
                "sha256": actual_hash,
                "file_size": actual_size,
                "detected_at": now_iso,
                "change_type": "content_update",
                "previous_sha256": known_hash,
            })

            item["current_version"] = {
                "sha256": actual_hash,
                "file_size": actual_size,
                "last_modified": now_iso,
                "publication_date": item.get("publication_date"),
                "etag": cur_ver.get("etag"),
            }
            item["file_sha256"] = actual_hash
            item["file_size_bytes"] = actual_size
            item["status"] = "content_modified"

            self._save_registry(registry)

        return {
            "document_id": document_id,
            "source_id": item.get("source_id"),
            "has_changed": True,
            "change_type": "content_update",
            "current_hash": actual_hash,
            "previous_hash": known_hash,
            "action_required": "reprocess_and_reembed",
        }

    def scan_all_sources(self) -> Dict[str, Any]:
        """
        Scans all registered documents and returns a summary of changed vs unchanged documents.
        """
        registry = self._load_registry()
        results: Dict[str, Any] = {
            "scanned_count": 0,
            "changed_count": 0,
            "unchanged_count": 0,
            "missing_count": 0,
            "details": [],
        }

        for item in registry:
            doc_id = item.get("document_id")
            if not doc_id:
                continue

            report = self.check_document_change(doc_id, update_history=False)
            results["scanned_count"] += 1
            if report.get("status") == "file_missing":
                results["missing_count"] += 1
            elif report.get("has_changed"):
                results["changed_count"] += 1
            else:
                results["unchanged_count"] += 1

            results["details"].append(report)

        return results


def check_source_freshness() -> Dict[str, Any]:
    """Convenience helper function to scan all sources."""
    detector = ChangeDetector()
    return detector.scan_all_sources()
