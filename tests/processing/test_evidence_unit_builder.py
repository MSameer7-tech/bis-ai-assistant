import json
from pathlib import Path
from unittest.mock import patch, mock_open

from ai.processing.document_extractor import ExtractedDocument, ExtractedClause
from ai.processing.evidence_unit_builder import EvidenceUnitBuilder

def test_source_url_propagation():
    """Test source_url propagation from acquisition metadata -> EvidenceUnit"""
    builder = EvidenceUnitBuilder()
    
    mock_meta = {
        "source": {
            "canonical_source_url": "https://example.bis.gov.in/doc1.pdf"
        },
        "acquisition": {
            "sha256": "574c459187f7b3c70f0d849edc0018ec6836a6bb0075590fd6e0d1cb9dc82715"
        },
        "document": {
            "document_id": "TEST-DOC-1",
            "document_family_id": "TEST",
            "document_type": "INDIAN_STANDARD"
        }
    }
    
    doc = ExtractedDocument(
        document_id="TEST-DOC-1",
        document_family_id="TEST",
        title="Test Doc",
        document_type="INDIAN_STANDARD",
        is_success=True,
        metadata=mock_meta,
        clauses=[
            ExtractedClause(
                clause_number="1.0",
                heading="Scope",
                content_text="This is a test scope."
            )
        ]
    )
    
    units, err = builder.build_evidence_units(doc)
    assert err is None
    assert len(units) == 1
    assert units[0].source_url == "https://example.bis.gov.in/doc1.pdf"
    assert units[0].parent_raw_sha256 == "574c459187f7b3c70f0d849edc0018ec6836a6bb0075590fd6e0d1cb9dc82715"

def test_source_url_preservation_missing():
    """Test missing source_url remains explicitly UNKNOWN_URL and is not fabricated."""
    builder = EvidenceUnitBuilder()
    
    mock_meta = {
        "acquisition": {
            "sha256": "574c459187f7b3c70f0d849edc0018ec6836a6bb0075590fd6e0d1cb9dc82715"
        },
        "document": {
            "document_id": "TEST-DOC-1",
            "document_family_id": "TEST",
            "document_type": "PRODUCT_MANUAL"
        }
    }
    
    doc = ExtractedDocument(
        document_id="TEST-DOC-1",
        document_family_id="TEST",
        title="Test Doc",
        document_type="PRODUCT_MANUAL",
        is_success=True,
        metadata=mock_meta,
        clauses=[
            ExtractedClause(
                clause_number="1.0",
                heading="Scope",
                content_text="This is a test scope."
            )
        ]
    )
    
    units, err = builder.build_evidence_units(doc)
    assert err is None
    assert len(units) == 1
    assert units[0].source_url == "UNKNOWN_URL"
