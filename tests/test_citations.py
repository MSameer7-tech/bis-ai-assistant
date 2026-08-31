"""
Tests for Phase 4 Batch 4: citation.py
"""
import pytest
from ai.rag.models import RetrievedChunk
from ai.rag.citation import CitationExtractor


@pytest.fixture
def evidence_chunks():
    return [
        RetrievedChunk(
            chunk_id="DOC-001-v001::8.1.1::REQ-001",
            document_id="DOC-001",
            version_id="DOC-001-v001",
            source_id="SRC-001",
            standard_number="IS 16102 (Part 1) : 2012",
            clause_number="8.1.1",
            pages=[9],
            chunk_type="requirement",
            normative_force="mandatory",
            temporal_status="current",
            valid_from="2012-08-01",
            score=0.032,
            text="The insulation resistance shall not be less than 4 MΩ.",
            content_hash="abc123hash",
            provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
        )
    ]


def test_valid_citation_extraction_and_verification(evidence_chunks):
    extractor = CitationExtractor()
    answer_text = (
        "The minimum insulation resistance is 4 MΩ.\n\n"
        "### Citations & Provenance\n"
        "- IS 16102 (Part 1) : 2012, Clause 8.1.1, Page(s) 9 (Document ID: DOC-001)"
    )

    citations = extractor.extract_citations(answer_text, evidence_chunks)
    assert len(citations) == 1
    assert citations[0].verified is True
    assert citations[0].standard_number == "IS 16102 (Part 1) : 2012"
    assert citations[0].clause == "8.1.1"
    assert citations[0].pages == [9]
    assert citations[0].chunk_id == "DOC-001-v001::8.1.1::REQ-001"


def test_invalid_hallucinated_citation_detected_as_unverified(evidence_chunks):
    extractor = CitationExtractor()
    hallucinated_answer = (
        "The minimum insulation resistance is 4 MΩ.\n\n"
        "### Citations & Provenance\n"
        "- IS 99999 : 2099, Clause 99.9, Page(s) 999 (Document ID: DOC-999)"
    )

    citations = extractor.extract_citations(hallucinated_answer, evidence_chunks)
    assert len(citations) == 1
    assert citations[0].verified is False
    assert citations[0].chunk_id == "UNMATCHED"
