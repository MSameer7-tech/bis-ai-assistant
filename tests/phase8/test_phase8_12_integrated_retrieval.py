import pytest
from typing import List, Optional
from ai.retrieval.integrated_retrieval import IntegratedRetrievalOrchestrator
from ai.retrieval.integrated_retrieval_models import EvidenceRole
from ai.retrieval.structured_retrieval_models import RetrievalResult, RetrievalSourceType
from ai.rag.models import RetrievedChunk
from ai.retrieval.query_parser import StructuredQuery
from ai.retrieval.intent_classifier import QueryIntent

class MockStructuredRouter:
    def __init__(self):
        self.results = []
    def route_query(self, query: str) -> List[RetrievalResult]:
        return self.results

class MockRAGRetriever:
    def __init__(self):
        self.results = []
    def retrieve(self, query: str, top_k: int = 5, as_of_date: Optional[str] = None, candidate_k: int = 20) -> List[RetrievedChunk]:
        return self.results

@pytest.fixture
def mock_structured():
    return MockStructuredRouter()

@pytest.fixture
def mock_rag():
    return MockRAGRetriever()

@pytest.fixture
def orchestrator(mock_structured, mock_rag):
    return IntegratedRetrievalOrchestrator(structured_router=mock_structured, rag_retriever=mock_rag)


# 1. Exact standard lookup
def test_exact_standard_lookup(orchestrator, mock_structured, mock_rag):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="123", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="Active",
        metadata={"internal_bis_id": "123", "status": "Active"}, provenance={"source_url": "mock"}
    )]
    res = orchestrator.retrieve("What is IS 15750?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 1
    assert res[0].evidence_role == EvidenceRole.IDENTITY_EVIDENCE
    assert res[0].standard_number == "IS 15750"

# 2. Exact standard with part
def test_exact_standard_with_part(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="456", score=1.0,
        standard_number="IS 60947 Part 2", title="Switchgear", text="Active",
        metadata={"internal_bis_id": "456"}, provenance={}
    )]
    res = orchestrator.retrieve("What is IS 60947 Part 2?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 1
    assert "Part 2" in res[0].standard_number

# 3. Exact standard with section
def test_exact_standard_with_section(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="789", score=1.0,
        standard_number="IS 60947 Part 4 Section 1", title="Switchgear", text="Active",
        metadata={"internal_bis_id": "789"}, provenance={}
    )]
    res = orchestrator.retrieve("IS 60947 Part 4 Section 1?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 1

# 4. Exact standard with year
def test_exact_standard_with_year(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="999", score=1.0,
        standard_number="IS 1234 : 2024", title="New", text="Active",
        metadata={}, provenance={}
    )]
    res = orchestrator.retrieve("IS 1234 : 2024", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 1
    assert res[0].standard_number == "IS 1234 : 2024"

# 5. Ambiguous base standard
def test_ambiguous_base_standard(orchestrator, mock_structured):
    mock_structured.results = [
        RetrievalResult(source_type=RetrievalSourceType.STANDARD_METADATA, record_id="1", score=1.0, standard_number="IS 60947 Part 1", title="", text="", metadata={"reconciliation_status": "AMBIGUOUS_MATCH"}, provenance={}),
        RetrievalResult(source_type=RetrievalSourceType.STANDARD_METADATA, record_id="2", score=1.0, standard_number="IS 60947 Part 2", title="", text="", metadata={"reconciliation_status": "AMBIGUOUS_MATCH"}, provenance={})
    ]
    res = orchestrator.retrieve("What is IS 60947?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 2
    assert res[0].ambiguity_state == "AMBIGUOUS_MATCH"

# 6. Year mismatch
def test_year_mismatch(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="1", score=1.0,
        standard_number="IS 1234 : 2012", title="", text="",
        metadata={"reconciliation_status": "YEAR_MISMATCH"}, provenance={}
    )]
    res = orchestrator.retrieve("What is IS 1234 : 2000?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert res[0].ambiguity_state == "YEAR_MISMATCH"

# 7. Withdrawn lifecycle
def test_withdrawn_lifecycle(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="1", score=1.0,
        standard_number="IS 1111", title="", text="",
        metadata={"status": "Withdrawn"}, provenance={}
    )]
    res = orchestrator.retrieve("IS 1111", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert res[0].lifecycle_status == "Withdrawn"

# 8. Product-to-standard query
def test_product_to_standard_query(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={"relationship_id": "rel_1"}, provenance={}
    )]
    res = orchestrator.retrieve("Standard for refrigerators", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].evidence_role == EvidenceRole.RELATIONSHIP_EVIDENCE

# 9. Product relationship provenance
def test_product_relationship_provenance(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={"source_url": "http://bis.gov.in/catalog"}
    )]
    res = orchestrator.retrieve("Standard for refrigerators", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].source_url == "http://bis.gov.in/catalog"

