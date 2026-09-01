"""
Verification Data Models for BIS Grounding and Compliance.
"""
from pydantic import BaseModel, Field


class NumericalVerification(BaseModel):
    """Audit verification for numerical technical parameters."""
    parameter: str = Field(..., description="Parameter name (e.g. yield_strength, air_delivery, elongation)")
    claim_value: float = Field(..., description="Value claimed in answer")
    claim_unit: str = Field(..., description="Unit claimed in answer (e.g. N/mm², m³/min, %)")
    source_value: float = Field(..., description="Authoritative value in retrieved evidence")
    source_unit: str = Field(..., description="Authoritative unit in evidence")
    passed: bool = Field(..., description="Whether claim matches authoritative evidence value")
    tolerance_error: float = Field(0.0, description="Numerical discrepancy or error delta")
