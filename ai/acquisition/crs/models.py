"""
Pydantic data models for BIS Compulsory Registration Scheme (CRS Records) - Phase 4 Batch D.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class CRSStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    UNDER_RENEWAL = "UNDER_RENEWAL"
    SUSPENDED = "SUSPENDED"


class CRSRecord(BaseModel):
    """
    Authoritative record for an Electronics / IT Compulsory Registration Scheme (CRS) Registration.
    """
    model_config = ConfigDict(populate_by_name=True)

    registration_number: str = Field(..., description="Unique 8-digit R-number e.g. R-41001234")
    standard_number: str = Field(..., description="Applicable Indian Standard e.g. IS 16046 (Part 2) : 2018")
    product_category: str = Field(..., description="CRO / CRS regulated electronics category")
    brand_name: str = Field(..., description="Registered brand trademark e.g. SAMSUNG, APPLE, PHILIPS")
    model_numbers: List[str] = Field(default_factory=list, description="Registered model numbers under series approval")
    
    # Manufacturing Entity
    manufacturer_name: str = Field(..., description="Registered manufacturing corporate entity")
    manufacturing_country: str = Field(default="India", description="Country of manufacturing origin")
    factory_address: str = Field(..., description="Physical manufacturing plant address")
    
    # Conformity & Testing
    scheme_code: str = Field(default="SCHEME-II", description="Conformity assessment scheme (Scheme-II: CRS)")
    status: CRSStatus = Field(default=CRSStatus.ACTIVE, description="Current registration validity status")
    test_report_number: Optional[str] = Field(None, description="Accredited lab test report reference number")
    testing_laboratory: Optional[str] = Field(None, description="BIS recognized laboratory where testing was performed")
    valid_from: str = Field(..., description="Registration effective grant date YYYY-MM-DD")
    valid_until: str = Field(..., description="Registration expiry date YYYY-MM-DD")
    
    # Provenance
    source_portal: str = Field(default="BIS CRS Portal (crsbis.in)", description="Data provenance")
    evidence_backed: bool = Field(default=True, description="Whether registration is backed by verified test report")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional technical series metadata")
