import unittest
import os
from pathlib import Path
from scripts.phase12_a1_vector_index import run, V22_EXPECTED_SHA, PHASE12_2_EXPECTED_SHA

class TestPhase12A1VectorIndex(unittest.TestCase):
    def test_01_immutability(self):
        res = run()
        self.assertEqual(res["v22_sha"], V22_EXPECTED_SHA)
        self.assertEqual(res["p12_2_sha"], PHASE12_2_EXPECTED_SHA)
        self.assertIsNotNone(res["p12_3_fp"])
        self.assertIsNotNone(res["bm25_sha"])

    def test_02_embedding_dependency(self):
        res = run()
        # Because we intentionally aborted installation, we expect status to FAIL
        self.assertEqual(res["status"], "FAIL")

if __name__ == '__main__':
    unittest.main()
