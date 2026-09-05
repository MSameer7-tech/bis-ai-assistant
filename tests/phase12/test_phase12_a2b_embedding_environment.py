import unittest
import os
import json
from scripts.phase12_a2b_embedding_environment import run, V22_EXPECTED_SHA, PHASE12_2_EXPECTED_SHA

class TestPhase12A2BEmbeddingEnvironment(unittest.TestCase):
    def test_01_immutability(self):
        res = run()
        self.assertEqual(res["v22_sha"], V22_EXPECTED_SHA)
        self.assertEqual(res["p12_2_sha"], PHASE12_2_EXPECTED_SHA)
        self.assertIsNotNone(res["p12_3_fp"])
        self.assertIsNotNone(res["bm25_sha"])

    def test_02_environment_and_status(self):
        res = run()
        self.assertEqual(res["status"], "PASS")
        self.assertIsNotNone(res["sim_b"])
        self.assertIsNotNone(res["sim_c"])
        self.assertGreater(res["sim_b"], res["sim_c"])

if __name__ == '__main__':
    unittest.main()
