"""
Automated Incremental Update Pipeline for BIS Documents (Steps 11 & 12).
Executes the selective knowledge update chain:
SHA-256 -> Change Gate -> Version Increment -> Phase 2C -> Phase 2D -> Semantic Diff -> Phase 2E -> Chunk Diff -> Vector DB Update Gate.
Avoids unnecessary model retraining by updating the RAG knowledge index incrementally.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.chunking.chunk_diff import ChunkDiffEngine
from ai.chunking.chunker import StructureAwareChunker
from ai.ingestion.change_detector import ChangeDetector, compute_sha256
from ai.ingestion.manifest import IngestionManifestManager
from ai.ingestion.processor import DocumentProcessor
from ai.ingestion.status import DocumentStatus
from ai.ingestion.versioning import DocumentVersion, make_version_id
from ai.processing.normalizer import DocumentNormalizer
from ai.versioning.semantic_diff import SemanticDiffEngine

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
NORMALIZED_DIR = DATA_DIR / "normalized"
CHUNKS_DIR = DATA_DIR / "chunks"
METADATA_DIR = DATA_DIR / "metadata"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"


class IncrementalUpdatePipeline:
    """Orchestrates end-to-end incremental standard updates through phases 2C -> 2D -> 2E."""

    def __init__(self):
        self.change_detector = ChangeDetector()
        self.doc_processor = DocumentProcessor()
        self.normalizer = DocumentNormalizer()
        self.chunker = StructureAwareChunker()
        self.semantic_diff_engine = SemanticDiffEngine()
        self.chunk_diff_engine = ChunkDiffEngine()
        self.manifest_manager = IngestionManifestManager()

    def process_updated_document(
        self,
        document_id: str,
        new_pdf_path: Path,
        version_label: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes the full Step 11 update chain for a changed or newly published document.
        """
        if not new_pdf_path.exists():
            raise FileNotFoundError(f"PDF file missing: {new_pdf_path}")

        new_hash = compute_sha256(new_pdf_path)
        file_size = new_pdf_path.stat().st_size
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 1: Change Detection
        change_report = self.change_detector.check_document_change(
            document_id, current_file_path=new_pdf_path, update_history=False
        )

        if not change_report.get("has_changed") and not force:
            logger.info("Document %s is unchanged (SHA: %s...). Skipping update.", document_id, new_hash[:12])
            return {
                "document_id": document_id,
                "status": DocumentStatus.UNCHANGED.value,
                "message": "Document content matches existing SHA-256 hash. Zero re-embedding needed.",
                "reembed_required_count": 0,
            }

        logger.info("🚀 Triggering incremental update pipeline for %s (New SHA: %s...)", document_id, new_hash[:12])

        # Step 2: Version Generation
        registry = []
        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)

        item = next((s for s in registry if s.get("document_id") == document_id), None)
        hist_len = len(item.get("history", [])) if item else 1
        new_version_id = make_version_id(document_id, hist_len + 1)
        source_id = item.get("source_id", "SRC-UNKNOWN") if item else "SRC-UNKNOWN"
        v_label = version_label or (item.get("standard_number", document_id) if item else document_id)

        # Step 3: Phase 2C - Page-Aware Extraction
        logger.info("▶️ [Phase 2C] Extracting canonical structure...")
        canonical_doc = self.doc_processor.process_document(document_id)

        # Step 4: Phase 2D - Semantic Normalization
        logger.info("▶️ [Phase 2D] Performing semantic normalization...")
        normalized_doc = self.normalizer.normalize_document(document_id)

        # Step 5: Semantic Diff against existing normalized version
        semantic_diff = {"has_semantic_changes": True, "total_changes_count": 0}
        old_norm_file = NORMALIZED_DIR / f"{document_id}.json"
        if old_norm_file.exists():
            try:
                with open(old_norm_file, "r", encoding="utf-8") as f:
                    old_norm_data = json.load(f)
                semantic_diff = self.semantic_diff_engine.compare_documents(old_norm_data, normalized_doc)
            except Exception as e:
                logger.warning("Could not compute semantic diff: %s", e)

        # Step 6: Load Old Chunks for Chunk-Level Diffing (Step 8)
        old_chunks = []
        old_chunks_file = CHUNKS_DIR / f"{document_id}.json"
        if old_chunks_file.exists():
            try:
                with open(old_chunks_file, "r", encoding="utf-8") as f:
                    old_chunks = json.load(f)
            except Exception:
                old_chunks = []

        # Step 7: Phase 2E - Structure-Aware Chunking with new Version ID
        logger.info("▶️ [Phase 2E] Generating structure-aware chunks with stable IDs...")
        new_chunks = self.chunker.chunk_document(document_id, version_id=new_version_id)

        # Step 8: Chunk-Level Diff
        chunk_diff = self.chunk_diff_engine.compare_chunk_sets(old_chunks, new_chunks)
        logger.info(
            "⚡ Chunk Diff Summary: %d unchanged (keep vectors), %d modified (re-embed), %d added (new vectors)",
            chunk_diff["unchanged_count"],
            chunk_diff["modified_count"],
            chunk_diff["added_count"],
        )

        # Step 9: Update Source Registry & Mark Historical Versions
        if item:
            if "history" not in item:
                item["history"] = []

            item["history"].append({
                "version_id": new_version_id,
                "sha256": new_hash,
                "file_size": file_size,
                "detected_at": now_iso,
                "change_type": "revision_update",
                "version_label": v_label,
            })

            item["current_version"] = {
                "version_id": new_version_id,
                "sha256": new_hash,
                "file_size": file_size,
                "last_modified": now_iso,
                "publication_date": item.get("publication_date"),
                "etag": None,
            }
            item["file_sha256"] = new_hash
            item["file_size_bytes"] = file_size
            item["status"] = DocumentStatus.CHUNKED.value

            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)

        # Step 10: Update Ingestion Manifest
        self.manifest_manager.generate_manifest()

        return {
            "document_id": document_id,
            "version_id": new_version_id,
            "source_id": source_id,
            "sha256": new_hash,
            "status": DocumentStatus.CHUNKED.value,
            "total_chunks": len(new_chunks),
            "semantic_diff": semantic_diff,
            "chunk_diff": chunk_diff,
            "reembed_required_count": chunk_diff["reembed_required_count"],
            "unchanged_chunks_count": chunk_diff["unchanged_count"],
            "ready_for_vector_db": True,
        }
