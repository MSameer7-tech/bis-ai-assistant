"""
BIS Knowledge Graph Schema & Ontology Definitions (Phase 5A).
Defines heterogeneous node types, directed edge relationships, and compliance chain contracts.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    PRODUCT = "PRODUCT"
    INDIAN_STANDARD = "INDIAN_STANDARD"
    AMENDMENT = "AMENDMENT"
    QCO = "QCO"
    CONFORMITY_SCHEME = "CONFORMITY_SCHEME"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"
    SIT_SCHEDULE = "SIT_SCHEDULE"
    TESTING_LABORATORY = "TESTING_LABORATORY"
    LICENCE_RECORD = "LICENCE_RECORD"
    CRS_REGISTRATION = "CRS_REGISTRATION"
    HALLMARKING_CENTRE = "HALLMARKING_CENTRE"
    EVIDENCE_UNIT = "EVIDENCE_UNIT"


class EdgeType(str, Enum):
    COVERED_BY_STANDARD = "COVERED_BY_STANDARD"
    AMENDED_BY = "AMENDED_BY"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    MANDATES_CERTIFICATION_FOR = "MANDATES_CERTIFICATION_FOR"
    CERTIFIED_UNDER_SCHEME = "CERTIFIED_UNDER_SCHEME"
    HAS_PRODUCT_MANUAL = "HAS_PRODUCT_MANUAL"
    HAS_SIT_SCHEDULE = "HAS_SIT_SCHEDULE"
    TESTED_BY_LABORATORY = "TESTED_BY_LABORATORY"
    LICENSED_UNDER_STANDARD = "LICENSED_UNDER_STANDARD"
    REGISTERED_UNDER_STANDARD = "REGISTERED_UNDER_STANDARD"
    CONTAINS_EVIDENCE_UNIT = "CONTAINS_EVIDENCE_UNIT"


class GraphNode(BaseModel):
    """Represents a node in the BIS Knowledge Graph."""
    node_id: str = Field(..., description="Unique node ID, e.g. PROD-TMT-STEEL, IS-1786-2008")
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Represents a directed typed relationship between two nodes."""
    edge_id: str = Field(..., description="Unique edge ID, e.g. EDGE-PROD-TMT-STEEL-IS-1786-2008")
    source_id: str
    target_id: str
    edge_type: EdgeType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ComplianceChain(BaseModel):
    """End-to-end regulatory compliance trace for a product or commodity."""
    product_name: str
    product_node: Optional[GraphNode] = None
    standard_node: Optional[GraphNode] = None
    is_mandatory: bool = False
    qco_node: Optional[GraphNode] = None
    scheme_node: Optional[GraphNode] = None
    product_manual_node: Optional[GraphNode] = None
    sit_schedule_node: Optional[GraphNode] = None
    amendments: List[GraphNode] = Field(default_factory=list)
    testing_laboratories: List[GraphNode] = Field(default_factory=list)
    licences_or_registrations: List[GraphNode] = Field(default_factory=list)
    evidence_units: List[GraphNode] = Field(default_factory=list)
