#!/usr/bin/env python3
"""
Phase 5 Extraction Readiness: Reporter & Audit Generator.
Compiles the extraction manifest into human-readable quality and coverage audits.
Enforces the mandatory Engineering Gate output.
"""
import json
import logging
import sys
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExtractionReporter")

EXTRACTION_MANIFEST_PATH = ROOT_DIR / "data" / "processed" / "extraction_manifest.json"
CORPUS_INVENTORY_PATH = ROOT_DIR / "data" / "processed" / "corpus_inventory.json"
QUALITY_REPORT_PATH = ROOT_DIR / "brain" / "e1896a58-91e7-4f5d-8c04-d8644f415acb" / "extraction_quality_report.md"
COVERAGE_AUDIT_PATH = ROOT_DIR / "brain" / "e1896a58-91e7-4f5d-8c04-d8644f415acb" / "extraction_coverage_audit.md"

def generate_reports():
    if not EXTRACTION_MANIFEST_PATH.exists() or not CORPUS_INVENTORY_PATH.exists():
        logger.error("Missing manifest or inventory")
        sys.exit(1)

    with open(EXTRACTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(CORPUS_INVENTORY_PATH, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    # 1. Generate Quality Report
    acc = manifest.get("accounting", {})
    qm = manifest.get("quality_metrics", {})
    classifications = manifest.get("classifications", {})
    
    docs_with_evidence = len(classifications.get("EXTRACTION_SUCCESS", [])) - qm.get("docs_with_zero_evidence_units", 0)

    quality_md = f"""# Phase 5: Extraction Quality Report

This report serves as the Engineering Gate for moving into Phase 6 (Vector Indexing / RAG).

## 1. Top-Level Metrics

| Metric | Count |
| :--- | :--- |
| **ACQUIRED_DOCUMENTS (Extractable)** | {acc.get("documents_expected", 0)} |
| **EXTRACTION_ATTEMPTED** | {acc.get("documents_processed", 0)} |
| **EXTRACTION_SUCCESS** | {acc.get("EXTRACTION_SUCCESS", 0)} |
| **EXTRACTION_FAILED** | {acc.get("EXTRACTION_FAILED", 0)} |
| **EMPTY_DOCUMENT** | {acc.get("EMPTY_DOCUMENT", 0)} |
| **CORRUPTED_DOCUMENT** | {acc.get("CORRUPTED_DOCUMENT", 0)} |
| **UNSUPPORTED_FORMAT** | {acc.get("UNSUPPORTED_FORMAT", 0)} |
| **PARSE_ERROR** | {acc.get("PARSE_ERROR", 0)} |
| **OCR_REQUIRED** | {acc.get("OCR_REQUIRED", 0)} |
| **EXTRACTION_MANUAL_REVIEW** | {acc.get("EXTRACTION_MANUAL_REVIEW", 0)} |

## 2. Evidence Formulation Outcomes

> [!WARNING]
> EXTRACTION_SUCCESS does not guarantee useful data. A parser can technically succeed on a scanned page and yield 0 clauses.

| Metric | Count |
| :--- | :--- |
| **EVIDENCE_UNITS_TOTAL** | {qm.get("total_evidence_units_extracted", 0)} |
| **DOCUMENTS_WITH_EVIDENCE_UNITS** | {docs_with_evidence} |
| **DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS** | {qm.get("docs_with_zero_evidence_units", 0)} |
| **DOCUMENTS_WITH_COMPLETE_PROVENANCE** | {acc.get("EXTRACTION_SUCCESS", 0)} (Required for Success) |

"""
    
    QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUALITY_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(quality_md)

    # 2. Generate Coverage Audit
    # Analyze by source family and document type
    fam_stats = defaultdict(lambda: {"total": 0, "success": 0, "zero_units": 0, "ocr_required": 0, "manual_review": 0})
    type_stats = defaultdict(lambda: {"total": 0, "success": 0, "zero_units": 0, "ocr_required": 0, "manual_review": 0})
    
    # Load authoritative source family mappings from acquisition manifest
    ACQ_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
    doc_to_srcf = {}
    if ACQ_MANIFEST_PATH.exists():
        with open(ACQ_MANIFEST_PATH, "r", encoding="utf-8") as f:
            acq_data = json.load(f)
            for acq_doc in acq_data.get("documents", []):
                doc_id = acq_doc.get("document", {}).get("document_id")
                srcf = acq_doc.get("source", {}).get("source_family_id")
                if doc_id and srcf:
                    doc_to_srcf[doc_id] = srcf
    
    for bucket_name, docs in classifications.items():
        for doc in docs:
            doc_id = doc.get("document_id")
            sf = doc_to_srcf.get(doc_id, "UNRESOLVED_SOURCE_FAMILY")
            dt = doc.get("document_type", "UNKNOWN")
            
            fam_stats[sf]["total"] += 1
            type_stats[dt]["total"] += 1
            
            if bucket_name == "EXTRACTION_SUCCESS":
                if doc.get("useful_extraction", True):
                    fam_stats[sf]["success"] += 1
                    type_stats[dt]["success"] += 1
                else:
                    fam_stats[sf]["zero_units"] += 1
                    type_stats[dt]["zero_units"] += 1
            elif bucket_name == "OCR_REQUIRED":
                fam_stats[sf]["ocr_required"] += 1
                type_stats[dt]["ocr_required"] += 1
            elif bucket_name == "EXTRACTION_MANUAL_REVIEW":
                fam_stats[sf]["manual_review"] += 1
                type_stats[dt]["manual_review"] += 1

    coverage_md = f"""# Phase 5: Corpus Coverage Audit

This audit determines which source families or document types have poor extraction coverage and require intervention (e.g. OCR) before indexing.

## Source Family Coverage

| Source Family | Total Attempted | Successfully Extracted (Has Units) | Zero Units | OCR Required | Manual Review | Coverage % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    
    for sf, st in sorted(fam_stats.items(), key=lambda x: x[0]):
        cov = (st["success"] / st["total"]) * 100 if st["total"] > 0 else 0
        coverage_md += f"| {sf} | {st['total']} | {st['success']} | {st['zero_units']} | {st['ocr_required']} | {st['manual_review']} | {cov:.1f}% |\n"

    coverage_md += "\n## Document Type Coverage\n\n"
    coverage_md += "| Document Type | Total Attempted | Successfully Extracted (Has Units) | Zero Units | OCR Required | Manual Review | Coverage % |\n"
    coverage_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for dt, st in sorted(type_stats.items(), key=lambda x: x[0]):
        cov = (st["success"] / st["total"]) * 100 if st["total"] > 0 else 0
        coverage_md += f"| {dt} | {st['total']} | {st['success']} | {st['zero_units']} | {st['ocr_required']} | {st['manual_review']} | {cov:.1f}% |\n"

    # Write the Coverage Report
    COVERAGE_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COVERAGE_AUDIT_PATH, "w", encoding="utf-8") as f:
        f.write(coverage_md)
        
    logger.info("✅ Generated Extraction Quality Report: %s", QUALITY_REPORT_PATH)
    logger.info("✅ Generated Extraction Coverage Audit: %s", COVERAGE_AUDIT_PATH)

    # Note: adding an explicit check for UNRESOLVED_SOURCE_FAMILY log
    unresolved_count = fam_stats.get("UNRESOLVED_SOURCE_FAMILY", {}).get("total", 0)
    if unresolved_count > 0:
        logger.warning(f"⚠️ Found {unresolved_count} documents with UNRESOLVED_SOURCE_FAMILY mapping!")



if __name__ == "__main__":
    generate_reports()
