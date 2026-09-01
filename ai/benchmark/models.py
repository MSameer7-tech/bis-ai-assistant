"""
Pydantic Data Models for Corpus-Grounded Master Benchmark Framework.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FailureSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # False retrieval on unsupported material, standard collision/hijacking, numerical error
    HIGH = "HIGH"          # Wrong clause, inverted normative force, missing mandatory citation
    MEDIUM = "MEDIUM"      # Target standard in Top-3/Top-5 but not Rank-1
    LOW = "LOW"            # Non-critical warning or formatting discrepancy


class BenchmarkCase(BaseModel):
    """Canonical test case schema for corpus-grounded benchmark."""
    id: str = Field(..., description="Unique stable test ID (e.g. PROD-CON-001, TECH-DOC034-7.1-001)")
    category: str = Field(..., description="Benchmark category (e.g. construction, electrical, safety, precedence)")
    query: str = Field(..., description="Natural language user question")
    query_type: str = Field(..., description="Query type (STANDARD_LOOKUP, TECHNICAL_VALUE, SAFETY_ABSTENTION, etc.)")

    expected_status: str = Field("VERIFIED", description="Expected status: VERIFIED, ABSTAINED, CLARIFICATION_REQUIRED")

    expected_standard: Optional[str] = Field(None, description="Expected Indian Standard number")
    expected_document_id: Optional[str] = Field(None, description="Expected BIS Document ID (DOC-xxx)")
    expected_clause: Optional[str] = Field(None, description="Expected clause or table identifier")

    expected_parameter: Optional[str] = Field(None, description="Canonical parameter identifier")
    expected_value: Optional[float] = Field(None, description="Expected physical value")
    expected_unit: Optional[str] = Field(None, description="Expected physical unit")

    expected_normative_force: Optional[str] = Field(None, description="Expected normative force (MANDATORY, INFORMATIVE, etc.)")

    expected_product: Optional[str] = Field(None, description="Canonical product name")
    expected_domain: Optional[str] = Field(None, description="Taxonomy product domain")

    abstention_reason: Optional[str] = Field(None, description="Expected abstention enum value if refused")

    forbidden_standards: List[str] = Field(default_factory=list, description="Standards that must NEVER be cited")

    source_chunk_ids: List[str] = Field(default_factory=list, description="Grounding chunk IDs from corpus")
    generation_source: str = Field(..., description="Provenance of test generation (e.g. DOC-034::Clause 7.1)")
    corpus_version: str = Field("v1.0", description="Version of BIS corpus used to generate this case")


class CaseEvaluationResult(BaseModel):
    """Detailed evaluation result for an individual benchmark case."""
    test_id: str
    category: str
    query: str
    query_type: str
    passed: bool
    failure_severity: Optional[FailureSeverity] = None

    expected: Dict[str, Any]
    actual: Dict[str, Any]
    checks: Dict[str, bool] = Field(default_factory=dict)

    elapsed_ms: float = 0.0
    error_message: Optional[str] = None


class CategoryMetrics(BaseModel):
    """Aggregated performance metrics for a category or query type."""
    name: str
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    accuracy: float = 0.0
    top1_accuracy: float = 0.0
    top3_accuracy: float = 0.0
    safety_rate: float = 0.0

    critical_failures: int = 0
    high_failures: int = 0
    medium_failures: int = 0
    low_failures: int = 0
    avg_latency_ms: float = 0.0


class MasterBenchmarkReport(BaseModel):
    """Master benchmark report capturing all categories, query types, and release gate metrics."""
    timestamp: str
    corpus_stats: Dict[str, Any] = Field(default_factory=dict)
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    overall_accuracy: float = 0.0

    critical_failures: int = 0
    high_failures: int = 0
    medium_failures: int = 0
    low_failures: int = 0

    categories: Dict[str, CategoryMetrics] = Field(default_factory=dict)
    query_types: Dict[str, CategoryMetrics] = Field(default_factory=dict)
    results: List[CaseEvaluationResult] = Field(default_factory=list)
    release_gate_passed: bool = False
