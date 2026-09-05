#!/usr/bin/env python3
"""
Step 0: Phase 6 Preflight.
Read-only validation of the Phase 5 frozen baseline before any chunking or indexing.
"""
import json
import logging
import sys
from pathlib import Path
import hashlib

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase6Preflight")

EVIDENCE_UNITS_DIR = ROOT_DIR / "data" / "processed" / "evidence_units"
EXPECTED_UNITS = 17167

def run_preflight():
    logger.info("🚀 Starting Phase 6 Preflight Validation...")
    
    if not EVIDENCE_UNITS_DIR.exists():
        logger.error(f"Directory not found: {EVIDENCE_UNITS_DIR}")
        sys.exit(1)
        
    eu_files = list(EVIDENCE_UNITS_DIR.rglob("*.json"))
    logger.info(f"Found {len(eu_files)} EvidenceUnit files.")
    
    total_units = 0
    missing_fields = []
    
    for eu_file in eu_files:
        try:
            with open(eu_file, "r", encoding="utf-8") as f:
                units = json.load(f)
                
            for u in units:
                total_units += 1
                eu_id = u.get("evidence_unit_id")
                
                required_fields = [
                    "evidence_unit_id", "document_id", "content_text",
                    "source_url", "parent_raw_sha256", "document_family_id"
                ]
                
                for field in required_fields:
                    if not u.get(field):
                        missing_fields.append((eu_id, field))
                        
                # Check location metadata
                if not u.get("section_or_clause") and u.get("page_number") is None:
                    missing_fields.append((eu_id, "location_metadata"))
                    
        except Exception as e:
            logger.error(f"Error reading {eu_file}: {e}")
            sys.exit(1)
            
    logger.info(f"Counted {total_units} EvidenceUnits.")
    
    if total_units != EXPECTED_UNITS:
        logger.error(f"🚨 Preflight Failed: Expected {EXPECTED_UNITS} EvidenceUnits, found {total_units}")
        sys.exit(1)
        
    if missing_fields:
        logger.error(f"🚨 Preflight Failed: Found {len(missing_fields)} units missing required fields.")
        for eu_id, field in missing_fields[:10]:
            logger.error(f"  - Unit {eu_id} missing {field}")
        if len(missing_fields) > 10:
            logger.error(f"  ... and {len(missing_fields) - 10} more.")
        sys.exit(1)
        
    logger.info("✅ Phase 6 Preflight Passed! Frozen baseline verified.")
    sys.exit(0)

if __name__ == "__main__":
    run_preflight()