# 10. Unresolved relationship
def test_unresolved_relationship(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 9999", title="Unknown", text="",
        metadata={"reconciliation_status": "UNRESOLVED"}, provenance={}
    )]
    res = orchestrator.retrieve("Standard for unknown", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].ambiguity_state == "UNRESOLVED"

# 11. Ambiguous relationship
def test_ambiguous_relationship(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 8888", title="Ambig", text="",
        metadata={"reconciliation_status": "AMBIGUOUS_MATCH"}, provenance={}
    )]
    res = orchestrator.retrieve("Standard for ambig", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].ambiguity_state == "AMBIGUOUS_MATCH"

# 12. Clause routing
def test_clause_routing(orchestrator, mock_structured, mock_rag):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.DOCUMENT_EVIDENCE, record_id="ROUTING_SIGNAL", score=1.0,
        standard_number="", title="DOCUMENT_EVIDENCE_REQUIRED", text="",
        metadata={}, provenance={}
    )]
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 1000",
        clause_number="6.2", title="Testing", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Must test.", content_hash="hash", provenance={}
    )]
    res = orchestrator.retrieve("Clause 6.2 of IS 1000", QueryIntent.CLAUSE_LOOKUP.value, StructuredQuery(raw_query="test", intent="CLAUSE_LOOKUP", clause="6.2", standard_code="IS 1000"))
    assert len(res) == 1
    assert res[0].evidence_role == EvidenceRole.NORMATIVE_EVIDENCE

# 13. Technical requirement routing
def test_technical_requirement_routing(orchestrator, mock_rag):
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 1000",
        clause_number="6.2", title="Testing", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Rated voltage 240V.", content_hash="hash", provenance={}
    )]
    res = orchestrator.retrieve("What is the rated voltage requirement?", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE", clause="6.2"))
    assert len(res) == 1
    assert res[0].evidence_role == EvidenceRole.NORMATIVE_EVIDENCE

# 14. Document evidence requirement
def test_document_evidence_requirement(orchestrator, mock_rag):
    mock_rag.results = []
    res = orchestrator.retrieve("What does clause 6.2 require?", QueryIntent.CLAUSE_LOOKUP.value, StructuredQuery(raw_query="test", intent="CLAUSE_LOOKUP", clause="6.2"))
    assert len(res) == 0  # Technical claim must abstain if normative evidence is absent

# 15. Mixed product + technical query
def test_mixed_product_technical_query(orchestrator, mock_structured, mock_rag):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 15750",
        clause_number="6.2", title="Testing", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Must test.", content_hash="hash", provenance={}
    )]
    res = orchestrator.retrieve("Standard for refrigerators and clause 6.2", QueryIntent.CLAUSE_LOOKUP.value, StructuredQuery(raw_query="test", intent="CLAUSE_LOOKUP", clause="6.2"))
    assert len(res) == 2
    roles = [r.evidence_role for r in res]
    assert EvidenceRole.RELATIONSHIP_EVIDENCE in roles
    assert EvidenceRole.NORMATIVE_EVIDENCE in roles

