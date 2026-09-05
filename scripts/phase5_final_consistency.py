import json
import logging
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase5Check")

EVIDENCE_UNITS_ROOT = Path("data/processed/evidence_units")
MANIFEST_PATH = Path("data/processed/extraction_manifest.json")
INVENTORY_PATH = Path("data/processed/corpus_inventory.json")
DUPLICATE_JSON = Path("data/processed/evidence_duplicate_audit.json")

def is_invalid_url(url):
    if not url: return True
    if not str(url).strip(): return True
    if url == "UNKNOWN" or url == "UNKNOWN_URL": return True
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True
    except:
        return True
    return False

def check():
    with open(MANIFEST_PATH, "r") as f: manifest = json.load(f)
    with open(INVENTORY_PATH, "r") as f: inventory = json.load(f)
    with open(DUPLICATE_JSON, "r") as f: dup_audit = json.load(f)
    
    total_units = 0
    invalid_url_units = []
    short_units = 0
    short_units_stripped = 0
    
    exact_duplicates = dup_audit.get("exact_duplicate_groups", 0) # group count, wait, the json might have exact metrics
    
    for doc_dir in EVIDENCE_UNITS_ROOT.iterdir():
        if not doc_dir.is_dir(): continue
        eu_path = doc_dir / "evidence_units.json"
        if not eu_path.exists(): continue
        
        with open(eu_path, "r") as f:
            units = json.load(f)
        
        for u in units:
            total_units += 1
            if is_invalid_url(u.get("source_url")):
                invalid_url_units.append(u.get("evidence_unit_id", "UNKNOWN"))
                
            text = u.get("content_text", "")
            if len(text) < 10:
                short_units += 1
            if len(text.strip()) < 10:
                short_units_stripped += 1

    logger.info(f"Total Evidence Units: {total_units}")
    logger.info(f"Invalid URLs: {len(invalid_url_units)}")
    if invalid_url_units:
        logger.info(f"Samples: {invalid_url_units[:5]}")
        
    logger.info(f"Units <10 chars (raw): {short_units}")
    logger.info(f"Units <10 chars (stripped): {short_units_stripped}")
    
    logger.info("Done.")

if __name__ == "__main__":
    check()
