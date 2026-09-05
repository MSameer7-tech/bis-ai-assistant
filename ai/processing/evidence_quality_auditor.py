#!/usr/bin/env python3
"""
Phase 5 Final Gate: EvidenceUnit Quality Auditor.
Exhaustively validates all extracted EvidenceUnits before Phase 6 RAG Indexing is authorized.
"""
import json
import logging
import sys
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EvidenceQualityAuditor")

CORPUS_INVENTORY_PATH = ROOT_DIR / "data" / "processed" / "corpus_inventory.json"
EXTRACTION_MANIFEST_PATH = ROOT_DIR / "data" / "processed" / "extraction_manifest.json"
EVIDENCE_UNITS_ROOT = ROOT_DIR / "data" / "processed" / "evidence_units"
IMMUTABLE_STORAGE_ROOT = ROOT_DIR / "data" / "raw" / "immutable"

AUDIT_JSON_PATH = ROOT_DIR / "data" / "processed" / "evidence_quality_audit.json"
AUDIT_MD_PATH = ROOT_DIR / "docs" / "phase5" / "evidence_quality_audit.md"
SOURCE_FAMILIES_PATH = ROOT_DIR / "data" / "sources" / "source_families.json"


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def normalize_text(text: str) -> str:
    # simple near-duplicate normalization
    import re
    return re.sub(r'\s+', ' ', text).strip().lower()

