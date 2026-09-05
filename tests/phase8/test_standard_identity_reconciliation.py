import pytest
from scripts.normalize_and_reconcile_standards import classify_and_extract

class TestStandardIdentityExtraction:
    def test_basic_base_number(self):
        res = classify_and_extract("10322")
        assert res['classification'] == "STANDARD_CANDIDATE"
        assert res['identity']['base_number'] == "10322"
        assert res['identity']['standard_prefix'] == "IS"

        res = classify_and_extract("IS 10322")
        assert res['classification'] == "CONFIDENT_STANDARD_CANDIDATE"
        assert res['identity']['base_number'] == "10322"
        assert res['identity']['standard_prefix'] == "IS"

    def test_parts_and_sections(self):
        res = classify_and_extract("10322 (Part 5/Sec 1)")
        assert res['classification'] == "STANDARD_CANDIDATE_WITH_SECTION"
        assert res['identity']['base_number'] == "10322"
        assert res['identity']['part'] == "5"
        assert res['identity']['section'] == "1"

        res = classify_and_extract("IS 10322 (Part 5/Sec 1) : 2026")
        assert res['classification'] == "STANDARD_CANDIDATE_WITH_SECTION"
        assert res['identity']['part'] == "5"
        assert res['identity']['section'] == "1"
        assert res['identity']['edition_year'] == "2026"

        res = classify_and_extract("302 (Part 1)")
        assert res['classification'] == "STANDARD_CANDIDATE_WITH_PART"
        assert res['identity']['base_number'] == "302"
        assert res['identity']['part'] == "1"
        assert res['identity']['section'] is None
        assert res['identity']['edition_year'] is None

    def test_clause_rejection(self):
        res = classify_and_extract("Clause 4.14")
        assert res['classification'] == "CLAUSE_REFERENCE"

        res = classify_and_extract("Clause 4.14 of IS 10613: 2014")
        assert res['classification'] == "CLAUSE_REFERENCE"

    def test_filename_rejection(self):
        res = classify_and_extract("some_document.pdf")
        assert res['classification'] == "FILENAME_REFERENCE"

        res = classify_and_extract("IS_10322_Part_5.pdf")
        assert res['classification'] == "FILENAME_CONTAINING_STANDARD_CANDIDATE"
        assert res['identity']['base_number'] == "10322"
        assert res['identity']['part'] == "5"

    def test_dual_standards(self):
        res = classify_and_extract("IS 10322 (Part 5/Sec 1) :2026/ IEC 60598-2-1 : 2020")
        assert res['classification'] == "DUAL_STANDARD_REFERENCE"
        assert res['identity']['base_number'] == "10322"
        assert res['identity']['part'] == "5"
        assert res['identity']['edition_year'] == "2026"
        assert len(res['referenced_standards']) == 1
        assert "60598" in res['referenced_standards'][0]['raw']

    def test_ambiguous(self):
        res = classify_and_extract("2024")
        assert res['classification'] in ["AMBIGUOUS", "NON_STANDARD_NUMERIC"]
