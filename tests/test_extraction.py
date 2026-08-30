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


def test_structure_parser_detects_hierarchical_clauses():
    """Verify that StructureParser identifies sections and constructs hierarchical subclause trees."""
    sample_pages = [
        {
            "page_number": 1,
            "text": "IS 16102 (Part 1) : 2012\n1 SCOPE\n1.1 This standard specifies safety requirements.\n1.2 Applicability covers 60W LED.",
        },
        {
            "page_number": 2,
            "text": "8 INSULATION RESISTANCE\n8.1 Insulation resistance shall be not less than 4 MΩ.\n8.2 Electric strength test.\n8.2.1 Test voltage shall apply 4000 V.",
        },
    ]

    struct = parse_structure(sample_pages)
    assert len(struct["sections"]) >= 2
    assert struct["flat_clauses_count"] >= 5

    # Check root clause nesting
    clause_8 = next(c for c in struct["clauses"] if c["clause_number"] == "8")
    assert clause_8["depth"] == 1
    assert len(clause_8["subclauses"]) >= 2

    # Check 8.2 has subclause 8.2.1
    c_82 = next(c for c in clause_8["subclauses"] if c["clause_number"] == "8.2")
    assert len(c_82["subclauses"]) >= 1
    assert c_82["subclauses"][0]["clause_number"] == "8.2.1"


def test_document_processor_canonical_schema_end_to_end():
    """Verify full end-to-end processing producing the canonical 2C.7 JSON schema with SHA-256."""
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

    # 3. Structural arrays
    assert isinstance(result["pages"], list)
    assert isinstance(result["sections"], list)
    assert isinstance(result["clauses"], list)
    assert isinstance(result["tables"], list)
    assert isinstance(result["annexes"], list)

    # 4. Extraction metadata
    ext_meta = result["extraction_metadata"]
    assert ext_meta["extraction_method"] == "pymupdf"
    assert "quality_summary" in ext_meta

    # 5. File persistence
    out_file = PROCESSED_DIR / f"{doc_id}.json"
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        saved_doc = json.load(f)

    assert saved_doc["document_metadata"]["sha256"] == meta["sha256"]
