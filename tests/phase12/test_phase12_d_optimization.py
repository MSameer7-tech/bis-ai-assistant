import unittest
import json
import os
import sys

sys.path.append("/Users/sameer/.gemini/antigravity-ide/brain/8ae9fa33-c4f9-46d1-8353-641188a30582/")
from scripts.phase12d_benchmark import run_benchmark

from data.derived.phase12.grounded_rag_v1.answer_engine import GroundedRAGEngine
from scripts.phase12_b_hybrid_retrieval import RetrievalData
from sentence_transformers import SentenceTransformer

class TestPhase12DOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rdata = RetrievalData()
        cls.model = SentenceTransformer('data/models/embeddings/all-MiniLM-L6-v2', device='cpu')
        
    def test_determinism(self):
        """Phase 12.D must be absolutely deterministic. Running the benchmark twice must yield identical metrics and statuses."""
        engine = GroundedRAGEngine(self.rdata, self.model)
        metrics_1, results_1 = run_benchmark(engine)
        metrics_2, results_2 = run_benchmark(engine)
        
        self.assertEqual(metrics_1["total_queries"], metrics_2["total_queries"], "Total queries mismatch")
        self.assertAlmostEqual(metrics_1["mrr"], metrics_2["mrr"], places=5, msg="MRR mismatch across runs")
        self.assertAlmostEqual(metrics_1["recall_5"], metrics_2["recall_5"], places=5, msg="Recall@5 mismatch across runs")
        self.assertAlmostEqual(metrics_1["precision_5"], metrics_2["precision_5"], places=5, msg="Precision@5 mismatch across runs")
        
        self.assertEqual(metrics_1["safety_violations"], metrics_2["safety_violations"], "Safety violations mismatch")
        
        for r1, r2 in zip(results_1, results_2):
            self.assertEqual(r1["status"], r2["status"], f"Status mismatch for {r1['query_id']}")
            self.assertEqual(r1["violation"], r2["violation"], f"Violation mismatch for {r1['query_id']}")

    def test_baseline_safety(self):
        """The baseline config MUST have 0 safety violations. We run this to assert our benchmark data and the codebase aren't broken."""
        engine = GroundedRAGEngine(self.rdata, self.model)
        metrics, results = run_benchmark(engine)
        
        self.assertEqual(metrics["safety_violations"], 0, f"Baseline has safety violations: {metrics}")
        self.assertEqual(metrics["entity_leakage"], 0)
        self.assertEqual(metrics["wrong_standard_rate"], 0)
        self.assertEqual(metrics["wrong_fee_rate"], 0)
        self.assertEqual(metrics["wrong_lab_rate"], 0)
        self.assertEqual(metrics["unsupported_qco_rate"], 0)
        self.assertEqual(metrics["unsupported_latest_rate"], 0)
        self.assertEqual(metrics["source_title_as_fact"], 0)
        self.assertEqual(metrics["unsupported_relationship"], 0)

if __name__ == "__main__":
    unittest.main()
