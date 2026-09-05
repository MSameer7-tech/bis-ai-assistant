import unittest
import json
import os
import shutil
from pathlib import Path
from scripts.phase12_3_entity_relationship_index import index_data, V22_EXPECTED_SHA, PHASE12_2_EXPECTED_SHA

class TestPhase12_3EntityRelationshipIndex(unittest.TestCase):
    def setUp(self):
        self.output_dir = Path("data/derived/phase12/entity_relationship_index_v1")
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def test_01_input_sha_verification(self):
        res = index_data()
        self.assertEqual(res["v22_sha"], V22_EXPECTED_SHA)
        self.assertEqual(res["p12_2_sha"], PHASE12_2_EXPECTED_SHA)

    def test_02_no_dangling_relationships(self):
        res = index_data()
        self.assertEqual(res["dangling_relationships"], 0)

    def test_03_no_unsupported_relationships(self):
        res = index_data()
        self.assertEqual(res["unsupported_relationships"], 0)

    def test_04_no_silently_dropped_objects(self):
        res = index_data()
        # The sum of entity counts minus STANDARD (which are implicit) should equal Phase 12.2 object count
        total_entities = sum(v for k, v in res["entity_counts"].items() if k != "STANDARD")
        # Subtract the implicit laboratories we manufactured to satisfy relationships
        total_implicit_labs = res.get("implicit_laboratories_count", 0)
        self.assertEqual(total_entities - total_implicit_labs, res["p12_2_count"])

    def test_05_unknown_preservation(self):
        res = index_data()
        unknown_entities_count = res["entity_counts"].get("UNKNOWN", 0)
        self.assertEqual(unknown_entities_count, 1)

    def test_06_determinism(self):
        # Run 1
        res1 = index_data()
        r1 = Path("data/derived/phase12/entity_relationship_index_v1/relationships.jsonl").read_bytes()
        
        # Run 2
        res2 = index_data()
        r2 = Path("data/derived/phase12/entity_relationship_index_v1/relationships.jsonl").read_bytes()
        
        self.assertEqual(r1, r2)
        
    def test_07_duplicate_relationship_detection(self):
        res = index_data()
        self.assertEqual(res["duplicate_relationship_ids"], 0)

if __name__ == '__main__':
    unittest.main()
