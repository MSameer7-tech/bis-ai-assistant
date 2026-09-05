"""
Pydantic API Schemas for Phase 5 Production Intelligence Endpoints.
Defines strict API contracts for Query Orchestrator, Certification Chain Reasoner,
Regulatory Timeline Engine, and Evidentiary Statistics.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class IntelligenceQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language regulatory question or product query", example="I manufacture 5-star ceiling fans. Do I need BIS certification and what tests are required?")
    as_of_date: Optional[str] = Field(None, description="ISO timestamp (YYYY-MM-DD) for historical evaluation", example="2024-01-01")
    top_k: int = Field(5, description="Number of vector/chunk context candidates", ge=1, le=20)


class IntelligenceQueryResponse(BaseModel):
    status: str = Field(..., description="Regulatory evaluation status (VERIFIED, REFUSAL, PARTIAL_EVIDENCE, HISTORICAL_CONTEXT)")
    query: str
    verdict: Dict[str, Any] = Field(..., description="Executive verdict dictionary with product, standard, scheme, mandatory status")
    answer_markdown: str = Field(..., description="Full rich Markdown answer including tables, paths, and citations")
    certification_chain: Optional[Dict[str, Any]] = Field(None, description="8-node structured certification chain")
    timeline: Optional[Dict[str, Any]] = Field(None, description="Chronological timeline of revisions, QCOs, and amendments")
    test_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="Normative test parameters and limits")
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list, description="Authoritative cryptographic evidence ledger")
    citations: List[str] = Field(default_factory=list, description="List of citation titles")
    warnings: List[str] = Field(default_factory=list, description="Safety or temporal advisory warnings")
    confidence: float = Field(0.95, description="Confidence score")


class ChainResolveRequest(BaseModel):
    product_or_standard: str = Field(..., description="Product name or Indian Standard number (e.g. 'Electric Ceiling Fans' or 'IS 1786')")
    as_of_date: Optional[str] = Field(None, description="Point-in-time date for historical chain evaluation")


class TimelineResolveRequest(BaseModel):
    standard_or_product: str = Field(..., description="Standard code or product (e.g. 'IS 374' or 'IS 16102')")
    as_of_date: Optional[str] = Field(None, description="Target evaluation date")


class EvidenceStatsResponse(BaseModel):
    total_evidence_records: int
    verified_evidence_records: int
    partial_evidence_records: int
    verified_evidence_pct: float
    total_graph_edges: int
    evidence_bound_edges_pct: float
    total_canonical_products: int
    total_governed_standards: int
    total_qcos_indexed: int
