from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class LicenceRecord:
    record_id: str
    record_type: str
    title: str
    content: str
    source_url: str
    source_type: str  # HTML, PDF, API
    issuing_authority: str  # BIS
    authority_level: str  # SUPPORTING_GUIDANCE, PROCEDURAL, STATUTORY
    retrieved_at: str
    source_sha256: str
    parent_source_url: Optional[str] = None
    access_status: str = "ACQUIRED" # ACQUIRED, FAILED, WAF_BLOCKED, SESSION_REQUIRED, ACCESS_RESTRICTED
    extraction_status: str = "SUCCESS" # SUCCESS, FAILED
    record_status: str = "ACTIVE"
    
    # Domain Specific fields
    information_type: Optional[str] = None # APPLICATION_PROCEDURE, SCHEME_INFO, FEES, CRS, FMCS, FAQ
    procedure_step: Optional[str] = None
    eligibility: Optional[str] = None
    required_document: Optional[str] = None
    fee: Optional[float] = None
    validity: Optional[str] = None
    official_portal: Optional[str] = None
    verification_method: Optional[str] = None