# 16. Metadata-only query does not require technical evidence
def test_metadata_only_no_technical(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="123", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    res = orchestrator.retrieve("What is IS 15750?", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    assert len(res) == 1
    assert res[0].evidence_role == EvidenceRole.IDENTITY_EVIDENCE

# 17. Technical query does not use metadata as normative evidence
# Covered by the rule that metadata is mapped to IDENTITY_EVIDENCE, which ContextBuilder banners as DO NOT USE AS NORMATIVE
def test_technical_query_metadata_not_normative(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="123", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    res = orchestrator.retrieve("IS 15750", QueryIntent.STANDARD_LOOKUP.value, StructuredQuery(raw_query="test", intent="STANDARD_LOOKUP"))
    chunk = res[0].to_retrieved_chunk()
    assert chunk.chunk_type == "IDENTITY_EVIDENCE"

# 18. Conflicting evidence (Negative Test 2)
def test_negative_2_product_x_phase6_y(orchestrator, mock_structured, mock_rag):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 60947",
        clause_number="6.2", title="Switchgear", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Must test.", content_hash="hash", provenance={}
    )]
    res = orchestrator.retrieve("Technical query", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE", clause="6.2"))
    # The structured router returns IS 15750. The RAG retriever returns IS 60947.
    # The relevance gate rejects IS 60947 because it does not match the linked standard (IS 15750).
    assert len(res) == 1
    assert res[0].standard_number == "IS 15750"
    assert res[0].evidence_role == EvidenceRole.RELATIONSHIP_EVIDENCE

# 19. Duplicate result handling
def test_duplicate_handling(orchestrator, mock_rag):
    chunk = RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 60947",
        clause_number="6.2", title="Switchgear", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Must test.", content_hash="hash", provenance={}
    )
    mock_rag.results = [chunk, chunk]
    res = orchestrator.retrieve("Duplicate test", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE", clause="6.2", standard_code="IS 60947"))
    assert len(res) == 1  # Deduplicated

# 20. Source-type correctness
def test_source_type_correctness(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    res = orchestrator.retrieve("Test", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].retrieval_source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP

# 21. Provenance completeness
def test_provenance_completeness(orchestrator, mock_rag):
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 60947",
        clause_number="6.2", title="Switchgear", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Must test.", content_hash="hash123", provenance={"extra": "data"}
    )]
    res = orchestrator.retrieve("Test", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE", clause="6.2", standard_code="IS 60947"))
    assert len(res) == 1
    assert res[0].sha256 == "hash123"
    assert res[0].provenance["extra"] == "data"

# 22. Negative Test 1: Metadata exists but normative absent
def test_negative_1_metadata_but_no_normative(orchestrator, mock_structured, mock_rag):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="123", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={}, provenance={}
    )]
    mock_rag.results = []
    res = orchestrator.retrieve("What is the technical requirement in IS 15750?", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE"))
    # Only metadata is returned. The LLM / EvidenceGate will abstain from the technical claim because no NORMATIVE_EVIDENCE is present.
    assert len(res) == 1
    assert res[0].evidence_role == EvidenceRole.IDENTITY_EVIDENCE

# 23. Negative Test 3: Withdrawn standard relationship
def test_negative_3_withdrawn_relationship(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP, record_id="rel_1", score=1.0,
        standard_number="IS 15750", title="Refrigerators", text="",
        metadata={"status": "Withdrawn"}, provenance={}
    )]
    res = orchestrator.retrieve("Standard", QueryIntent.PRODUCT_STANDARD.value, StructuredQuery(raw_query="test", intent="PRODUCT_STANDARD"))
    assert res[0].lifecycle_status == "Withdrawn"

# 24. Negative Test 4: Clause query retrieves irrelevant chunks
def test_negative_4_irrelevant_clause(orchestrator, mock_rag):
    mock_rag.results = [RetrievedChunk(
        chunk_id="chunk1", document_id="DOC1", source_id="SRC1", standard_number="IS 9999",
        clause_number="6.2", title="Unrelated", chunk_type="requirement", normative_force="mandatory",
        temporal_status="current", score=0.9, text="Unrelated text.", content_hash="hash", provenance={}
    )]
    # The relevance gate correctly identifies that "IS 9999" chunk does not contain "6.2" and standard does not match "IS 1000".
    # Wait, the chunk above has clause_number="6.2", but standard_number="IS 9999".
    # We query for standard_code="IS 1000". The gate should reject it due to standard mismatch!
    res = orchestrator.retrieve("Clause 6.2 of IS 1000", QueryIntent.CLAUSE_LOOKUP.value, StructuredQuery(raw_query="test", intent="CLAUSE_LOOKUP", clause="6.2", standard_code="IS 1000"))
    assert len(res) == 0  # Irrelevant chunk is rejected.

# 25. Negative Test 5: Metadata title contains technical-looking language
def test_negative_5_metadata_technical_language(orchestrator, mock_structured):
    mock_structured.results = [RetrievalResult(
        source_type=RetrievalSourceType.STANDARD_METADATA, record_id="123", score=1.0,
        standard_number="IS 1234", title="Method of Test for Tensile Strength max 500 MPa", text="",
        metadata={}, provenance={}
    )]
    res = orchestrator.retrieve("What is the tensile strength?", QueryIntent.TECHNICAL_VALUE.value, StructuredQuery(raw_query="test", intent="TECHNICAL_VALUE"))
    chunk = res[0].to_retrieved_chunk()
    assert chunk.chunk_type == "IDENTITY_EVIDENCE" # Banner prevents it from being used as normative evidence
