import re
import hashlib
from typing import Optional, Tuple, Dict, Any
from ai.acquisition.lims_scope.models import TestingCharge

def normalize_standard(raw: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    Normalizes standard strings like:
    IS 4246
    IS 4246 : 2000
    IS 4246 (Part 1)
    IS 4246 : 2000 (Part 1)
    """
    normalized = raw.strip()
    part = None
    section = None
    year = None
    
    # Simple regex extractions
    part_match = re.search(r'\(?Part\s*(\d+)\)?', normalized, re.IGNORECASE)
    if part_match:
        part = part_match.group(1)
        
    sec_match = re.search(r'\(?Sec\w*\s*(\d+)\)?', normalized, re.IGNORECASE)
    if sec_match:
        section = sec_match.group(1)
        
    year_match = re.search(r':\s*(\d{4})', normalized)
    if year_match:
        year = year_match.group(1)
        
    # Remove the extracted parts from the base number
    base = re.sub(r'\(?Part\s*\d+\)?', '', normalized, flags=re.IGNORECASE)
    base = re.sub(r'\(?Sec\w*\s*\d+\)?', '', base, flags=re.IGNORECASE)
    base = re.sub(r':\s*\d{4}', '', base)
    
    base = base.strip()
    
    return base, part, section, year

def parse_testing_charge(raw: str) -> Optional[TestingCharge]:
    """
    Extracts testing charge and taxes from raw string.
    Example: "Rs. 4000 (excluding GST)" -> amount 4000
    """
    if not raw or not isinstance(raw, str):
        return None
        
    raw = raw.strip()
    if not raw or raw.lower() in ['na', 'n/a', '-', 'nil']:
        return None
        
    amount = 0.0
    # Try to find a numeric value
    # E.g. "4000", "4,000", "4000.00"
    num_match = re.search(r'[\d,]+(?:\.\d+)?', raw)
    if num_match:
        val_str = num_match.group(0).replace(',', '')
        try:
            amount = float(val_str)
        except ValueError:
            pass
            
    if amount > 0:
        tax_included = 'including tax' in raw.lower() or 'incl gst' in raw.lower()
        return TestingCharge(
            amount=amount,
            currency="INR",
            tax_included=tax_included,
            raw_value=raw,
            charge_context="specific laboratory/test"
        )
    return None

def hash_row(cells: list) -> str:
    """Generate a deterministic hash for a scope row to aid in duplicate detection."""
    combined = "|".join(str(c).strip().lower() for c in cells)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()
