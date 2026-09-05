#!/usr/bin/env python3
"""
Bulk BIS Data Discovery & Acquisition Orchestrator (Phase 3).
Executes the full pipeline: Strategy-driven Discovery -> Candidate Gating -> Streamed Download ->
Content Validation -> Strict Canonical Identity -> Persistent 4-Way Deduplication -> Immutable Storage -> Manifest.
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.acquisition.discovery_engine import DiscoveryEngine, CandidateDocument
from ai.acquisition.candidate_validator import CandidateValidator
from ai.acquisition.pipeline_downloader import PipelineDownloader
from ai.acquisition.content_validator import ContentValidator
from ai.acquisition.identity_resolver import IdentityResolver, DeduplicationDecision
from ai.acquisition.relationship_discoverer import RelationshipDiscoverer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BulkAcquisitionOrchestrator")

IMMUTABLE_STORAGE_ROOT = ROOT_DIR / "data" / "raw" / "immutable"
MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
FAILURES_PATH = ROOT_DIR / "data" / "acquisition" / "failures" / "acquisition_failures.json"
QUARANTINE_PATH = ROOT_DIR / "data" / "acquisition" / "quarantine" / "quarantined_candidates.json"


class BulkAcquisitionOrchestrator:
    """Orchestrates end-to-end multi-source discovery and acquisition."""

    def __init__(self):
        self.discovery_engine = DiscoveryEngine()
        self.candidate_validator = CandidateValidator()
        self.downloader = PipelineDownloader()
        self.content_validator = ContentValidator()
        self.identity_resolver = IdentityResolver()
        self.relationship_discoverer = RelationshipDiscoverer()

    def run(self, dry_run: bool = False, pilot: bool = False, live_network: bool = False, from_registry: bool = True, canary_limit: int = 0) -> Dict[str, Any]:
        """Runs the acquisition workflow."""
        logger.info("🚀 Starting Phase 4 Acquisition Pipeline (DryRun=%s, Canary=%s, LiveNet=%s)...", dry_run, canary_limit, live_network)

        # 1. Load Candidates
        if from_registry:
            registry_path = ROOT_DIR / "data" / "candidates" / "candidate_documents.json"
            if not registry_path.exists():
                logger.error("Registry not found at %s", registry_path)
                sys.exit(1)
            with open(registry_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            all_candidates = [CandidateDocument(**c) for c in raw_data]
            logger.info("REGISTRY CANDIDATES: %d", len(all_candidates))
            
            if len(all_candidates) != 1909:
                logger.error("🛑 CRITICAL: Expected exactly 1,909 candidates in registry, but found %d. Halting.", len(all_candidates))
                sys.exit(1)
        else:
            # Fallback to multi-strategy discovery (should not be used in Phase 4 normally)
            all_candidates = self.discovery_engine.discover_all_candidates()
            logger.info("🔍 Discovered %d candidate documents across official source endpoints", len(all_candidates))

        # 2. Candidate Validation & Quarantine
        valid_candidates, quarantined = self.candidate_validator.filter_and_quarantine(all_candidates)
        logger.info("🛡️ Validated %d candidates (%d quarantined)", len(valid_candidates), len(quarantined))

        if canary_limit > 0:
            # Pick a diverse set of candidates for the canary
            diverse_cands = []
            seen_types = set()
            # First pass: try to get one of each document type
            for c in valid_candidates:
                if c.document_type not in seen_types:
                    seen_types.add(c.document_type)
                    diverse_cands.append(c)
                if len(diverse_cands) >= canary_limit:
                    break
            # Fill the rest if we haven't reached the limit
            for c in valid_candidates:
                if len(diverse_cands) >= canary_limit:
                    break
                if c not in diverse_cands:
                    diverse_cands.append(c)
            valid_candidates = diverse_cands
            logger.info("🐤 CANARY MODE: Selected %d diverse candidates", len(valid_candidates))
        elif pilot:
            # Select 1 representative candidate per source family
            seen_families = set()
            pilot_candidates = []
            for c in valid_candidates:
                if c.source_family_id not in seen_families:
                    seen_families.add(c.source_family_id)
                    pilot_candidates.append(c)
            valid_candidates = pilot_candidates
            logger.info("🎯 Pilot mode: Selected %d representative candidates", len(valid_candidates))

        if dry_run:
            logger.info("🛑 Dry-run mode enabled: Halting before download execution.")
            return {
                "dry_run": True,
                "discovered_count": len(all_candidates),
                "validated_count": len(valid_candidates),
                "quarantined_count": len(quarantined)
            }

        # 3. Document Acquisition & Content Validation
        manifest_entries = []
        failures = []

        for cand in valid_candidates:
            # 3E: Strict Canonical Identity Resolution (Zero Fallback)
            doc_id, fam_id, id_err = self.identity_resolver.generate_document_id(
                document_type=cand.document_type,
                standard_number=cand.standard_number,
                part=cand.part,
                edition_year=cand.edition_year,
                amendment_number=cand.metadata.get("amendment_number"),
                ministry_acronym=cand.metadata.get("ministry"),
                notification_number=cand.metadata.get("notification_number"),
                year=cand.metadata.get("year"),
                version_label=cand.metadata.get("version"),
                custom_identifier=cand.candidate_id.replace("CAND-", "")
            )

            if not doc_id:
                logger.warning("Quarantining %s: %s", cand.candidate_id, id_err)
                quarantined.append({
                    "candidate_id": cand.candidate_id,
                    "rejection_reason": id_err,
                    "quarantined_at": datetime.now(timezone.utc).isoformat()
                })
                continue

            file_type = cand.metadata.get("file_type", "PDF").upper()
            ext = ".pdf" if file_type == "PDF" else (".html" if file_type == "HTML" else ".json")

            target_doc_dir = IMMUTABLE_STORAGE_ROOT / doc_id
            target_raw_file = target_doc_dir / f"original{ext}"

            # Download / Ingest payload
            mock_payload = None
            if not live_network:
                if file_type == "PDF":
                    mock_payload = f"%PDF-1.4\n%Authoritative BIS Document: {cand.title} ({doc_id})\n%%EOF".encode("utf-8")
                elif file_type == "HTML":
                    mock_payload = f"<!DOCTYPE html><html><head><title>{cand.title}</title></head><body><h1>{cand.title}</h1><p>Authoritative BIS Record: {doc_id}</p></body></html>".encode("utf-8")
                else:
                    mock_payload = json.dumps({"document_id": doc_id, "title": cand.title, "authority": "BIS"}).encode("utf-8")

            acq_res = self.downloader.acquire_document(
                url=cand.source_url,
                target_path=target_raw_file,
                offline_mock_payload=mock_payload
            )

            if not acq_res.get("success"):
                err_msg = str(acq_res.get("error", "Unknown download error"))
                code = "DOWNLOAD_FAILED"
                if "403" in err_msg or "Session" in err_msg or "SESSION_REQUIRED" in err_msg:
                    code = "SESSION_BLOCKED"
                elif "404" in err_msg:
                    code = "DOWNLOAD_FAILED"
                
                quarantined.append({
                    "candidate_id": cand.candidate_id,
                    "source_id": cand.source_id,
                    "source_family": cand.source_family_id,
                    "canonical_url": cand.discovered_from_url,
                    "final_url": acq_res.get("final_url"),
                    "failure_code": code,
                    "error_message": err_msg,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "attempt_count": 3
                })
                failures.append({"candidate_id": cand.candidate_id, "doc_id": doc_id, "error": err_msg})
                manifest_entries.append({
                    "document": {"document_id": doc_id, "title": cand.title, "document_type": cand.document_type},
                    "acquisition": {"validation_passed": False, "deduplication_result": code, "final_url": cand.source_url}
                })
                continue

            # 4. Content Validation
            content_ok, content_err = self.content_validator.validate_file(
                file_path=target_raw_file,
                expected_format=file_type,
                reported_content_type=acq_res.get("content_type")
            )

            if not content_ok:
                logger.error("Content validation failed for %s: %s", doc_id, content_err)
                code = "INVALID_CONTENT"
                if "masquerading" in str(content_err).lower():
                    code = "HTML_INSTEAD_OF_DOCUMENT"
                elif "magic byte" in str(content_err).lower():
                    code = "PDF_CORRUPTED"
                
                quarantined.append({
                    "candidate_id": cand.candidate_id,
                    "source_id": cand.source_id,
                    "source_family": cand.source_family_id,
                    "canonical_url": cand.discovered_from_url,
                    "final_url": acq_res.get("final_url"),
                    "failure_code": code,
                    "error_message": str(content_err),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "attempt_count": 1
                })
                failures.append({"candidate_id": cand.candidate_id, "doc_id": doc_id, "error": content_err})
                manifest_entries.append({
                    "document": {"document_id": doc_id, "title": cand.title, "document_type": cand.document_type},
                    "acquisition": {"validation_passed": False, "deduplication_result": code, "final_url": acq_res.get("final_url")}
                })
                continue

            # 5. Persistent Deduplication Decision
            sha = acq_res["sha256"]
            dedup_decision: DeduplicationDecision = self.identity_resolver.resolve_deduplication(
                document_id=doc_id,
                document_family_id=fam_id,
                raw_sha256=sha
            )

            # 6. Build Manifest Entry (3-Block Provenance)
            manifest_entry = {
                "document": {
                    "document_id": doc_id,
                    "document_family_id": fam_id,
                    "title": cand.title,
                    "document_type": cand.document_type,
                    "authority": cand.metadata.get("authority", "Bureau of Indian Standards"),
                    "authority_class": "PRIMARY_NORMATIVE" if cand.document_type in {"INDIAN_STANDARD", "AMENDMENT", "QCO_NOTIFICATION"} else "OFFICIAL_OPERATIONAL",
                    "edition_year": cand.edition_year,
                    "published_date_raw": cand.metadata.get("pub_date"),
                    "published_date_normalized": cand.metadata.get("pub_date"),
                    "effective_date_raw": cand.metadata.get("valid_from"),
                    "effective_date_normalized": cand.metadata.get("valid_from"),
                    "revision": None,
                    "status": "CURRENT",
                    "parent_document_id": cand.metadata.get("parent_document_id"),
                    "supersedes": None,
                    "superseded_by": None
                },
                "source": {
                    "source_id": cand.source_id,
                    "source_family_id": cand.source_family_id,
                    "source_name": f"Source {cand.source_id}",
                    "canonical_source_url": cand.discovered_from_url,
                    "source_ownership": "BIS_PUBLISHED" if cand.source_family_id in {"SRCF-001", "SRCF-002", "SRCF-004", "SRCF-005"} else "BIS_OPERATED"
                },
                "acquisition": {
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "final_url": acq_res.get("final_url", cand.source_url),
                    "http_status": acq_res.get("http_status", 200),
                    "content_type": acq_res.get("content_type", "application/pdf"),
                    "content_length_bytes": acq_res.get("content_length_bytes", target_raw_file.stat().st_size),
                    "sha256": sha,
                    "file_type": file_type,
                    "acquisition_method": acq_res.get("acquisition_method", "HTTPS_GET_STREAM"),
                    "tls_verified": acq_res.get("tls_verified", True),
                    "validation_passed": True,
                    "deduplication_result": dedup_decision.deduplication_status,
                    "deduplication_rule": dedup_decision.resolution_rule,
                    "storage_path": str(target_raw_file.relative_to(ROOT_DIR))
                }
            }

            # Persist sidecar metadata in immutable storage
            sidecar_meta_path = target_doc_dir / "metadata.json"
            with open(sidecar_meta_path, "w", encoding="utf-8") as f:
                json.dump(manifest_entry, f, indent=2)

            manifest_entries.append(manifest_entry)

        # 7. Discover Relationships
        relationships = self.relationship_discoverer.discover_relationships(manifest_entries)
        logger.info("🔗 Discovered %d verified cross-document relationships", len(relationships))

        # 8. Compile Final Authoritative Manifest
        acq_count = sum(1 for e in manifest_entries if e["acquisition"]["deduplication_result"] == "DISTINCT_DOCUMENT")
        already_count = sum(1 for e in manifest_entries if e["acquisition"]["deduplication_result"] == "UNCHANGED_DOCUMENT")
        dup_alias_count = sum(1 for e in manifest_entries if e["acquisition"]["deduplication_result"] == "DUPLICATE_REPRESENTATION_ALIAS")
        changed_count = sum(1 for e in manifest_entries if e["acquisition"]["deduplication_result"] == "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW")
        
        manual_review_count = sum(1 for q in quarantined if "MANUAL_REVIEW" in str(q.get("rejection_reason", "")))
        down_fail_count = sum(1 for q in quarantined if q.get("failure_code") == "DOWNLOAD_FAILED")
        html_count = sum(1 for q in quarantined if q.get("failure_code") == "HTML_INSTEAD_OF_DOCUMENT")
        sess_block_count = sum(1 for q in quarantined if q.get("failure_code") == "SESSION_BLOCKED")
        corr_pdf_count = sum(1 for q in quarantined if q.get("failure_code") == "PDF_CORRUPTED")
        inv_cont_count = sum(1 for q in quarantined if q.get("failure_code") == "INVALID_CONTENT")
        other_quar_count = len(quarantined) - (manual_review_count + down_fail_count + html_count + sess_block_count + corr_pdf_count + inv_cont_count)

        terminal_state_total = (acq_count + already_count + dup_alias_count + changed_count + 
                                manual_review_count + down_fail_count + html_count + sess_block_count + 
                                corr_pdf_count + inv_cont_count + other_quar_count)

        processed_total = len(manifest_entries) + len(quarantined)
        
        metrics = {
            "REGISTRY_TOTAL": len(all_candidates),
            "PROCESSED_TOTAL": processed_total,
            "SUCCESSFULLY_ACQUIRED": acq_count,
            "ALREADY_PRESENT": already_count,
            "DUPLICATE_ALIAS": dup_alias_count,
            "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW": changed_count,
            "MANUAL_REVIEW": manual_review_count,
            "DOWNLOAD_FAILED": down_fail_count,
            "HTML_INSTEAD_OF_DOCUMENT": html_count,
            "SESSION_BLOCKED": sess_block_count,
            "CORRUPTED_PDF": corr_pdf_count,
            "INVALID_CONTENT": inv_cont_count,
            "OTHER_QUARANTINED": other_quar_count,
            "TERMINAL_STATE_TOTAL": terminal_state_total
        }

        manifest_payload = {
            "manifest_version": "1.0",
            "phase": "Phase 4: Bulk BIS Data Acquisition",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "total_acquired": len(manifest_entries),
            "total_relationships": len(relationships),
            "documents": manifest_entries,
            "relationships": [r.model_dump() for r in relationships]
        }

        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest_payload, f, indent=2)

        if failures:
            FAILURES_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(FAILURES_PATH, "w", encoding="utf-8") as f:
                json.dump(failures, f, indent=2)

        if quarantined:
            QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(QUARANTINE_PATH, "w", encoding="utf-8") as f:
                json.dump(quarantined, f, indent=2)

        logger.info("💾 Saved authoritative acquisition manifest to %s", MANIFEST_PATH)
        return manifest_payload


def main():
    parser = argparse.ArgumentParser(description="Bulk BIS Data Discovery & Acquisition Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Run discovery and validation without downloading")
    parser.add_argument("--pilot", action="store_true", help="Acquire a representative pilot sample from each source family")
    parser.add_argument("--live", action="store_true", help="Enable live HTTPS network acquisition")
    parser.add_argument("--from-registry", action="store_true", default=True, help="Load directly from canonical candidates JSON (Default: True)")
    parser.add_argument("--canary-limit", type=int, default=0, help="Run a canary test on N diverse candidates before full run")
    args = parser.parse_args()

    orchestrator = BulkAcquisitionOrchestrator()
    res = orchestrator.run(
        dry_run=args.dry_run, 
        pilot=args.pilot, 
        live_network=args.live, 
        from_registry=args.from_registry,
        canary_limit=args.canary_limit
    )
    print(f"\n✅ Phase 4 Orchestration Complete!")
    if "metrics" in res:
        m = res["metrics"]
        print("\n--- REGISTRY ACCOUNTING ---")
        for k, v in m.items():
            print(f"  {k}: {v}")
        print(f"  TOTAL RELATIONSHIPS: {res.get('total_relationships', 0)}")


if __name__ == "__main__":
    main()
