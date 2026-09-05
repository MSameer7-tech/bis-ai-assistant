import unittest
import os
import platform
from pathlib import Path
from scripts.phase12_a2_embedding_environment import run, V22_EXPECTED_SHA, PHASE12_2_EXPECTED_SHA

class TestPhase12A2EmbeddingEnvironment(unittest.TestCase):
    def test_01_immutability(self):
        res = run()
        self.assertEqual(res["v22_sha"], V22_EXPECTED_SHA)
        self.assertEqual(res["p12_2_sha"], PHASE12_2_EXPECTED_SHA)
        self.assertIsNotNone(res["p12_3_fp"])
        self.assertIsNotNone(res["bm25_sha"])

    def test_02_environment_and_status(self):
        res = run()
        self.assertEqual(res["status"], "FAIL")
        self.assertTrue("3.14" in platform.python_version() or "3.9" in platform.python_version())

if __name__ == '__main__':
    unittest.main()
