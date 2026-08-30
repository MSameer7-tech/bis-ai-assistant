"""
Semantic Schema and Semantic ID Generators for Phase 2D and Temporal Lineage (Steps 13 & 14).
Produces stable, canonical semantic identifiers across all normalized knowledge objects:
- Document: DOC-001
- Section: SEC-DOC001-08
- Clause: CLAUSE-DOC001-8.1.1
- Requirement: REQ-DOC001-8.1.1-001
- Test: TEST-DOC001-8.1.1-001
- Parameter: PARAM-insulation_resistance
- Standard: STD-IS15885-P1
- Term: TERM-self_ballasted_led_lamp
- Table: TABLE-DOC001-T03
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def sanitize_id_token(token: str) -> str:
    """Sanitizes text strings into clean alphanumeric ID components."""
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", str(token)).strip("_")
    return cleaned.upper()


def make_section_id(doc_id: str, sec_num: str) -> str:
    doc_clean = doc_id.replace("-", "").upper()
    sec_clean = str(sec_num).zfill(2) if str(sec_num).isdigit() else sanitize_id_token(sec_num)
    return f"SEC-{doc_clean}-{sec_clean}"


def make_clause_id(doc_id: str, clause_num: str) -> str:
    doc_clean = doc_id.replace("-", "").upper()
    return f"CLAUSE-{doc_clean}-{clause_num}"


def make_requirement_id(doc_id: str, clause_num: str, seq: int = 1) -> str:
    doc_clean = doc_id.replace("-", "").upper()
    return f"REQ-{doc_clean}-{clause_num}-{seq:03d}"


def make_test_id(doc_id: str, clause_num: str, seq: int = 1) -> str:
    doc_clean = doc_id.replace("-", "").upper()
    return f"TEST-{doc_clean}-{clause_num}-{seq:03d}"


def make_parameter_id(param_name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", param_name.strip()).lower().strip("_")
    return f"PARAM-{clean}"


def make_standard_id(std_num: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", std_num.strip()).upper().strip("_")
    clean = clean.replace("PART_", "P").replace("SECTION_", "S").replace("SEC_", "S")
    return f"STD-{clean}"


def make_term_id(term_name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", term_name.strip()).lower().strip("_")
    return f"TERM-{clean}"


def make_table_id(doc_id: str, table_num: str) -> str:
    doc_clean = doc_id.replace("-", "").upper()
    t_clean = str(table_num).replace("TABLE-", "").replace("TABLE", "").replace("T", "").zfill(2)
    return f"TABLE-{doc_clean}-T{t_clean}"


# Pydantic Schemas for Knowledge Layer Validation

class ProvenanceModel(BaseModel):
    document_id: str
    source_id: str
    standard: str
    clause: str
    page: int
    pages: List[int] = Field(default_factory=list)
    section: Optional[str] = None
    original_text: str


class RequirementModel(BaseModel):
    entity_type: str = "requirement"
    requirement_type: str
    requirement_id: str
    status: str = "mandatory"
    clause: str
    subject: str
    parameter: str
    operator: str
    original_value: Optional[str] = None
    normalized: Optional[Dict[str, Any]] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    test: Optional[Dict[str, Any]] = None
    acceptance_criterion: Optional[Dict[str, Any]] = None
    exceptions: Optional[str] = None
    evidence: str
    source_pages: List[int]
    provenance: ProvenanceModel
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    temporal_status: str = "current"  # "current", "superseded", "pending", "provisional"
    superseded_by: Optional[str] = None
    amendment_id: Optional[str] = None
