import unittest
import hashlib
import json
import os

from scripts.phase12_2_structured_extraction import (
    Extractor,
    DerivedKnowledge,
    Relationship,
    extract_is_number,
    get_provenance
)

V22_PATH = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"

class TestPhase12_2StructuredExtraction(unittest.TestCase):

    def setUp(self):
        self.extractor = Extractor()

    def test_01_v22_immutability(self):
        self.assertTrue(os.path.exists(V22_PATH))
        with open(V22_PATH, 'rb') as f:
            v22_bytes = f.read()
        sha = hashlib.sha256(v22_bytes).hexdigest()
        self.assertEqual(sha, V22_EXPECTED_SHA, "v22 SHA256 mutated!")
        self.assertEqual(len(v22_bytes.decode('utf-8').strip().split('\n')), 1135)

    def test_02_provenance_preservation(self):
        rec = {
            "record_id": "TEST-1",
            "source_url": "http://x",
            "source_sha256": "hash",
            "authority": "TIER_1_NORMATIVE",
            "retrieved_at": "now",
            "domain": "LABORATORIES",
            "title": "Title",
            "content": "Content"
        }
        prov = get_provenance(rec)
        self.assertEqual(prov["source_record_id"], "TEST-1")
        self.assertEqual(prov["corpus_version"], "v22")
        self.assertEqual(prov["provenance_status"], "PROVENANCE_COMPLETE")

    def test_03_one_to_many_extraction(self):
        # A single LIMS lab record can yield a lab entity and multiple scope/fee entities.
        rec = {
            "record_id": "LIMS-1",
            "record_type": "RECOGNIZED_LAB",
            "source_url": "http://x",
            "source_sha256": "hash",
            "authority": "TIER_1_NORMATIVE",
            "retrieved_at": "now",
            "domain": "LABORATORIES",
            "title": "My Lab",
            "content": '{"lab_name": "My Lab", "scopes": [{"is_number": "IS 1", "fee": "10"}, {"is_number": "IS 2", "fee": "20"}]}'
        }
        entities = self.extractor.extract(rec)
        self.assertTrue(len(entities) > 1, "Should produce multiple entities for a lab with scopes")
        for e in entities:
            self.assertEqual(e.provenance["source_record_id"], "LIMS-1")

    def test_04_invalid_record_no_fabrication(self):
        rec = {
            "record_id": "LAB-UNKNOWN_79dcb12d",
            "source_url": "http://x",
            "source_sha256": None,
            "authority": "BIS_PUBLISHED",
            "retrieved_at": "now",
            "domain": "LABORATORIES",
            "title": "8102006 Laboratory",
            "content": '{"lab_code": "UNKNOWN_79dcb12d"}'
        }
        entities = self.extractor.extract(rec)
        # Should return an UNKNOWN or INACCESSIBLE entity with NO substantive relationships
        self.assertEqual(len(entities), 1)
        self.assertIn(entities[0].evidence_status, ["UNKNOWN", "INACCESSIBLE_SOURCE", "NOT_ESTABLISHED"])
        self.assertEqual(len(entities[0].relationships), 0, "No fabricated relationships allowed")

    def test_05_raw_vs_normalized(self):
        norm, raw = extract_is_number("We test IS 1234 (Part 1)")
        self.assertEqual(raw, "We test IS 1234 (Part 1)")
        self.assertEqual(norm, "IS 1234")

    def test_06_determinism(self):
        rec = {
            "record_id": "TEST-DET",
            "source_url": "http://x",
            "source_sha256": "hash",
            "authority": "TIER_1_NORMATIVE",
            "retrieved_at": "now",
            "domain": "LABORATORIES",
            "title": "Det Lab",
            "content": "Content"
        }
        e1 = self.extractor.extract(rec)
        e2 = self.extractor.extract(rec)
        
        d1 = json.dumps([e.to_dict() for e in e1], sort_keys=True)
        d2 = json.dumps([e.to_dict() for e in e2], sort_keys=True)
        self.assertEqual(d1, d2)

if __name__ == '__main__':
    unittest.main()
