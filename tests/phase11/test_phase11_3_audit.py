import unittest
from scripts.phase11_3_corpus_audit import (
    validate_record, 
    extract_date, 
    extract_is_number, 
    classify_record_type,
    detect_conflict,
    evaluate_gap,
    extract_fee_metrics,
    get_provenance_status,
    is_exact_duplicate
)

class TestPhase11_3Audit(unittest.TestCase):

    def test_01_integrity_valid_record(self):
        rec = {
            "record_id": "123",
            "source_sha256": "abc",
            "source_url": "http://bis.gov.in/1",
            "domain": "LABORATORIES",
            "authority": "BIS_PUBLISHED",
            "content": "test",
            "title": "title"
        }
        err = validate_record(rec)
        self.assertIsNone(err)

    def test_02_integrity_missing_field(self):
        rec = {"record_id": "123", "domain": "LABORATORIES"}
        err = validate_record(rec)
        self.assertIsNotNone(err)

    def test_03_date_extraction_year(self):
        self.assertEqual(extract_date("Guidelines for 2026"), "2026")

    def test_04_date_extraction_amendment(self):
        self.assertEqual(extract_date("Amendment August 2026"), "August 2026")

    def test_05_date_extraction_supersession(self):
        self.assertEqual(extract_date("This order is superseded by 2026 order"), "SUPERSEDED")

    def test_06_is_extraction(self):
        self.assertEqual(extract_is_number("IS 1234"), ("IS 1234", "IS 1234"))
        self.assertEqual(extract_is_number("IS 1234 (Part 1)"), ("IS 1234", "IS 1234 (Part 1)"))

    def test_07_record_classification(self):
        self.assertEqual(classify_record_type({"record_type": "FAQ"}), "FAQ")
        self.assertEqual(classify_record_type({"title": "List of labs", "domain": "LABORATORIES"}), "LABORATORY")
        self.assertEqual(classify_record_type({"content": "fee field", "domain": "LABORATORIES"}), "FEE")

    def test_08_conflict_detection(self):
        r1 = {"record_id": "1", "is_number": "IS 1234", "fee": "5000", "lab": "Lab A"}
        r2 = {"record_id": "2", "is_number": "IS 1234", "fee": "5000", "lab": "Lab A"}
        r3 = {"record_id": "3", "is_number": "IS 1234", "fee": "6000", "lab": "Lab A"}
        r4 = {"record_id": "4", "is_number": "IS 1234", "scope": "Part 1"}
        r5 = {"record_id": "5", "is_number": "IS 1234", "scope": "Part 2"}
        r6 = {"record_id": "6", "title": "Amendment 2026", "superseded_by": "2027"}

        self.assertEqual(detect_conflict(r1, r2), "NO_CONFLICT")
        self.assertEqual(detect_conflict(r4, r5), "SAME_SUBJECT_DIFFERENT_SCOPE")
        self.assertEqual(detect_conflict(r1, r3), "POTENTIAL_CONFLICT")
        self.assertEqual(detect_conflict(r6, r6), "SUPERSESSION_CANDIDATE")

    def test_09_gap_analysis(self):
        self.assertEqual(evaluate_gap(has_evidence=True, accessible=True, complete=True), "AVAILABLE_EVIDENCE")
        self.assertEqual(evaluate_gap(has_evidence=False, accessible=True, complete=False), "MISSING_EVIDENCE")
        self.assertEqual(evaluate_gap(has_evidence=True, accessible=False, complete=True), "INACCESSIBLE_EVIDENCE")
        self.assertEqual(evaluate_gap(has_evidence=True, accessible=True, complete=False), "PARTIAL_EVIDENCE")

    def test_10_provenance(self):
        complete_r = {"source_url": "u", "source_sha256": "s", "authority": "a", "retrieved_at": "r"}
        self.assertEqual(get_provenance_status(complete_r), "PROVENANCE_COMPLETE")
        
        missing_r = {}
        self.assertEqual(get_provenance_status(missing_r), "PROVENANCE_MISSING")

        incomplete_r = {"source_url": "u", "source_sha256": "s"}
        self.assertEqual(get_provenance_status(incomplete_r), "PROVENANCE_INCOMPLETE")

    def test_11_fee_metrics(self):
        r1 = {"content": "testing charge: 100 INR, effective 2026-01-01"}
        m = extract_fee_metrics(r1)
        self.assertTrue(m["is_fee"])
        self.assertTrue(m["has_amount"])
        self.assertTrue(m["has_currency"])
        self.assertTrue(m["has_date"])
        
        r2 = {"content": "this has a price"}
        m2 = extract_fee_metrics(r2)
        self.assertFalse(m2["is_fee"])  # "price" isn't a direct explicit structured fee field match by default heuristic

    def test_12_exact_duplicate(self):
        r1 = {"record_id": "1", "source_sha256": "hash", "source_url": "url", "content": "c"}
        r2 = {"record_id": "1", "source_sha256": "hash", "source_url": "url", "content": "c"}
        r3 = {"record_id": "2", "source_sha256": "hash", "source_url": "url", "content": "c"}
        self.assertTrue(is_exact_duplicate(r1, r2))
        self.assertFalse(is_exact_duplicate(r1, r3))

if __name__ == '__main__':
    unittest.main()
