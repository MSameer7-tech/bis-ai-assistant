import json
from pathlib import Path
import pytest
from ai.ingestion.extractor import extract_pdf_pages
from ai.ingestion.processor import DocumentProcessor
from ai.ingestion.structure_parser import parse_structure
from ai.ingestion.table_parser import extract_tables

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def test_extractor_preserves_pages_and_metadata():
    """Verify that PDFExtractor extracts text with page numbers and rich audit metadata."""
    sample_pdf = ROOT_DIR / "data" / "raw" / "standards" / "IS_16102_Part_1_2012.pdf"
    assert sample_pdf.exists()

    pages = extract_pdf_pages(sample_pdf)
    assert len(pages) > 0
    for idx, p in enumerate(pages):
        assert p["page_number"] == idx + 1
        assert "text" in p
        assert isinstance(p["char_count"], int)
        assert isinstance(p["word_count"], int)
        assert p["extraction_method"] == "pymupdf"
        assert p["quality_flag"] in ("OK", "SUSPICIOUS_LOW_TEXT", "SUSPICIOUS_EMPTY")


def test_structure_parser_detects_page_refs_and_annexes():
    """Verify that StructureParser identifies page_refs, multi-page spans, and annexes."""
    sample_pages = [
        {
            "page_number": 12,
            "text": "IS 16102 (Part 1) : 2012\n6 MARKING\n6.1 The lamp shall be marked with wattage.\n6.2 Marking durability test starts.",
        },
        {
            "page_number": 13,
            "text": "6.2.1 Continued durability test.\n6.3 Packaging markings.",
        },
        {
            "page_number": 14,
            "text": "ANNEX A\nGUIDELINES FOR TESTING\nDetails of test conditions.",
        },
    ]

    struct = parse_structure(sample_pages)
    assert len(struct["sections"]) >= 1
    assert len(struct["annexes"]) == 1

    # Check Annex
    annex_a = struct["annexes"][0]
    assert "ANNEX A" in annex_a["annex_id"]
    assert annex_a["page_start"] == 14
    assert 14 in annex_a["page_refs"]

    # Check Clause 6 spans pages 12 and 13
    clause_6 = next(c for c in struct["clauses"] if c["clause_number"] == "6")
    assert clause_6["page_start"] == 12
    assert clause_6["page_end"] == 13
    assert 12 in clause_6["page_refs"]
    assert 13 in clause_6["page_refs"]


def test_document_processor_canonical_schema_and_tables():
    """Verify full end-to-end processing with canonical schema, tables, annexes, and SHA-256."""
    processor = DocumentProcessor()
    doc_id = "DOC-001"

    result = processor.process_document(doc_id)

    # 1. Top level identifiers
    assert result["document_id"] == doc_id
    assert result["source_id"] == "SRC-001"

    # 2. Document metadata
    meta = result["document_metadata"]
    assert "title" in meta
    assert "standard_number" in meta
    assert "sha256" in meta
    assert len(meta["sha256"]) == 64

    # 3. Structural arrays with page_refs
    assert len(result["pages"]) > 0
    assert len(result["clauses"]) > 0
    for root_clause in result["clauses"]:
        assert "page_refs" in root_clause
        assert isinstance(root_clause["page_refs"], list)

    # 4. Tables
    assert isinstance(result["tables"], list)
    if len(result["tables"]) > 0:
        t = result["tables"][0]
        assert "table_id" in t
        assert "headers" in t
        assert "rows" in t
        assert "page_number" in t

    # 5. Extraction metadata
    ext_meta = result["extraction_metadata"]
    assert "quality_summary" in ext_meta
    assert "ocr_used" in ext_meta
