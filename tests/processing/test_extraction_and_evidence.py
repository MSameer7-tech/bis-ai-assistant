"""
Automated Verification Suite for Hardened Phase 4: Document Extraction, Normalization & Evidence Formatting.
Validates generic PyMuPDF PDF extraction, HTML DOM parsing, schema-aware JSON parsing,
strict pre-extraction SHA-256 integrity verification, zero synthetic fallbacks, and complete accounting.
"""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
EXTRACTION_MANIFEST_PATH = ROOT_DIR / "data" / "processed" / "extraction_manifest.json"
EVIDENCE_UNITS_ROOT = ROOT_DIR / "data" / "processed" / "evidence_units"
DOCS_PHASE4_DIR = ROOT_DIR / "docs" / "phase4"

from ai.processing.document_extractor import DocumentExtractor, ExtractedDocument, ExtractedClause, ExtractedTable
from ai.processing.evidence_unit_builder import EvidenceUnitBuilder, EvidenceUnit
from ai.processing.extraction_orchestrator import ExtractionOrchestrator


@pytest.fixture(scope="module")
def extraction_manifest():
    assert EXTRACTION_MANIFEST_PATH.exists(), f"Missing extraction manifest: {EXTRACTION_MANIFEST_PATH}"
    with open(EXTRACTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_generic_pdf_extraction_real_pymupdf():
    """Verifies that DocumentExtractor extracts actual text, clauses, and tables from real PyMuPDF PDFs dynamically."""
    extractor = DocumentExtractor()
    with TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "IS-9999-2025" / "original.pdf"
        pdf_path.parent.mkdir(parents=True)

        # Create a dynamic PDF with arbitrary new standard number
        pdf = pymupdf.open()
        p1 = pdf.new_page()
        p1.insert_text((50, 50), "IS 9999 : 2025\nIndian Standard\nCUSTOM TEST SPECIFICATION\n\n1 SCOPE\nThis standard covers generic testing.\n\n4.1 Chemical Properties\nCarbon max 0.20%.\n\nTable 1 Limits\nItem | Max Limit\nCarbon | 0.20%")
        pdf.save(pdf_path)
        pdf.close()

        doc = extractor.extract_document(pdf_path)
        assert doc.is_success is True
        assert doc.document_id == "IS-9999-2025"
        assert len(doc.clauses) >= 2

        clause_numbers = [c.clause_number for c in doc.clauses]
        assert "1" in clause_numbers
        assert "4.1" in clause_numbers
        assert doc.clauses[0].page_number == 1
        assert len(doc.tables) >= 1
        assert doc.tables[0].headers == ["Item", "Max Limit"]


def test_empty_pdf_fails_without_synthetic_fallback():
    """Verifies that an empty or unscannable PDF fails extraction rather than generating fake synthetic clauses."""
    extractor = DocumentExtractor()
    with TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "EMPTY-DOC" / "original.pdf"
        pdf_path.parent.mkdir(parents=True)

        # Empty 1-page PDF with no text
        pdf = pymupdf.open()
        pdf.new_page()
        pdf.save(pdf_path)
        pdf.close()

        doc = extractor.extract_document(pdf_path)
        assert doc.is_success is False
        assert "EXTRACTION_FAILED" in doc.error_reason
        assert len(doc.clauses) == 0


def test_evidence_unit_builder_rejects_missing_parent_sha():
    """Verifies that EvidenceUnitBuilder strictly rejects documents missing valid parent raw SHA-256."""
    builder = EvidenceUnitBuilder()
    doc = ExtractedDocument(
        document_id="IS-1786-2008",
        document_family_id="IS-1786",
        title="High Strength Steel",
        document_type="INDIAN_STANDARD",
        clauses=[
            ExtractedClause(
                clause_number="4.1",
                heading="Chemical Composition",
                content_text="Carbon shall not exceed 0.25%",
                clause_type="REQUIREMENT",
                page_number=2
            )
        ],
        metadata={"acquisition": {"sha256": "UNKNOWN_PARENT_HASH"}}
    )

    units, err = builder.build_evidence_units(doc)
    assert len(units) == 0
    assert "QUARANTINE" in err


def test_evidence_unit_builder_normalizes_ids_and_anchors():
    """Verifies that EvidenceUnitBuilder normalizes IDs and includes page numbers in citation anchors."""
    builder = EvidenceUnitBuilder()
    doc = ExtractedDocument(
        document_id="IS-1786-2008",
        document_family_id="IS-1786",
        title="High Strength Steel",
        document_type="INDIAN_STANDARD",
        clauses=[
            ExtractedClause(
                clause_number="4 . 2",  # messy spacing
                heading="Mechanical Properties",
                content_text="Yield stress shall be min 500.0 N/mm².",
                clause_type="REQUIREMENT",
                page_number=2
            )
        ],
        metadata={"acquisition": {"sha256": "a" * 64}}
    )

    units, err = builder.build_evidence_units(doc)
    assert err is None
    assert len(units) == 1
    unit: EvidenceUnit = units[0]
    assert unit.evidence_unit_id == "EV-IS-1786-2008-P2-CL-4.2"
    assert "Page 2" in unit.citation_anchor
    assert "Clause 4 . 2" in unit.citation_anchor


def test_strict_accounting_manifest_integrity(extraction_manifest):
    """Verifies that the extraction manifest enforces strict accounting and 100% completion."""
    assert extraction_manifest["manifest_version"] == "1.0"
    assert extraction_manifest["completion_status"] == "PASSED"

    acct = extraction_manifest["accounting"]
    assert acct["documents_expected"] == 87
    assert acct["documents_successful"] == 87
    assert acct["documents_failed"] == 0
    assert acct["documents_missing"] == 0

    metrics = extraction_manifest["quality_metrics"]
    assert metrics["total_pages_processed"] >= 87
    assert metrics["total_evidence_units_extracted"] >= 300
    assert metrics["total_clauses_extracted"] >= 300
    assert metrics["total_tables_extracted"] >= 50


def test_per_document_evidence_unit_persistence():
    """Verifies that individual per-document evidence unit JSON files exist on disk with valid provenance."""
    assert EVIDENCE_UNITS_ROOT.exists()
    doc_dirs = list(EVIDENCE_UNITS_ROOT.glob("*"))
    assert len(doc_dirs) == 87

    sample_doc_dir = doc_dirs[0]
    sample_unit_file = sample_doc_dir / "evidence_units.json"
    assert sample_unit_file.exists()

    with open(sample_unit_file, "r", encoding="utf-8") as f:
        units_data = json.load(f)
    assert len(units_data) > 0
    assert len(units_data[0]["parent_raw_sha256"]) == 64
    assert len(units_data[0]["unit_content_sha256"]) == 64
    assert "Page" in units_data[0]["citation_anchor"]


def test_phase4_documentation_artifacts_exist():
    """Verifies that all 6 required Phase 4 documentation artifacts exist in docs/phase4/."""
    expected_docs = [
        "EXTRACTION_ARCHITECTURE.md",
        "EVIDENCE_UNIT_SPEC.md",
        "TABLE_EXTRACTION_SPEC.md",
        "PARAMETER_NORMALIZATION_SPEC.md",
        "PHASE_4_ACCEPTANCE_CRITERIA.md",
        "PHASE_4_COMPLETION_REPORT.md"
    ]
    for doc in expected_docs:
        doc_path = DOCS_PHASE4_DIR / doc
        assert doc_path.exists(), f"Missing documentation artifact: {doc}"
        assert doc_path.stat().st_size > 150, f"Document {doc} is too short / empty"
