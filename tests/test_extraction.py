import json
from pathlib import Path
import pytest
from ai.ingestion.extractor import extract_pdf_pages
from ai.ingestion.processor import DocumentProcessor
from ai.ingestion.structure_parser import parse_structure

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


def test_structure_parser_detects_clauses():
    """Verify that StructureParser identifies standard clauses and sections."""
    sample_pages = [
        {
            "page_number": 1,
            "text": "IS 16102 (Part 1) : 2012\n1 SCOPE\n1.1 This standard specifies safety requirements.\n1.2 Applicability covers 60W LED.",
        },
        {
            "page_number": 2,
            "text": "8 INSULATION RESISTANCE\n8.1 Insulation resistance shall be not less than 4 MΩ.\n8.2 Electric strength test shall apply 4000 V.",
        },
    ]

    struct = parse_structure(sample_pages)
    assert len(struct["sections"]) >= 2
    assert len(struct["clauses"]) >= 4

    clause_nums = [c["clause_number"] for c in struct["clauses"]]
    assert "1.1" in clause_nums
    assert "8.1" in clause_nums

    c_81 = next(c for c in struct["clauses"] if c["clause_number"] == "8.1")
    assert c_81["page_start"] == 2
    assert c_81["page_end"] == 2
    assert "4 MΩ" in c_81["content"]


def test_document_processor_end_to_end():
    """Verify full end-to-end processing producing structured JSON with quality summary."""
    processor = DocumentProcessor()
    doc_id = "DOC-001"

    result = processor.process_document(doc_id)

    assert result["document_id"] == doc_id
    assert result["total_pages"] > 0
    assert result["total_clauses"] > 0
    assert "quality_summary" in result
    assert result["quality_summary"]["total_pages"] == result["total_pages"]

    out_file = PROCESSED_DIR / f"{doc_id}.json"
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        saved_doc = json.load(f)

    assert saved_doc["document_id"] == doc_id
    assert len(saved_doc["pages"]) == saved_doc["total_pages"]
    assert len(saved_doc["clauses"]) == saved_doc["total_clauses"]
    assert "quality_flag" in saved_doc["pages"][0]
