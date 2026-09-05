"""
Machine-readable per-product evidence chain policy definitions (Phase 4 Batch F).
Prevents the audit system from treating structurally impossible relationships (e.g. CRS for Cement or ISI for Laptops) as missing evidence.
"""
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field


class ProductChainPolicy(BaseModel):
    """
    Formally defines the required, optional, and structurally excluded evidence nodes for a product category.
    """
    policy_id: str = Field(..., description="Unique policy identifier")
    category_name: str = Field(..., description="Canonical product category name")
    scheme_code: str = Field(..., description="Conformity assessment scheme e.g. SCHEME-I, SCHEME-II, SCHEME-IV")
    is_qco_mandatory: bool = Field(default=True, description="True if mandatory under Quality Control Order")
    required_nodes: List[str] = Field(..., description="Evidence nodes that MUST be present for COMPLETE status")
    optional_nodes: List[str] = Field(default_factory=list, description="Evidence nodes that may be present")
    excluded_nodes: List[str] = Field(default_factory=list, description="Evidence nodes that are structurally invalid for this product")


# Machine-readable product chain policy matrix
CHAIN_POLICIES: Dict[str, ProductChainPolicy] = {
    # 1. Scheme-I Mandatory Industrial & Consumer Goods (ISI Mark)
    "MANDATORY_ISI_INDUSTRIAL": ProductChainPolicy(
        policy_id="POLICY-SCHEME-I-INDUSTRIAL",
        category_name="Mandatory ISI Industrial Goods (Steel, Cement, Cables, Pipes)",
        scheme_code="SCHEME-I",
        is_qco_mandatory=True,
        required_nodes=[
            "STANDARD", "QCO", "SCHEME", "PRODUCT_MANUAL", "SIT", "TEST", "LABORATORY", "LICENCE"
        ],
        optional_nodes=["CONSUMER", "AMENDMENTS"],
        excluded_nodes=["CRS", "HALLMARKING"]
    ),
    "MANDATORY_ISI_APPLIANCES": ProductChainPolicy(
        policy_id="POLICY-SCHEME-I-APPLIANCES",
        category_name="Mandatory ISI Consumer Appliances (Fans, Stoves, Cookers, Helmets, Heaters)",
        scheme_code="SCHEME-I",
        is_qco_mandatory=True,
        required_nodes=[
            "STANDARD", "QCO", "SCHEME", "PRODUCT_MANUAL", "SIT", "TEST", "LABORATORY", "LICENCE", "CONSUMER"
        ],
        optional_nodes=["AMENDMENTS"],
        excluded_nodes=["CRS", "HALLMARKING"]
    ),
    "MANDATORY_ISI_FOOD_WATER": ProductChainPolicy(
        policy_id="POLICY-SCHEME-I-FOOD-WATER",
        category_name="Mandatory ISI Food & Water (Packaged Water, Milk Powder)",
        scheme_code="SCHEME-I",
        is_qco_mandatory=True,
        required_nodes=[
            "STANDARD", "QCO", "SCHEME", "PRODUCT_MANUAL", "SIT", "TEST", "LABORATORY", "LICENCE", "CONSUMER"
        ],
        optional_nodes=["AMENDMENTS"],
        excluded_nodes=["CRS", "HALLMARKING"]
    ),

    # 2. Scheme-II Mandatory Electronics & IT Goods (CRS Registration)
    "MANDATORY_CRS_ELECTRONICS": ProductChainPolicy(
        policy_id="POLICY-SCHEME-II-CRS",
        category_name="Mandatory Electronics & IT Equipment (LEDs, Batteries, IT Hardware)",
        scheme_code="SCHEME-II",
        is_qco_mandatory=True,
        required_nodes=[
            "STANDARD", "QCO", "SCHEME", "TEST", "LABORATORY", "CRS", "CONSUMER"
        ],
        optional_nodes=["PRODUCT_MANUAL", "SIT", "AMENDMENTS"],
        excluded_nodes=["LICENCE", "HALLMARKING"]
    ),

    # 3. Scheme-IV Mandatory Precious Metals (Hallmarking)
    "MANDATORY_HALLMARKING_GOLD": ProductChainPolicy(
        policy_id="POLICY-SCHEME-IV-HALLMARK",
        category_name="Mandatory Gold & Silver Jewellery Hallmarking",
        scheme_code="SCHEME-IV",
        is_qco_mandatory=True,
        required_nodes=[
            "STANDARD", "QCO", "SCHEME", "TEST", "LABORATORY", "HALLMARKING", "CONSUMER"
        ],
        optional_nodes=["AMENDMENTS"],
        excluded_nodes=["LICENCE", "CRS", "PRODUCT_MANUAL"]
    ),

    # 4. Voluntary / Standard Scope Products
    "VOLUNTARY_STANDARD_SCOPE": ProductChainPolicy(
        policy_id="POLICY-VOLUNTARY-STANDARD-SCOPE",
        category_name="Voluntary / Non-QCO Indian Standards",
        scheme_code="SCHEME-I",
        is_qco_mandatory=False,
        required_nodes=["STANDARD", "SCHEME"],
        optional_nodes=["PRODUCT_MANUAL", "SIT", "TEST", "LABORATORY", "LICENCE", "CONSUMER", "AMENDMENTS"],
        excluded_nodes=["CRS", "HALLMARKING"]
    )
}


def get_policy_for_product(standard_id: str, scheme_id: str, is_mandatory: bool) -> ProductChainPolicy:
    """Resolves the authoritative chain policy for any product / standard pair."""
    std_upper = standard_id.upper().strip()
    
    if "1417" in std_upper or "2112" in std_upper:
        return CHAIN_POLICIES["MANDATORY_HALLMARKING_GOLD"]
    
    if scheme_id == "SCHEME-II" or any(s in std_upper for s in ["16046", "16102", "13252", "616", "16242"]):
        return CHAIN_POLICIES["MANDATORY_CRS_ELECTRONICS"]
    
    if is_mandatory:
        if any(s in std_upper for s in ["14543", "13428", "1165"]):
            return CHAIN_POLICIES["MANDATORY_ISI_FOOD_WATER"]
        if any(s in std_upper for s in ["374", "4246", "2347", "4151", "2082", "302"]):
            return CHAIN_POLICIES["MANDATORY_ISI_APPLIANCES"]
        return CHAIN_POLICIES["MANDATORY_ISI_INDUSTRIAL"]
    
    return CHAIN_POLICIES["VOLUNTARY_STANDARD_SCOPE"]
