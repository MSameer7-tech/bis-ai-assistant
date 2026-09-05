"""
Pydantic data models for BIS and recognized laboratory network entities (Phase 4 Batch D).
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LabType(str, Enum):
    CENTRAL = "CENTRAL"
    REGIONAL = "REGIONAL"
    BRANCH = "BRANCH"
    NABL_ACCREDITED = "NABL_ACCREDITED"
    RECOGNIZED_PARTNER = "RECOGNIZED_PARTNER"
    PRIVATE_RECOGNIZED = "PRIVATE_RECOGNIZED"


class LabStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RECOGNITION_EXPIRED = "RECOGNITION_EXPIRED"


class LaboratoryRecord(BaseModel):
    """
    Authoritative record for a laboratory in the BIS testing network.
    """
    model_config = ConfigDict(populate_by_name=True)

    lab_id: str = Field(..., description="Unique canonical lab identifier e.g. LAB-001")
    lab_name: str = Field(..., description="Full official name of the laboratory")
    short_code: str = Field(..., description="Abbreviation e.g. CL, WROL, EROL, CPRI")
    lab_type: LabType = Field(..., description="Classification: CENTRAL, REGIONAL, BRANCH, NABL_ACCREDITED, etc.")
    status: LabStatus = Field(default=LabStatus.ACTIVE, description="Current operational recognition status")
    
    # Location details
    address: str = Field(..., description="Physical street address / campus")
    city: str = Field(..., description="City / town")
    state: str = Field(..., description="State / UT")
    pincode: Optional[str] = Field(None, description="6-digit PIN code")
    
    # Contact
    contact_email: Optional[str] = Field(None, description="Official email address")
    contact_phone: Optional[str] = Field(None, description="Official telephone")
    website_url: Optional[str] = Field(None, description="Website / portal URL")
    
    # Scope & Capabilities
    disciplines: List[str] = Field(default_factory=list, description="Testing disciplines e.g. Electrical, Chemical, Mechanical")
    standards_tested: List[str] = Field(default_factory=list, description="IS standards the lab is equipped and accredited to test")
    product_categories: List[str] = Field(default_factory=list, description="Product families tested")
    
    # Accreditation & Recognition
    nabl_cert_number: Optional[str] = Field(None, description="NABL Certificate Number if applicable")
    valid_from: Optional[str] = Field(None, description="Recognition start date YYYY-MM-DD")
    valid_until: Optional[str] = Field(None, description="Recognition expiry date YYYY-MM-DD")
    is_bis_owned: bool = Field(default=False, description="True if owned/operated by BIS directly")
    
    # Provenance
    source_portal: str = Field(default="BIS LPPD Laboratory Network & NABL Directory", description="Data provenance")
    evidence_backed: bool = Field(default=True, description="Whether lab record has verified capabilities and scope")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional technical metadata")
