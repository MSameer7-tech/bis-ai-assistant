"""
Validation tests for all processed document JSON artifacts in data/processed/.
Verifies page count equivalence with raw PDFs, valid page numbering, text metadata,
clause numbering syntax, valid clause page ranges, and page_refs integrity.
"""

import json
import re
from pathlib import Path
import pymupdf
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

CLAUSE_NUM_REGEX = re.compile(r"^[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*$")


GOLDEN_REF_PATH = ROOT_DIR / "data" / "metadata" / "golden_reference_v1.json"


@pytest.fixture(scope="module")
def processed_documents():
    """Loads pilot golden reference processed document JSON artifacts."""
    assert GOLDEN_REF_PATH.exists(), "golden_reference_v1.json must exist"
    with open(GOLDEN_REF_PATH, "r", encoding="utf-8") as f:
        golden_ref = json.load(f)

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        all_manifests = json.load(f)
    manifest_map = {m["document_id"]: m for m in all_manifests}

    docs = []
    for g_doc in golden_ref["documents"]:
        doc_id = g_doc["document_id"]
        manifest = manifest_map.get(doc_id)
        if not manifest:
            continue
        json_path = PROCESSED_DIR / f"{doc_id}.json"
        assert json_path.exists(), f"Processed JSON missing for {doc_id}: {json_path}"
        with open(json_path, "r", encoding="utf-8") as f:
            docs.append((manifest, json.load(f)))
    return docs


def test_processed_documents_exist_for_all_acquired():
    """Verify that all acquired documents have a corresponding processed JSON."""
    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        doc_manifests = json.load(f)
    assert len(doc_manifests) >= 6
    for manifest in doc_manifests:
        doc_id = manifest["document_id"]
        json_path = PROCESSED_DIR / f"{doc_id}.json"
        assert json_path.exists(), f"Processed JSON missing for {doc_id}: {json_path}"


def test_1_page_count_matches_raw_pdf(processed_documents):
    """Test 1: Verifies PDF page count == JSON page count for every document."""
    for manifest, doc in processed_documents:
        raw_path = ROOT_DIR / manifest["file_path"]
        pdf_doc = pymupdf.open(str(raw_path))
        try:
            expected_pages = pdf_doc.page_count
        finally:
            pdf_doc.close()

        actual_pages = doc["extraction_metadata"]["total_pages"]
        assert len(doc["pages"]) == expected_pages, f"Page count mismatch in {manifest['document_id']}"
        assert actual_pages == expected_pages, f"Metadata page count mismatch in {manifest['document_id']}"


def test_2_every_page_has_valid_number(processed_documents):
    """Test 2: Verifies page_number != null and page numbers are 1-indexed and contiguous."""
    for manifest, doc in processed_documents:
        total_pages = doc["extraction_metadata"]["total_pages"]
        for idx, page in enumerate(doc["pages"]):
            p_num = page.get("page_number")
            assert p_num is not None, f"Null page_number in {manifest['document_id']}"
            assert p_num == idx + 1, f"Non-contiguous page_number in {manifest['document_id']}: expected {idx + 1}, got {p_num}"
            assert 1 <= p_num <= total_pages


def test_3_every_extracted_page_has_text_metadata(processed_documents):
    """Test 3: Verifies every page has char_count, word_count, extraction_method, and quality_flag."""
    for manifest, doc in processed_documents:
        for page in doc["pages"]:
            assert "text" in page, f"Missing text key in {manifest['document_id']} page {page.get('page_number')}"
            assert isinstance(page.get("char_count"), int), f"Invalid char_count in {manifest['document_id']}"
            assert isinstance(page.get("word_count"), int), f"Invalid word_count in {manifest['document_id']}"
            assert page.get("extraction_method") in ("pymupdf", "ocr"), f"Invalid extraction_method in {manifest['document_id']}"
            assert page.get("quality_flag") in ("OK", "SUSPICIOUS_LOW_TEXT", "SUSPICIOUS_EMPTY"), f"Invalid quality_flag in {manifest['document_id']}"


def test_4_clauses_have_valid_numbering(processed_documents):
    """Test 4: Verifies all clauses have valid non-empty numbering."""
    for manifest, doc in processed_documents:
        def check_clause_numbers(clause_list):
            for c in clause_list:
                c_num = c.get("clause_number")
                assert c_num, f"Empty clause_number in {manifest['document_id']}"
                assert CLAUSE_NUM_REGEX.match(c_num) or c_num.isalnum(), f"Invalid clause syntax '{c_num}' in {manifest['document_id']}"
                if c.get("subclauses"):
                    check_clause_numbers(c["subclauses"])

        check_clause_numbers(doc.get("clauses", []))


def test_5_clause_page_ranges_are_valid(processed_documents):
    """Test 5: Verifies clause page_start <= page_end and within document limits."""
    for manifest, doc in processed_documents:
        total_pages = doc["extraction_metadata"]["total_pages"]

        def check_page_ranges(clause_list):
            for c in clause_list:
                p_start = c.get("page_start")
                p_end = c.get("page_end")
                assert p_start is not None and p_end is not None, f"Missing page range in clause {c.get('clause_number')}"
                assert 1 <= p_start <= p_end <= total_pages, f"Invalid page range [{p_start}, {p_end}] in {manifest['document_id']} clause {c.get('clause_number')}"
                if c.get("subclauses"):
                    check_page_ranges(c["subclauses"])

        check_page_ranges(doc.get("clauses", []))


def test_6_page_references_actually_exist(processed_documents):
    """Test 6: Verifies that all page numbers in page_refs exist in the document."""
    for manifest, doc in processed_documents:
        total_pages = doc["extraction_metadata"]["total_pages"]

        def check_page_refs(clause_list):
            for c in clause_list:
                refs = c.get("page_refs", [])
                assert isinstance(refs, list), f"page_refs must be list in {c.get('clause_number')}"
                assert len(refs) > 0, f"Empty page_refs in {manifest['document_id']} clause {c.get('clause_number')}"
                for p in refs:
                    assert 1 <= p <= total_pages, f"Referenced page {p} out of bounds [1, {total_pages}] in {manifest['document_id']}"
                if c.get("subclauses"):
                    check_page_refs(c["subclauses"])

        check_page_refs(doc.get("clauses", []))
