"""
Certification Procedures Data Models
Authoritative schemas for BIS licensing procedures, application workflows, surveillance, renewal, fees, and timelines.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ProcedureRecord(BaseModel):
    """Authoritative record for a BIS certification / licensing workflow procedure."""
    procedure_id: str = Field(..., description="Unique procedure ID (e.g., PROC-APP-NORMAL, PROC-APP-SIMPLIFIED, PROC-RENEWAL)")
    title: str = Field(..., description="Official title of the procedure")
    scheme_id: str = Field(..., description="Linked conformity assessment scheme (e.g., SCHEME-I, SCHEME-II, FMCS)")
    stage_name: str = Field(..., description="Stage in lifecycle (Application, Inspection, Testing, Grant, Surveillance, Renewal, Suspension)")
    description: str = Field(..., description="Detailed normative workflow instructions")
    required_documents: List[str] = Field(default_factory=list, description="Mandatory documentation and proof of facilities required")
    inspection_details: str = Field(..., description="Scope of factory/premises inspection and officer audit checklists")
    sampling_procedure: str = Field(..., description="Dual sample drawing, sealing, and laboratory routing instructions")
    timelines_days: str = Field(..., description="Statutory processing time / service level agreement (e.g., 30 days, 90 days)")
    fees_structure: str = Field(..., description="Statutory fee schedule (Application fee, Inspection charges, Marking fee)")
    renewal_terms: Optional[str] = Field(None, description="Terms for licence renewal, validity periods, and production returns")
    suspension_conditions: Optional[str] = Field(None, description="Grounds and procedure for stop-marking, suspension, and cancellation")
    source_url: str = Field(..., description="Authoritative BIS portal / regulatory guideline URL")
    document_id: Optional[str] = Field(None, description="Internal document identifier")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp of ingestion")
