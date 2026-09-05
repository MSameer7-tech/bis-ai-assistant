import pytest
from scripts.phase8_10_metadata_recovery import normalize_family_record, match_candidate_to_family

class TestDeterministicMatching:
    def test_normalize_family_record(self):
        rec1 = normalize_family_record("BIS -- IS/IEC 60947 : Part 2 : 2016")
        assert rec1["base_number"] == "60947"
        assert rec1["part"] == "2"
        assert rec1["section"] is None
        assert rec1["edition_year"] == "2016"
        assert rec1["prefix"] == "IS/IEC"

        rec2 = normalize_family_record("BIS -- IS/IEC 60947 : PART 4 : Sec 1 : 2023")
        assert rec2["base_number"] == "60947"
        assert rec2["part"] == "4"
        assert rec2["section"] == "1"
        assert rec2["edition_year"] == "2023"

        rec3 = normalize_family_record("BIS -- IS 15750 : 2006")
        assert rec3["base_number"] == "15750"
        assert rec3["part"] is None
        assert rec3["edition_year"] == "2006"

    def test_exact_base_match(self):
        candidate = {"base_number": "15750", "part": None, "section": None, "edition_year": "2006"}
        family = [
            {"base_number": "15750", "part": None, "section": None, "edition_year": "2006", "internal_id": "1"}
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "MATCHED"
        assert res["matched_record"]["internal_id"] == "1"

    def test_part_match(self):
        candidate = {"base_number": "60947", "part": "2", "section": None, "edition_year": "2016"}
        family = [
            {"base_number": "60947", "part": "1", "section": None, "edition_year": "2016", "internal_id": "1"},
            {"base_number": "60947", "part": "2", "section": None, "edition_year": "2016", "internal_id": "2"}
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "MATCHED"
        assert res["matched_record"]["internal_id"] == "2"

    def test_section_match(self):
        candidate = {"base_number": "60947", "part": "4", "section": "1", "edition_year": "2023"}
        family = [
            {"base_number": "60947", "part": "4", "section": "2", "edition_year": "2020", "internal_id": "1"},
            {"base_number": "60947", "part": "4", "section": "1", "edition_year": "2023", "internal_id": "2"}
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "MATCHED"
        assert res["matched_record"]["internal_id"] == "2"

    def test_ambiguous_match(self):
        candidate = {"base_number": "60947", "part": None, "section": None, "edition_year": None}
        family = [
            {"base_number": "60947", "part": "1", "section": None, "edition_year": "2016", "internal_id": "1"},
            {"base_number": "60947", "part": "2", "section": None, "edition_year": "2016", "internal_id": "2"}
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "AMBIGUOUS_MATCH"
        assert len(res["matched_records"]) == 2

    def test_no_part_match(self):
        candidate = {"base_number": "60947", "part": "99", "section": None, "edition_year": None}
        family = [
            {"base_number": "60947", "part": "1", "section": None, "edition_year": "2016", "internal_id": "1"},
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "PART_MISMATCH"

    def test_year_mismatch(self):
        candidate = {"base_number": "15750", "part": None, "section": None, "edition_year": "2026"}
        family = [
            {"base_number": "15750", "part": None, "section": None, "edition_year": "2006", "internal_id": "1"}
        ]
        res = match_candidate_to_family(candidate, family)
        assert res["status"] == "YEAR_MISMATCH"
