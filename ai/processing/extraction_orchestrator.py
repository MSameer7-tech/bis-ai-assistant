#!/usr/bin/env python3
"""
Hardened Batch Extraction & Evidence Formulation Orchestrator (Phase 4).
Verifies cryptographic raw file integrity before extraction, processes genuine PDF/HTML/JSON content,
and enforces strict completion accounting.
"""
import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.processing.document_extractor import DocumentExtractor, ExtractedDocument
from ai.processing.evidence_unit_builder import EvidenceUnitBuilder, EvidenceUnit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExtractionOrchestrator")

ACQUISITION_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
CORPUS_INVENTORY_PATH = ROOT_DIR / "data" / "processed" / "corpus_inventory.json"
IMMUTABLE_STORAGE_ROOT = ROOT_DIR / "data" / "raw" / "immutable"
EVIDENCE_UNITS_ROOT = ROOT_DIR / "data" / "processed" / "evidence_units"
EXTRACTION_MANIFEST_PATH = ROOT_DIR / "data" / "processed" / "extraction_manifest.json"


def compute_file_sha256(path: Path) -> str:
    """Computes SHA-256 digest of a local file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ExtractionOrchestrator:
    """Orchestrates genuine batch extraction across the immutable raw corpus with full integrity verification."""

    def __init__(self):
        self.extractor = DocumentExtractor()
        self.builder = EvidenceUnitBuilder()

    def run_extraction(self) -> Dict[str, Any]:
        """Runs batch extraction on all extractable documents in the corpus inventory."""
        logger.info("🚀 Starting Hardened Phase 5 Document Extraction...")

        if not CORPUS_INVENTORY_PATH.exists():
            logger.error("Corpus inventory not found at %s", CORPUS_INVENTORY_PATH)
            sys.exit(1)

        with open(CORPUS_INVENTORY_PATH, "r", encoding="utf-8") as f:
            inventory_data = json.load(f)

        inventory_docs = inventory_data.get("inventory", [])
        extractable_docs = [doc for doc in inventory_docs if doc.get("extraction_state") == "READY_FOR_EXTRACTION"]
        
        total_expected = len(extractable_docs)
        logger.info("📄 Ingesting %d expected documents from corpus inventory...", total_expected)

        all_evidence_units: List[EvidenceUnit] = []
        
        # Classification buckets
        classifications = {
            "EXTRACTION_SUCCESS": [],
            "EXTRACTION_FAILED": [],
            "EMPTY_DOCUMENT": [],
            "CORRUPTED_DOCUMENT": [],
            "UNSUPPORTED_FORMAT": [],
            "PARSE_ERROR": [],
            "OCR_REQUIRED": [],
            "EXTRACTION_MANUAL_REVIEW": []
        }

        total_pages = 0
        total_clauses = 0
        total_tables = 0
        docs_with_zero_evidence_units = 0

        for item in extractable_docs:
            doc_id = item.get("document_id")
            expected_sha = item.get("sha256")
            acq_state = item.get("acquisition_state")
            doc_type = item.get("document_type")
            source_family = item.get("source_family")

            doc_dir = IMMUTABLE_STORAGE_ROOT / doc_id
            if not doc_dir.exists():
                logger.error("❌ Document directory missing for %s", doc_id)
                classifications["EXTRACTION_FAILED"].append({
                    "document_id": doc_id, "source_family": source_family, "document_type": doc_type, "reason": "Directory missing in immutable storage"
                })
                continue

            raw_files = list(doc_dir.glob("original.*"))
            if not raw_files:
                logger.error("❌ No raw file found in %s", doc_dir)
                classifications["EXTRACTION_FAILED"].append({
                    "document_id": doc_id, "source_family": source_family, "document_type": doc_type, "reason": "No original.* file in immutable directory"
                })
                continue

            raw_file = raw_files[0]
            sidecar_meta = doc_dir / "metadata.json"

            # 1. Pre-Extraction Cryptographic Integrity Verification (Enforce for ALREADY_PRESENT too!)
            actual_sha = compute_file_sha256(raw_file)
            if actual_sha != expected_sha:
                logger.error("❌ Cryptographic SHA mismatch for %s: expected %s, got %s", doc_id, expected_sha, actual_sha)
                classifications["CORRUPTED_DOCUMENT"].append({
                    "document_id": doc_id, "source_family": source_family, "document_type": doc_type, 
                    "reason": f"Integrity Mismatch: expected SHA {expected_sha} != actual {actual_sha}"
                })
                continue

            # 2. Multi-Format Genuine Extraction
            extracted_doc: ExtractedDocument = self.extractor.extract_document(
                raw_file_path=raw_file,
                metadata_path=sidecar_meta
            )

            if not extracted_doc.is_success:
                logger.error("❌ Extraction failed for %s: %s", doc_id, extracted_doc.error_reason)
                err_str = str(extracted_doc.error_reason).lower()
                
                # Classify the error
                bucket = "EXTRACTION_FAILED"
                if "empty" in err_str:
                    bucket = "EMPTY_DOCUMENT"
                elif "unsupported" in err_str:
                    bucket = "UNSUPPORTED_FORMAT"
                elif "parse" in err_str:
                    bucket = "PARSE_ERROR"
                elif "ocr" in err_str:
                    bucket = "OCR_REQUIRED"
                elif "review" in err_str:
                    bucket = "EXTRACTION_MANUAL_REVIEW"
                    
                classifications[bucket].append({
                    "document_id": doc_id, "source_family": source_family, "document_type": doc_type, "reason": extracted_doc.error_reason
                })
                continue

            # 3. Formulate Atomic Evidence Units
            units, build_err = self.builder.build_evidence_units(extracted_doc)
            if build_err:
                logger.error("❌ Evidence formulation failed for %s: %s", doc_id, build_err)
                bucket = "EXTRACTION_MANUAL_REVIEW" if "review" in build_err.lower() else "EXTRACTION_FAILED"
                classifications[bucket].append({
                    "document_id": doc_id, "source_family": source_family, "document_type": doc_type, "reason": build_err
                })
                continue
                
            if not units:
                docs_with_zero_evidence_units += 1
                classifications["EXTRACTION_SUCCESS"].append({
                    "document_id": doc_id,
                    "source_family": source_family,
                    "document_type": doc_type,
                    "pages_count": extracted_doc.pages_count,
                    "total_units": 0,
                    "clauses_extracted": 0,
                    "tables_extracted": 0,
                    "useful_extraction": False
                })
                continue

            total_pages += extracted_doc.pages_count
            total_clauses += len(extracted_doc.clauses)
            total_tables += len(extracted_doc.tables)
            all_evidence_units.extend(units)

            # 4. Persist per-document evidence units
            target_unit_dir = EVIDENCE_UNITS_ROOT / doc_id
            target_unit_dir.mkdir(parents=True, exist_ok=True)
            with open(target_unit_dir / "evidence_units.json", "w", encoding="utf-8") as f:
                json.dump([u.model_dump() for u in units], f, indent=2)

            classifications["EXTRACTION_SUCCESS"].append({
                "document_id": doc_id,
                "source_family": source_family,
                "document_type": doc_type,
                "pages_count": extracted_doc.pages_count,
                "total_units": len(units),
                "clauses_extracted": len(extracted_doc.clauses),
                "tables_extracted": len(extracted_doc.tables),
                "useful_extraction": True
            })

        # 5. Compile Extraction Manifest
        total_processed = sum(len(v) for v in classifications.values())
        
        extraction_manifest = {
            "manifest_version": "1.1",
            "phase": "Phase 5: Extraction Readiness",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "accounting": {
                "documents_expected": total_expected,
                "documents_processed": total_processed,
                "EXTRACTION_SUCCESS": len(classifications["EXTRACTION_SUCCESS"]),
                "EXTRACTION_FAILED": len(classifications["EXTRACTION_FAILED"]),
                "EMPTY_DOCUMENT": len(classifications["EMPTY_DOCUMENT"]),
                "CORRUPTED_DOCUMENT": len(classifications["CORRUPTED_DOCUMENT"]),
                "UNSUPPORTED_FORMAT": len(classifications["UNSUPPORTED_FORMAT"]),
                "PARSE_ERROR": len(classifications["PARSE_ERROR"]),
                "OCR_REQUIRED": len(classifications["OCR_REQUIRED"]),
                "EXTRACTION_MANUAL_REVIEW": len(classifications["EXTRACTION_MANUAL_REVIEW"])
            },
            "quality_metrics": {
                "total_pages_processed": total_pages,
                "total_evidence_units_extracted": len(all_evidence_units),
                "total_clauses_extracted": total_clauses,
                "total_tables_extracted": total_tables,
                "docs_with_zero_evidence_units": docs_with_zero_evidence_units
            },
            "classifications": classifications
        }

        EXTRACTION_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(EXTRACTION_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(extraction_manifest, f, indent=2)

        logger.info(
            "📊 Phase 5 Extraction Finished: %d/%d successful",
            len(classifications["EXTRACTION_SUCCESS"]),
            total_expected
        )
        return extraction_manifest


def main():
    orchestrator = ExtractionOrchestrator()
    res = orchestrator.run_extraction()
    print(f"\n📊 Phase 5 Extraction Report:")
    print(f"  Documents Expected: {res['accounting']['documents_expected']}")
    print(f"  Extraction Success: {res['accounting']['EXTRACTION_SUCCESS']}")
    print(f"  Extraction Failed: {res['accounting']['EXTRACTION_FAILED']}")
    print(f"  Extraction Manual Review: {res['accounting']['EXTRACTION_MANUAL_REVIEW']}")
    print(f"  Docs with Zero Evidence Units: {res['quality_metrics']['docs_with_zero_evidence_units']}")
    print(f"  Total Evidence Units: {res['quality_metrics']['total_evidence_units_extracted']}")


if __name__ == "__main__":
    main()
