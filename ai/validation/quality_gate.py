"""
Phase 5D: Dataset Quality Gate, Lifecycle State Machine, and Manifest Generator.
Audits documents through 10-stage quality lifecycle:
DISCOVERED -> DOWNLOADED -> EXTRACTED -> CONTENT_VERIFIED -> NORMALIZED ->
SEMANTIC_VERIFIED -> CHUNKED -> CHUNKING_VERIFIED -> INDEXED -> AVAILABLE_TO_RAG
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
METADATA_DIR = ROOT_DIR / "data" / "metadata"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"

REGISTRY_PATH = METADATA_DIR / "source_registry.json"
DOCUMENTS_PATH = METADATA_DIR / "documents.json"
MANIFEST_PATH = METADATA_DIR / "dataset_manifest.json"
QUALITY_LOG_PATH = METADATA_DIR / "quality_gate_log.json"


class DocumentLifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    DOWNLOADED = "DOWNLOADED"
    EXTRACTED = "EXTRACTED"
    CONTENT_VERIFIED = "CONTENT_VERIFIED"
    NORMALIZED = "NORMALIZED"
    SEMANTIC_VERIFIED = "SEMANTIC_VERIFIED"
    CHUNKED = "CHUNKED"
    CHUNKING_VERIFIED = "CHUNKING_VERIFIED"
    INDEXED = "INDEXED"
    AVAILABLE_TO_RAG = "AVAILABLE_TO_RAG"
    REJECTED = "REJECTED"


class DatasetQualityGate:
    """Audits documents against strict quality gates and produces dataset_manifest.json."""

    def __init__(self):
        METADATA_DIR.mkdir(parents=True, exist_ok=True)

    def audit_document(self, document_id: str) -> Dict[str, Any]:
        """
        Runs comprehensive validation across extraction, normalization, and chunking stages.
        Returns audit report with passed flag, final lifecycle state, and risk flags.
        """
        issues: List[str] = []
        risk_flags: List[str] = []

        # 1. Check Raw / Processed File
        proc_file = PROCESSED_DIR / f"{document_id}.json"
        if not proc_file.exists():
            return {
                "document_id": document_id,
                "passed": False,
                "state": DocumentLifecycleState.REJECTED.value,
                "reason": f"Missing processed file: {proc_file}",
                "risk_flags": ["MISSING_PROCESSED"]
            }

        with open(proc_file, "r", encoding="utf-8") as f:
            proc_doc = json.load(f)

        if not proc_doc.get("clauses") and not proc_doc.get("pages"):
            issues.append("Document has 0 clauses and 0 pages.")

        # 2. Check Normalized File
        norm_file = NORMALIZED_DIR / f"{document_id}.json"
        if not norm_file.exists():
            norm_file = NORMALIZED_DIR / f"{document_id}.normalized.json"

        if not norm_file.exists():
            return {
                "document_id": document_id,
                "passed": False,
                "state": DocumentLifecycleState.EXTRACTED.value,
                "reason": "Missing normalized file",
                "risk_flags": ["MISSING_NORMALIZED"]
            }

        with open(norm_file, "r", encoding="utf-8") as f:
            norm_doc = json.load(f)

        entities = norm_doc.get("entities", [])
        if not entities:
            risk_flags.append("LOW_ENTITY_COUNT")

        # 3. Check Chunks File
        chunks_file = CHUNKS_DIR / f"{document_id}.json"
        if not chunks_file.exists():
            chunks_file = CHUNKS_DIR / f"{document_id}.chunks.json"

        if not chunks_file.exists():
            return {
                "document_id": document_id,
                "passed": False,
                "state": DocumentLifecycleState.SEMANTIC_VERIFIED.value,
                "reason": "Missing chunk file",
                "risk_flags": ["MISSING_CHUNKS"]
            }

        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        if not chunks:
            issues.append("0 chunks generated")

        for idx, c in enumerate(chunks):
            if not c.get("chunk_id"):
                issues.append(f"Chunk {idx} missing chunk_id")
            if not c.get("text"):
                issues.append(f"Chunk {idx} missing text content")
            if not c.get("content_hash"):
                issues.append(f"Chunk {idx} missing content_hash")
            if not c.get("provenance", {}).get("document_id"):
                issues.append(f"Chunk {idx} missing document_id in provenance")

        # Risk Analysis for Manual Review Queue
        std_title = proc_doc.get("document_metadata", {}).get("title", "")
        if "Revision" in std_title or "revision" in str(proc_doc.get("document_metadata", {}).get("edition", "")).lower():
            risk_flags.append("NEW_REVISION")
        if "Amendment" in std_title or "amendment" in std_title.lower():
            risk_flags.append("AMENDMENT")
        if any(c.get("chunk_type") == "table" for c in chunks):
            risk_flags.append("CONTAINS_TABLES")
        if any(c.get("normative_force") == "under_consideration" for c in chunks):
            risk_flags.append("PROVISIONAL_REQUIREMENTS")

        passed = len(issues) == 0
        final_state = DocumentLifecycleState.CHUNKING_VERIFIED.value if passed else DocumentLifecycleState.REJECTED.value

        return {
            "document_id": document_id,
            "passed": passed,
            "state": final_state,
            "issues": issues,
            "risk_flags": risk_flags,
            "total_clauses": len(proc_doc.get("clauses", [])),
            "total_entities": len(entities),
            "total_chunks": len(chunks)
        }

    def run_full_quality_audit(self) -> Dict[str, Any]:
        """Runs quality gate across all registered documents and generates dataset_manifest.json."""
        if not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(f"Documents manifest missing: {DOCUMENTS_PATH}")

        with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
            docs = json.load(f)

        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)

        audit_results: List[Dict[str, Any]] = []
        verified_count = 0
        rejected_count = 0
        manual_review_queue: List[Dict[str, Any]] = []

        total_chunks = 0
        product_domain_counts: Dict[str, int] = {}
        source_hashes: Dict[str, str] = {}

        for doc in docs:
            doc_id = doc["document_id"]
            report = self.audit_document(doc_id)
            audit_results.append(report)

            if report["passed"]:
                verified_count += 1
                total_chunks += report["total_chunks"]
            else:
                rejected_count += 1

            if report["risk_flags"]:
                manual_review_queue.append({
                    "document_id": doc_id,
                    "title": doc.get("title"),
                    "risk_flags": report["risk_flags"]
                })

            # Domain breakdown
            domain = doc.get("product_domain", "electrical")
            product_domain_counts[domain] = product_domain_counts.get(domain, 0) + 1
            if doc.get("file_sha256"):
                source_hashes[doc_id] = doc["file_sha256"]

        # Generate dataset_manifest.json
        now_iso = datetime.now(timezone.utc).isoformat()
        manifest_data = {
            "dataset_version": "1.0.0",
            "generated_at": now_iso,
            "documents": len(docs),
            "verified_documents": verified_count,
            "rejected_documents": rejected_count,
            "product_domains": product_domain_counts,
            "total_chunks": total_chunks,
            "total_indexed_chunks": total_chunks,
            "source_hashes": source_hashes,
            "pipeline_version": "2.0.0",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "quality_gate_status": "PASSED" if rejected_count == 0 else "WARNING",
            "manual_review_sample_queue_size": len(manual_review_queue),
            "manual_review_samples": manual_review_queue[:10]
        }

        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        with open(QUALITY_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "audited_at": now_iso,
                "total_documents": len(docs),
                "verified": verified_count,
                "rejected": rejected_count,
                "manual_review_queue": manual_review_queue,
                "document_reports": audit_results
            }, f, indent=2, ensure_ascii=False)

        logger.info("Quality Gate Audit Complete: %d/%d passed, %d chunks verified across %d domains.",
                    verified_count, len(docs), total_chunks, len(product_domain_counts))
        return manifest_data


if __name__ == "__main__":
    gate = DatasetQualityGate()
    gate.run_full_quality_audit()
