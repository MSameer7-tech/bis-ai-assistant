"""
Phase 6A: Canonical Identifier Generator for BIS Entities.
Provides deterministic, immutable canonical IDs across all BIS entity types:
- Standards: STD-IS-1786-2024
- Amendments: AMD-IS-1786-2024-1
- Product Manuals: PM-IS-1786-1
- Schemes of Inspection & Testing (SIT): SIT-IS-1786-1
- Quality Control Orders: QCO-STEEL-2024
- Laboratories: LAB-CL-SAHIBABAD
- Committees: COMM-MTD-04
- Products: PRD-000001
"""
import re
from typing import Optional


def normalize_std_code(std_num: str) -> str:
    """Normalizes standard string (e.g. 'is/iec 60065' -> 'IS-IEC-60065')."""
    clean = std_num.strip().upper()
    clean = re.sub(r"[/:\s]+", "-", clean)
    clean = re.sub(r"-+", "-", clean)
    return clean


def make_standard_canonical_id(standard_number: str, edition: Optional[str] = "2024") -> str:
    std_code = normalize_std_code(standard_number)
    ed = str(edition).strip() if edition else "2024"
    return f"STD-{std_code}-{ed}"


def make_amendment_canonical_id(standard_number: str, edition: Optional[str] = "2024", amendment_number: int = 1) -> str:
    std_code = normalize_std_code(standard_number)
    ed = str(edition).strip() if edition else "2024"
    return f"AMD-{std_code}-{ed}-{amendment_number}"


def make_product_manual_canonical_id(standard_number: str, manual_code: Optional[str] = "1") -> str:
    std_code = normalize_std_code(standard_number)
    code = str(manual_code).replace("/", "-").replace(" ", "-").strip()
    return f"PM-{std_code}-{code}"


def make_sit_canonical_id(standard_number: str, sit_code: Optional[str] = "1") -> str:
    std_code = normalize_std_code(standard_number)
    code = str(sit_code).replace("/", "-").replace(" ", "-").strip()
    return f"SIT-{std_code}-{code}"


def make_qco_canonical_id(qco_identifier: str) -> str:
    clean = re.sub(r"[^A-Z0-9]+", "-", qco_identifier.upper().strip()).strip("-")
    return f"QCO-{clean[:32]}"


def make_lab_canonical_id(lab_name: str, location: Optional[str] = None) -> str:
    base = f"{lab_name}-{location}" if location else lab_name
    clean = re.sub(r"[^A-Z0-9]+", "-", base.upper().strip()).strip("-")
    return f"LAB-{clean[:32]}"


def make_committee_canonical_id(dept_code: str, committee_number: str) -> str:
    dept = dept_code.upper().strip()
    num = str(committee_number).replace(dept, "").strip(" -:")
    return f"COMM-{dept}-{num.zfill(2)}"


def make_product_canonical_id(index: int) -> str:
    return f"PRD-{index:06d}"
