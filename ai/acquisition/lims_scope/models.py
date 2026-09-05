from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Laboratory:
    lab_code: str
    lab_name: str
    laboratory_type: str  # BIS_RECOGNIZED, BIS_EMPANELLED, BIS_OWNED
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    recognition_status: Optional[str] = None
    validity_date: Optional[str] = None
    source_url: Optional[str] = None
    retrieved_at: Optional[str] = None
    source_sha256: Optional[str] = None
    scope_status: str = "DISCOVERED"

@dataclass
class TestingCharge:
    amount: float
    currency: str
    tax_included: bool
    raw_value: str
    charge_context: str

@dataclass
class ScopeRecord:
    scope_record_id: str
    laboratory_identity: str
    raw_standard_reference: str
    normalized_standard_number: str
    part: Optional[str] = None
    section: Optional[str] = None
    edition_year: Optional[str] = None
    product_material: Optional[str] = None
    characteristic_test: Optional[str] = None
    test_method: Optional[str] = None
    clause_reference: Optional[str] = None
    range_limit: Optional[str] = None
    sample_requirement: Optional[str] = None
    unit: Optional[str] = None
    testing_charge: Optional[TestingCharge] = None
    tax_information: Optional[str] = None
    turnaround_time: Optional[str] = None
    scope_validity: Optional[str] = None
    source_url: Optional[str] = None
    source_sha256: Optional[str] = None
    retrieved_at: Optional[str] = None
    table_index: int = 0
    row_index: int = 0
    extraction_method: str = "HTML_TABLE_PARSE"
    duplicate_group_id: Optional[str] = None
    source_row_hash: Optional[str] = None
