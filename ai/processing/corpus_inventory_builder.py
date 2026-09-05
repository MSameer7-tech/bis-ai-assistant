#!/usr/bin/env python3
"""
Phase 5 Extraction Readiness: Corpus Inventory Builder.
Freezes the acquisition baseline and creates a machine-readable extraction inventory.
Enforces the mandatory preservation of all MANUAL_REVIEW backlog candidates.
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CorpusInventoryBuilder")

ACQ_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
CORPUS_INVENTORY_PATH = ROOT_DIR / "data" / "processed" / "corpus_inventory.json"


def build_inventory():
    if not ACQ_MANIFEST_PATH.exists():
        logger.error("❌ Acquisition manifest not found at %s", ACQ_MANIFEST_PATH)
        sys.exit(1)

    logger.info("Reading acquisition baseline from %s", ACQ_MANIFEST_PATH)
    with open(ACQ_MANIFEST_PATH, "r", encoding="utf-8") as f:
        acq_data = json.load(f)

    metrics = acq_data.get("metrics", {})
    acq_docs = acq_data.get("documents", [])

    # The 229-Document Check
    expected_manual_review = 229
    actual_acq_manual_review = metrics.get("MANUAL_REVIEW", 0)
    
    if actual_acq_manual_review != expected_manual_review:
        logger.warning(
            "⚠️ Expected %d ACQUISITION_MANUAL_REVIEW items in metrics, but found %d. Proceeding based on actual manifest content.",
            expected_manual_review, actual_acq_manual_review
        )

    # We need to build the inventory
    inventory = {
        "metadata": {
            "inventory_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(ACQ_MANIFEST_PATH),
            "source_manifest_documents": len(acq_docs),
        },
        "inventory": []
    }

    # Groupings
    categorized = {
        "SUCCESSFULLY_ACQUIRED": [],
        "ALREADY_PRESENT": [],
        "MANUAL_REVIEW": [],
        "DOWNLOAD_FAILED": [],
        "HTML_INSTEAD_OF_DOCUMENT": [],
        "SESSION_BLOCKED": [],
        "OTHER_QUARANTINED": []
    }

    extractable_count = 0

    for doc in acq_docs:
        acq_info = doc.get("acquisition", {})
        doc_info = doc.get("document", {})
        
        doc_id = doc_info.get("document_id")
        dedup_res = acq_info.get("deduplication_result", "UNKNOWN")
        
        acq_state = "OTHER_QUARANTINED"
        if dedup_res == "DISTINCT_DOCUMENT":
            acq_state = "SUCCESSFULLY_ACQUIRED"
        elif dedup_res == "UNCHANGED_DOCUMENT":
            acq_state = "ALREADY_PRESENT"
        elif dedup_res == "DUPLICATE_REPRESENTATION_ALIAS":
            acq_state = "DUPLICATE_ALIAS"
        else:
            acq_state = dedup_res  # E.g., DOWNLOAD_FAILED, HTML_INSTEAD_OF_DOCUMENT
        
        # Determine extraction readiness
        extraction_state = "READY_FOR_EXTRACTION" if acq_state in ["SUCCESSFULLY_ACQUIRED", "ALREADY_PRESENT"] else "NOT_EXTRACTABLE"
        if extraction_state == "READY_FOR_EXTRACTION":
            extractable_count += 1
            
        inv_record = {
            "document_id": doc_id,
            "source_family": doc_info.get("document_family_id"),
            "document_type": doc_info.get("document_type"),
            "title": doc_info.get("title"),
            "standard_number": doc_info.get("standard_number"),
            "edition": doc_info.get("year_of_publication") or doc_info.get("edition"),
            "lifecycle": doc_info.get("status"),
            "source_url": doc_info.get("source_url"),
            "raw_file_path": acq_info.get("local_path"),
            "sha256": acq_info.get("sha256"),
            "acquisition_state": acq_state,
            "identity_state": "RESOLVED" if doc_id and not doc_id.startswith("UNKNOWN") else "UNRESOLVED",
            "extraction_state": extraction_state
        }
        
        inventory["inventory"].append(inv_record)
        
        if acq_state in categorized:
            categorized[acq_state].append(doc_id)
        elif acq_state == "FAILED":
            err = acq_info.get("error_reason", "")
            if "HTML error" in err or "Masquerading" in err:
                categorized["HTML_INSTEAD_OF_DOCUMENT"].append(doc_id)
            elif "403" in err or "Forbidden" in err:
                categorized["SESSION_BLOCKED"].append(doc_id)
            elif "404" in err or "timed out" in err or "connection" in err.lower():
                categorized["DOWNLOAD_FAILED"].append(doc_id)
            else:
                categorized["OTHER_QUARANTINED"].append(doc_id)
        else:
            categorized["OTHER_QUARANTINED"].append(doc_id)
            
    quarantine_path = ROOT_DIR / "data" / "acquisition" / "quarantine" / "quarantined_candidates.json"
    if quarantine_path.exists():
        with open(quarantine_path, "r", encoding="utf-8") as f:
            quarantined_data = json.load(f)
            
        for qdoc in quarantined_data:
            q_id = qdoc.get("candidate_id")
            q_reason = qdoc.get("rejection_reason") or qdoc.get("error_message") or ""
            
            acq_state = "OTHER_QUARANTINED"
            if "MANUAL_REVIEW" in q_reason:
                acq_state = "MANUAL_REVIEW"
            elif "HTML" in q_reason or "masquerading" in q_reason.lower():
                acq_state = "HTML_INSTEAD_OF_DOCUMENT"
            elif "404" in q_reason or "timed out" in q_reason.lower() or "connection" in q_reason.lower():
                acq_state = "DOWNLOAD_FAILED"
            
            inv_record = {
                "document_id": q_id,
                "source_family": qdoc.get("source_family") or qdoc.get("source_family_id"),
                "document_type": qdoc.get("document_type", "UNKNOWN"),
                "title": qdoc.get("title", "UNKNOWN"),
                "standard_number": None,
                "source_url": qdoc.get("source_url") or qdoc.get("canonical_url"),
                "raw_file_path": None,
                "sha256": None,
                "acquisition_state": acq_state,
                "identity_state": "UNRESOLVED" if "MANUAL_REVIEW" in acq_state else "RESOLVED",
                "extraction_state": "NOT_EXTRACTABLE"
            }
            
            if not any(r["document_id"] == q_id for r in inventory["inventory"] if r["document_id"]):
                inventory["inventory"].append(inv_record)
                if acq_state in categorized:
                    categorized[acq_state].append(q_id)

    # Automated 229-Document Check
    in_inventory = len(categorized["MANUAL_REVIEW"])
    missing = expected_manual_review - in_inventory
    
    logger.info("--- MANUAL_REVIEW AUDIT ---")
    logger.info("ACQUISITION_MANUAL_REVIEW: %d", expected_manual_review)
    logger.info("IN_EXTRACTION_INVENTORY: %d", in_inventory)
    logger.info("MISSING_FROM_INVENTORY: %d", missing)
    
    if missing > 0:
        logger.error("❌ EXTRACTION GATE FAILED: %d MANUAL_REVIEW documents were silently dropped from the inventory!", missing)
        sys.exit(1)
        
    logger.info("✅ MANUAL_REVIEW Audit Passed. Zero documents lost.")

    CORPUS_INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_INVENTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    logger.info("✅ Corpus Inventory built successfully at %s", CORPUS_INVENTORY_PATH)
    logger.info("Total records in inventory: %d", len(inventory["inventory"]))
    logger.info("Total extractable (SUCCESS / ALREADY_PRESENT): %d", extractable_count)
    logger.info("Breakdown:")
    for k, v in categorized.items():
        logger.info("  %s: %d", k, len(v))

if __name__ == "__main__":
    build_inventory()