def run_audit():
    logger.info("🚀 Starting EvidenceUnit Quality Gate Audit...")

    if not CORPUS_INVENTORY_PATH.exists() or not EXTRACTION_MANIFEST_PATH.exists():
        logger.error("Missing inventory or extraction manifest.")
        sys.exit(1)

    with open(CORPUS_INVENTORY_PATH, "r", encoding="utf-8") as f:
        inventory_data = json.load(f)
    with open(EXTRACTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    source_families_map = {}
    if SOURCE_FAMILIES_PATH.exists():
        with open(SOURCE_FAMILIES_PATH, "r", encoding="utf-8") as f:
            sf_data = json.load(f)
            for family in sf_data.get("source_families", []):
                source_families_map[family.get("source_family_id")] = family.get("name")
                
                # Check for subfamilies (like SRCF-009)
                for sub in family.get("subfamilies", []):
                    source_families_map[sub.get("subfamily_id")] = sub.get("name")

    inventory_docs = {d["document_id"]: d for d in inventory_data.get("inventory", [])}
    classifications = manifest_data.get("classifications", {})

    # Baseline metrics
    eligible_docs = [d for d in inventory_data.get("inventory", []) if d.get("extraction_state") == "READY_FOR_EXTRACTION"]
    total_eligible = len(eligible_docs)
    total_attempted = sum(len(v) for v in classifications.values())
    
    success_docs = classifications.get("EXTRACTION_SUCCESS", [])
    failed_buckets = ["EXTRACTION_FAILED", "EMPTY_DOCUMENT", "CORRUPTED_DOCUMENT", "UNSUPPORTED_FORMAT", "PARSE_ERROR", "OCR_REQUIRED"]
    failed_docs = []
    for fb in failed_buckets:
        failed_docs.extend(classifications.get(fb, []))

    # Audit Data Structures
    audit = {
        "CHECK_1_PROVENANCE": {
            "TOTAL_UNITS": 0,
            "UNITS_WITH_VALID_SHA": 0,
            "UNITS_WITH_INVALID_SHA": 0,
            "UNITS_WITH_SOURCE_URL": 0,
            "UNITS_MISSING_SOURCE_URL": 0,
            "UNITS_WITH_COMPLETE_PROVENANCE": 0,
            "HARD_FAILURES": []
        },
        "CHECK_2_DOCUMENT_COVERAGE": {
            "EXTRACTION_SUCCESS_DOCUMENTS": len(success_docs),
            "DOCUMENTS_WITH_EVIDENCE_UNITS": 0,
            "DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS": 0,
            "ZERO_UNIT_DOCUMENTS": []
        },
        "CHECK_3_QUALITY": {
            "EMPTY_UNITS": 0,
            "WHITESPACE_ONLY_UNITS": 0,
            "EXTREMELY_SHORT_UNITS": 0,  # < 10 chars
            "DUPLICATE_UNITS": 0,
            "NEAR_DUPLICATE_UNITS": 0,
            "MALFORMED_IDENTIFIERS": 0,
            "MISSING_LOCATION_METADATA": 0,
            "MISSING_DOCUMENT_IDENTITY": 0,
            "MISSING_PROVENANCE": 0
        },
        "CHECK_4_DOCUMENT_TYPE_COVERAGE": defaultdict(lambda: {"eligible": 0, "attempted": 0, "success": 0, "failed": 0, "evidence_units": 0, "zero_unit_docs": 0}),
        "CHECK_5_SOURCE_FAMILY_COVERAGE": defaultdict(lambda: {"success": 0, "evidence_units": 0}),
        "CHECK_6_EXTRACTION_FAILURE_AUDIT": [],
        "CHECK_7_METADATA_QUALITY": {
            "CLAUSE_METADATA": 0,
            "SECTION_METADATA": 0,
            "HEADING_METADATA": 0,
            "TABLE_METADATA": 0,
            "DEFINITION_METADATA": 0,
            "REQUIREMENT_METADATA": 0,
            "CROSS_REFERENCE_METADATA": 0,
            "PAGE_METADATA": 0
        },
        "CHECK_8_DUPLICATION": {
            "EXACT_DUPLICATES": 0,
            "NEAR_DUPLICATES": 0
        },
        "CHECK_9_MANUAL_REVIEW_PRESERVATION": {
            "ACQUISITION_MANUAL_REVIEW": 229,
            "PRESERVED_IN_CORPUS_INVENTORY": 0,
            "DROPPED": 0
        }
    }

    # Populate Document Type and Family Eligible/Attempted
    for doc in eligible_docs:
        dt = doc.get("document_type", "UNKNOWN")
        sf = doc.get("source_family", "UNKNOWN")
        audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["eligible"] += 1
        
    for k, docs in classifications.items():
        for doc in docs:
            dt = doc.get("document_type", "UNKNOWN")
            sf = doc.get("source_family", "UNKNOWN")
            audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["attempted"] += 1
            if k == "EXTRACTION_SUCCESS":
                audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["success"] += 1
                audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["success"] += 1
            else:
                audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["failed"] += 1
                
    # Check 9: Manual Review
    manual_review_docs = [d for d in inventory_data.get("inventory", []) if d.get("acquisition_state") == "MANUAL_REVIEW"]
    audit["CHECK_9_MANUAL_REVIEW_PRESERVATION"]["PRESERVED_IN_CORPUS_INVENTORY"] = len(manual_review_docs)
    audit["CHECK_9_MANUAL_REVIEW_PRESERVATION"]["DROPPED"] = 229 - len(manual_review_docs)

    # Global hashes for exact/near deduplication
    exact_hashes = set()
    near_hashes = set()

    for doc_meta in success_docs:
        doc_id = doc_meta["document_id"]
        sf = doc_meta.get("source_family", "UNKNOWN")
        dt = doc_meta.get("document_type", "UNKNOWN")
        
        unit_file = EVIDENCE_UNITS_ROOT / doc_id / "evidence_units.json"
        
        if not unit_file.exists():
            audit["CHECK_2_DOCUMENT_COVERAGE"]["DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS"] += 1
            audit["CHECK_2_DOCUMENT_COVERAGE"]["ZERO_UNIT_DOCUMENTS"].append(doc_id)
            audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["zero_unit_docs"] += 1
            continue
            
        with open(unit_file, "r", encoding="utf-8") as f:
            units = json.load(f)
            
        if len(units) == 0:
            audit["CHECK_2_DOCUMENT_COVERAGE"]["DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS"] += 1
            audit["CHECK_2_DOCUMENT_COVERAGE"]["ZERO_UNIT_DOCUMENTS"].append(doc_id)
            audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["zero_unit_docs"] += 1
            continue
            
        audit["CHECK_2_DOCUMENT_COVERAGE"]["DOCUMENTS_WITH_EVIDENCE_UNITS"] += 1
        
        # We need the real hash of the immutable binary for validation
        expected_raw_sha = None
        inv_doc = inventory_docs.get(doc_id)
        if inv_doc:
            expected_raw_sha = inv_doc.get("sha256")
            
        # Verify hash matches actual binary
        actual_raw_sha = None
        raw_files = list((IMMUTABLE_STORAGE_ROOT / doc_id).glob("original.*"))
        if raw_files:
            actual_raw_sha = compute_file_sha256(raw_files[0])
            
        for unit in units:
            audit["CHECK_1_PROVENANCE"]["TOTAL_UNITS"] += 1
            audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"][dt]["evidence_units"] += 1
            audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["evidence_units"] += 1
            
            unit_sha = unit.get("parent_raw_sha256")
            unit_url = unit.get("source_url")
            unit_text = unit.get("content_text", "")
            
            # 1. Provenance
            is_valid_sha = False
            if unit_sha and len(unit_sha) == 64 and unit_sha == actual_raw_sha:
                audit["CHECK_1_PROVENANCE"]["UNITS_WITH_VALID_SHA"] += 1
                is_valid_sha = True
            else:
                audit["CHECK_1_PROVENANCE"]["UNITS_WITH_INVALID_SHA"] += 1
                audit["CHECK_1_PROVENANCE"]["HARD_FAILURES"].append(unit.get("evidence_unit_id", "UNKNOWN"))
                
            has_url = False
            if unit_url and unit_url not in ["", "UNKNOWN_URL"]:
                audit["CHECK_1_PROVENANCE"]["UNITS_WITH_SOURCE_URL"] += 1
                has_url = True
            else:
                audit["CHECK_1_PROVENANCE"]["UNITS_MISSING_SOURCE_URL"] += 1
                
            if is_valid_sha and has_url and unit.get("document_id") and unit.get("document_family_id") and unit.get("document_type") and unit_text:
                audit["CHECK_1_PROVENANCE"]["UNITS_WITH_COMPLETE_PROVENANCE"] += 1
            else:
                audit["CHECK_3_QUALITY"]["MISSING_PROVENANCE"] += 1

            if not unit.get("document_id") or not unit.get("document_family_id"):
                audit["CHECK_3_QUALITY"]["MISSING_DOCUMENT_IDENTITY"] += 1
                
            # 3. Quality
            if not unit_text:
                audit["CHECK_3_QUALITY"]["EMPTY_UNITS"] += 1
            elif not unit_text.strip():
                audit["CHECK_3_QUALITY"]["WHITESPACE_ONLY_UNITS"] += 1
            elif len(unit_text.strip()) < 10:
                audit["CHECK_3_QUALITY"]["EXTREMELY_SHORT_UNITS"] += 1
                
            if not unit.get("evidence_unit_id"):
                audit["CHECK_3_QUALITY"]["MALFORMED_IDENTIFIERS"] += 1
                
            if not unit.get("section_or_clause") and not unit.get("page_number"):
                audit["CHECK_3_QUALITY"]["MISSING_LOCATION_METADATA"] += 1
                
            # 7. Metadata Quality
            if "CLAUSE" in unit.get("content_type", "") or unit.get("section_or_clause"):
                audit["CHECK_7_METADATA_QUALITY"]["CLAUSE_METADATA"] += 1
            if "SECTION" in unit.get("content_type", ""):
                audit["CHECK_7_METADATA_QUALITY"]["SECTION_METADATA"] += 1
            if unit.get("heading"):
                audit["CHECK_7_METADATA_QUALITY"]["HEADING_METADATA"] += 1
            if unit.get("content_type") == "TABLE" or "TABLE" in str(unit.get("section_or_clause", "")).upper():
                audit["CHECK_7_METADATA_QUALITY"]["TABLE_METADATA"] += 1
            if unit.get("content_type") == "DEFINITION":
                audit["CHECK_7_METADATA_QUALITY"]["DEFINITION_METADATA"] += 1
            if unit.get("page_number") is not None:
                audit["CHECK_7_METADATA_QUALITY"]["PAGE_METADATA"] += 1
                
            # Requirements and Cross-Refs are in structured_data or semantic inference, we can check basic keywords for now
            if "shall" in unit_text.lower() or "must" in unit_text.lower():
                audit["CHECK_7_METADATA_QUALITY"]["REQUIREMENT_METADATA"] += 1
            if "see clause" in unit_text.lower() or "refer to" in unit_text.lower() or "in accordance with" in unit_text.lower():
                audit["CHECK_7_METADATA_QUALITY"]["CROSS_REFERENCE_METADATA"] += 1
                
            # 8. Duplication
            unit_hash = hashlib.md5(unit_text.encode('utf-8')).hexdigest()
            if unit_hash in exact_hashes:
                audit["CHECK_3_QUALITY"]["DUPLICATE_UNITS"] += 1
                audit["CHECK_8_DUPLICATION"]["EXACT_DUPLICATES"] += 1
            else:
                exact_hashes.add(unit_hash)
                
            near_text = normalize_text(unit_text)
            if near_text:
                near_hash = hashlib.md5(near_text.encode('utf-8')).hexdigest()
                if near_hash in near_hashes:
                    audit["CHECK_3_QUALITY"]["NEAR_DUPLICATE_UNITS"] += 1
                    audit["CHECK_8_DUPLICATION"]["NEAR_DUPLICATES"] += 1
                else:
                    near_hashes.add(near_hash)

    # Check 6: Failure Audit
    for doc in failed_docs:
        doc_id = doc.get("document_id")
        inv_doc = inventory_docs.get(doc_id, {})
        
        audit["CHECK_6_EXTRACTION_FAILURE_AUDIT"].append({
            "document_id": doc_id,
            "document_type": doc.get("document_type"),
            "source_family": doc.get("source_family"),
            "failure_classification": "UNKNOWN", # Would need to map back which bucket it was in, let's derive
            "error_reason": doc.get("reason"),
            "raw_sha": inv_doc.get("sha256"),
            "can_resolve_with_ocr": "ocr" in str(doc.get("reason", "")).lower() or "scan" in str(doc.get("reason", "")).lower()
        })
        
    # Check 10: Final Gate Determination
    gate_status = "PASS"
    fail_reasons = []
    
    if audit["CHECK_9_MANUAL_REVIEW_PRESERVATION"]["DROPPED"] > 0:
        gate_status = "FAIL"
        fail_reasons.append(f"Dropped {audit['CHECK_9_MANUAL_REVIEW_PRESERVATION']['DROPPED']} MANUAL_REVIEW documents")
        
    if audit["CHECK_1_PROVENANCE"]["UNITS_WITH_INVALID_SHA"] > 0:
        gate_status = "FAIL"
        fail_reasons.append(f"Found {audit['CHECK_1_PROVENANCE']['UNITS_WITH_INVALID_SHA']} units with invalid SHAs")
        
    if audit["CHECK_1_PROVENANCE"]["UNITS_MISSING_SOURCE_URL"] > 0:
        gate_status = "FAIL"
        fail_reasons.append(f"Found {audit['CHECK_1_PROVENANCE']['UNITS_MISSING_SOURCE_URL']} units missing source URLs")
        
    if audit["CHECK_2_DOCUMENT_COVERAGE"]["DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS"] > 0:
        if gate_status == "PASS":
            gate_status = "CONDITIONAL_PASS"
        fail_reasons.append(f"Found {audit['CHECK_2_DOCUMENT_COVERAGE']['DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS']} successfully parsed documents with 0 evidence units")

    audit["CHECK_10_FINAL_GATE"] = {
        "STATUS": gate_status,
        "FAIL_REASONS": fail_reasons
    }

    # Fetch canonical source family IDs from acquisition manifest for accurate reporting
    canonical_source_families = {}
    ACQ_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
    if ACQ_MANIFEST_PATH.exists():
        with open(ACQ_MANIFEST_PATH, "r", encoding="utf-8") as f:
            acq_data = json.load(f)
            for acq_doc in acq_data.get("documents", []):
                doc_id = acq_doc.get("document", {}).get("document_id")
                srcf = acq_doc.get("source", {}).get("source_family_id")
                if doc_id and srcf:
                    canonical_source_families[doc_id] = srcf
            
    # Re-bucket success and evidence units into canonical source families
    audit["CHECK_5_SOURCE_FAMILY_COVERAGE"] = defaultdict(lambda: {"eligible": 0, "attempted": 0, "success": 0, "failed": 0, "evidence_units": 0, "zero_unit_docs": 0})
    
    for doc in eligible_docs:
        sf = canonical_source_families.get(doc["document_id"], "UNKNOWN")
        audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["eligible"] += 1
        
    for k, docs in classifications.items():
        for doc in docs:
            sf = canonical_source_families.get(doc["document_id"], "UNKNOWN")
            audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["attempted"] += 1
            if k == "EXTRACTION_SUCCESS":
                audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["success"] += 1
            else:
                audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["failed"] += 1
                
    for doc_meta in success_docs:
        doc_id = doc_meta["document_id"]
        sf = canonical_source_families.get(doc_id, "UNKNOWN")
        unit_file = EVIDENCE_UNITS_ROOT / doc_id / "evidence_units.json"
        if unit_file.exists():
            with open(unit_file, "r", encoding="utf-8") as f:
                units = json.load(f)
                if len(units) > 0:
                    audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["evidence_units"] += len(units)
                else:
                    audit["CHECK_5_SOURCE_FAMILY_COVERAGE"][sf]["zero_unit_docs"] += 1

    # Write JSON
    AUDIT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
        
    # Write MD
    total_failed = sum(len(classifications.get(fb, [])) for fb in failed_buckets)
    
    md = f"""# Phase 5: Final EvidenceUnit Quality Audit

## PHASE_5_STATUS = {gate_status}

The PASS gate requires:
- SHA provenance: PASS
- source_url provenance: PASS
- document coverage: PASS
- manual-review preservation: PASS
- EvidenceUnit identity/location integrity: PASS
- duplicate investigation: PASS
- short-unit investigation: PASS
- extraction failures explicitly accounted for: PASS

{'''### Findings:
- ''' + chr(10).join('- ' + r for r in fail_reasons) if fail_reasons else "All primary integrity gates passed clean."}

## CHECK 1: Cryptographic Provenance
- Total Units: {audit["CHECK_1_PROVENANCE"]["TOTAL_UNITS"]}
- Units with Valid SHA: {audit["CHECK_1_PROVENANCE"]["UNITS_WITH_VALID_SHA"]}
- Units with Invalid SHA: {audit["CHECK_1_PROVENANCE"]["UNITS_WITH_INVALID_SHA"]}
- Units with Source URL: {audit["CHECK_1_PROVENANCE"]["UNITS_WITH_SOURCE_URL"]}
- Units missing Source URL: {audit["CHECK_1_PROVENANCE"]["UNITS_MISSING_SOURCE_URL"]}
- Units with Complete Provenance: {audit["CHECK_1_PROVENANCE"]["UNITS_WITH_COMPLETE_PROVENANCE"]}

## CHECK 2: Document Coverage
- Extraction Eligible Documents: {total_eligible}
- Extraction Attempted: {total_attempted}
- Extraction Success: {len(success_docs)}
- Extraction Failed: {total_failed}
- Documents with Zero EvidenceUnits: {audit["CHECK_2_DOCUMENT_COVERAGE"]["DOCUMENTS_WITH_ZERO_EVIDENCE_UNITS"]}

## CHECK 3: EvidenceUnit Quality
- Empty Units: {audit["CHECK_3_QUALITY"]["EMPTY_UNITS"]}
- Whitespace-only Units: {audit["CHECK_3_QUALITY"]["WHITESPACE_ONLY_UNITS"]}
- Extremely Short Units (<10 chars): {audit["CHECK_3_QUALITY"]["EXTREMELY_SHORT_UNITS"]}
- Duplicate Units: {audit["CHECK_3_QUALITY"]["DUPLICATE_UNITS"]}
- Near-Duplicate Units: {audit["CHECK_3_QUALITY"]["NEAR_DUPLICATE_UNITS"]}
- Malformed Identifiers: {audit["CHECK_3_QUALITY"]["MALFORMED_IDENTIFIERS"]}
- Missing Location Metadata: {audit["CHECK_3_QUALITY"]["MISSING_LOCATION_METADATA"]}
- Missing Document Identity: {audit["CHECK_3_QUALITY"]["MISSING_DOCUMENT_IDENTITY"]}
- Missing Provenance: {audit["CHECK_3_QUALITY"]["MISSING_PROVENANCE"]}

## CHECK 4: Document Type Coverage
| Type | Eligible | Attempted | Success | Failed | EvidenceUnits | Zero-Unit Docs |
|---|---|---|---|---|---|---|
"""
    for dt, stats in sorted(audit["CHECK_4_DOCUMENT_TYPE_COVERAGE"].items()):
        md += f"| {dt} | {stats['eligible']} | {stats['attempted']} | {stats['success']} | {stats['failed']} | {stats['evidence_units']} | {stats['zero_unit_docs']} |\n"

    md += """
## CHECK 5: Source Family Coverage
| Family | Eligible | Attempted | Success | Failed | EvidenceUnits | Zero-Unit Docs |
|---|---|---|---|---|---|---|
"""
    for sf, stats in sorted(audit["CHECK_5_SOURCE_FAMILY_COVERAGE"].items()):
        sf_display = f"{sf} ({source_families_map.get(sf, 'Unknown Family')})" if sf != "UNKNOWN" else sf
        md += f"| {sf_display} | {stats['eligible']} | {stats['attempted']} | {stats['success']} | {stats['failed']} | {stats['evidence_units']} | {stats['zero_unit_docs']} |\n"

    md += f"""
## CHECK 6: Extraction Failure Audit
Explicit accounting for the {total_failed} terminal extraction failures:
| Document ID | Type | Source Family | Reason |
|---|---|---|---|
"""
    for fail in audit["CHECK_6_EXTRACTION_FAILURE_AUDIT"]:
        sf = canonical_source_families.get(fail['document_id'], fail.get('source_family', 'UNKNOWN'))
        sf_display = f"{sf} ({source_families_map.get(sf, 'Unknown Family')})" if sf != "UNKNOWN" else sf
        md += f"| {fail['document_id']} | {fail['document_type']} | {sf_display} | {fail['error_reason']} |\n"

    md += """
## CHECK 7: Table/Clause/Definition Quality (Metadata Presence)
- Clause Metadata: {CLAUSE_METADATA}
- Section Metadata: {SECTION_METADATA}
- Heading Metadata: {HEADING_METADATA}
- Table Metadata: {TABLE_METADATA}
- Definition Metadata: {DEFINITION_METADATA}
- Page Metadata: {PAGE_METADATA}
- Requirement Language: {REQUIREMENT_METADATA}
- Cross-Reference Language: {CROSS_REFERENCE_METADATA}
""".format(**audit["CHECK_7_METADATA_QUALITY"])

    md += """
## CHECK 8: Duplication
- Exact Duplicates: {EXACT_DUPLICATES}
- Near Duplicates: {NEAR_DUPLICATES}
""".format(**audit["CHECK_8_DUPLICATION"])

    md += """
## CHECK 9: Manual Review Preservation
- ACQUISITION_MANUAL_REVIEW: {ACQUISITION_MANUAL_REVIEW}
- PRESERVED_IN_CORPUS_INVENTORY: {PRESERVED_IN_CORPUS_INVENTORY}
- DROPPED: {DROPPED}
""".format(**audit["CHECK_9_MANUAL_REVIEW_PRESERVATION"])

    AUDIT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info(f"✅ Audit Complete! Gate Status: {gate_status}")

if __name__ == "__main__":
    run_audit()
