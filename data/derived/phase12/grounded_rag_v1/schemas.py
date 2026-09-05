from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

class QueryIntent(Enum):
    STANDARD_LOOKUP = "STANDARD_LOOKUP"
    PRODUCT_STANDARD = "PRODUCT_STANDARD"
    CERTIFICATION_REQUIREMENT = "CERTIFICATION_REQUIREMENT"
    QCO_APPLICABILITY = "QCO_APPLICABILITY"
    LABORATORY_LOOKUP = "LABORATORY_LOOKUP"
    LABORATORY_SCOPE = "LABORATORY_SCOPE"
    TESTING_FEE = "TESTING_FEE"
    TESTING_REQUIREMENT = "TESTING_REQUIREMENT"
    LICENCE_PROCEDURE = "LICENCE_PROCEDURE"
    REGISTRATION = "REGISTRATION"
    HALLMARKING = "HALLMARKING"
    HUID = "HUID"
    CONSUMER_COMPLAINT = "CONSUMER_COMPLAINT"
    FAQ_GUIDANCE = "FAQ_GUIDANCE"
    HISTORICAL_VERSION = "HISTORICAL_VERSION"
    CURRENT_STATUS = "CURRENT_STATUS"
    GENERAL_BIS_INFORMATION = "GENERAL_BIS_INFORMATION"
    UNKNOWN = "UNKNOWN"

class EvidenceStatus(Enum):
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    NO_EVIDENCE = "NO_EVIDENCE"
    CONFLICT = "CONFLICT"

class ConfidenceLabel(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class SupportStatus(Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"

@dataclass
class EvidenceObject:
    # Source Metadata
    source_record_id: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    document_title: Optional[str] = None
    
    # Standard
    standard_number: Optional[str] = None
    standard_title: Optional[str] = None
    standard_revision: Optional[str] = None
    
    # Laboratory
    laboratory_id: Optional[str] = None
    laboratory_name: Optional[str] = None
    laboratory_type: Optional[str] = None
    
    # Scope
    scope_id: Optional[str] = None
    product: Optional[str] = None
    grade_type_size: Optional[str] = None
    validity_date: Optional[str] = None
    
    # Test
    test_parameter: Optional[str] = None
    test_method: Optional[str] = None
    clause: Optional[str] = None
    
    # Fee
    fee_amount: Optional[float] = None
    fee_currency: Optional[str] = None
    fee_type: Optional[str] = None
    effective_date: Optional[str] = None
    conditions: Optional[str] = None
    remarks: Optional[str] = None
    
    # Relationships
    relationships: List[Dict[str, str]] = field(default_factory=list) # e.g. [{"subject": "IS 616", "predicate": "HAS_FEE", "object": "22000"}]
    
    # Retrieval
    retrieval_unit_id: Optional[str] = None
    entity_type: Optional[str] = None
    authority: Optional[int] = None
    provenance_status: Optional[str] = None
    text: Optional[str] = None

@dataclass
class Claim:
    claim_id: str
    claim_type: str # "BIS_FACT" or "META"
    text: str
    
    # Binding
    subject_entity: Optional[str] = None
    predicate: Optional[str] = None
    object_entity: Optional[str] = None
    
    supporting_evidence_ids: List[str] = field(default_factory=list)
    support_status: SupportStatus = SupportStatus.UNSUPPORTED
    source_record_ids: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)

@dataclass
class Subquestion:
    id: str
    query: str
    intent: QueryIntent
    evidence_status: EvidenceStatus = EvidenceStatus.NO_EVIDENCE
    confidence: Dict[str, Any] = field(default_factory=lambda: {"label": "NONE", "score": 0.0, "reasons": [], "calibration_status": "BASELINE_UNCALIBRATED"})
    gaps: List[Dict[str, Any]] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    unsupported_claims: List[Claim] = field(default_factory=list)
    answer_text: str = ""
