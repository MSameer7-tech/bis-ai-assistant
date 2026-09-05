#!/usr/bin/env python3
"""
Step 1: Phase 6 Corpus Fingerprint.
Generates a deterministic fingerprint of the frozen EvidenceUnit corpus.
"""
import json
import logging
import sys
import hashlib
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase6Fingerprint")

EVIDENCE_UNITS_DIR = ROOT_DIR / "data" / "processed" / "evidence_units"
INDEXES_DIR = ROOT_DIR / "data" / "indexes"
FINGERPRINT_PATH = INDEXES_DIR / "corpus_fingerprint.json"
ACQ_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"

def get_canonical_source_families() -> dict:
    doc_to_srcf = {}
    if ACQ_MANIFEST_PATH.exists():
        with open(ACQ_MANIFEST_PATH, "r", encoding="utf-8") as f:
            acq_data = json.load(f)
            for acq_doc in acq_data.get("documents", []):
                doc_id = acq_doc.get("document", {}).get("document_id")
                srcf = acq_doc.get("source", {}).get("source_family_id")
                if doc_id and srcf:
                    doc_to_srcf[doc_id] = srcf
    return doc_to_srcf

def run_fingerprint():
    logger.info("🚀 Generating Phase 6 Corpus Fingerprint...")
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    
    eu_files = list(EVIDENCE_UNITS_DIR.rglob("*.json"))
    
    all_units = []
    
    doc_to_srcf = get_canonical_source_families()
    
    for eu_file in eu_files:
        with open(eu_file, "r", encoding="utf-8") as f:
            units = json.load(f)
            for u in units:
                doc_id = u.get("document_id")
                # Build canonical representation of each EvidenceUnit
                canonical_unit = {
                    "evidence_unit_id": u.get("evidence_unit_id"),
                    "document_id": doc_id,
                    "content": u.get("content_text", "").strip(),
                    "clause": str(u.get("section_or_clause") or ""),
                    "section": str(u.get("section") or ""),
                    "heading": str(u.get("heading") or ""),
                    "page": str(u.get("page_number") or ""),
                    "source_url": str(u.get("source_url") or ""),
                    "parent_raw_sha256": str(u.get("parent_raw_sha256") or ""),
                    "document_type": str(u.get("document_type") or "UNKNOWN"),
                    "source_family": str(doc_to_srcf.get(doc_id, "UNRESOLVED_SOURCE_FAMILY"))
                }
                all_units.append(canonical_unit)
                
    # Sort deterministically
    all_units.sort(key=lambda x: (x["document_id"], x["evidence_unit_id"]))
    
    # Hash the canonical representation
    # json.dumps with sort_keys=True ensures consistent byte formatting
    canonical_json = json.dumps(all_units, sort_keys=True, separators=(',', ':'))
    fingerprint = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    manifest = {
        "algorithm": "SHA-256",
        "canonicalization_version": "1.0",
        "evidence_unit_count": len(all_units),
        "corpus_fingerprint": fingerprint,
        "creation_timestamp": datetime.utcnow().isoformat() + "Z",
        "input_path": str(EVIDENCE_UNITS_DIR.relative_to(ROOT_DIR))
    }
    
    with open(FINGERPRINT_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"✅ Generated Fingerprint: {fingerprint}")
    logger.info(f"💾 Saved to {FINGERPRINT_PATH}")
    sys.exit(0)

if __name__ == "__main__":
    run_fingerprint()
