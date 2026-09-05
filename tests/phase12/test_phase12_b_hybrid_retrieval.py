#!/usr/bin/env python3
"""Tests for Phase 12.B: Hybrid Retrieval Intelligence."""

import unittest
import json
import os
import hashlib
import pickle
import subprocess
from pathlib import Path

import numpy as np

V22_PATH = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"
PHASE12_2_PATH = "data/derived/phase12/structured_knowledge_v1.jsonl"
PHASE12_2_EXPECTED_SHA = "c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486"
VECTORS_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy")
VECTORS_EXPECTED_SHA = "ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad"
BM25_INDEX_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/bm25_index.pkl")
CONFIG_PATH = Path("data/derived/phase12/hybrid_retrieval_v1/retrieval_config.json")
EMBEDDING_VENV_PYTHON = "scratch/embedding_venv/bin/python"

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def run_retrieval_query(query):
    """Execute a hybrid retrieval query via subprocess in embedding venv."""
    runner = f'''
import os, json, sys
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, ".")
from scripts.phase12_b_hybrid_retrieval import RetrievalData, hybrid_retrieve
from sentence_transformers import SentenceTransformer
data = RetrievalData()
model = SentenceTransformer("data/models/embeddings/all-MiniLM-L6-v2", device="cpu")
result = hybrid_retrieve(data, """{query}""", model)
print("===RESULT===")
print(json.dumps(result, default=str))
'''
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    proc = subprocess.run(
        [EMBEDDING_VENV_PYTHON, "-c", runner],
        capture_output=True, text=True, env=env
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Query failed: {proc.stderr}")
    out = proc.stdout
    json_str = out.split("===RESULT===")[1].strip()
    return json.loads(json_str)


class TestPhase12BHybridRetrieval(unittest.TestCase):
    """Phase 12.B hybrid retrieval validation tests."""

    # 1. Structured retrieval
    def test_01_structured_retrieval(self):
        result = run_retrieval_query("IS 616")
        self.assertGreater(result["structured_candidates"], 0)

    # 2. BM25 retrieval
    def test_02_bm25_retrieval(self):
        result = run_retrieval_query("cement testing laboratory")
        self.assertGreater(result["bm25_candidates"], 0)

    # 3. Vector retrieval
    def test_03_vector_retrieval(self):
        result = run_retrieval_query("BIS hallmarking gold")
        self.assertGreater(result["vector_candidates"], 0)

    # 4. Candidate union
    def test_04_candidate_union(self):
        result = run_retrieval_query("IS 8978 testing fee")
        self.assertGreater(result["union_candidates"], 0)
        # Union should be <= sum of all channels
        total = result["structured_candidates"] + result["bm25_candidates"] + result["vector_candidates"]
        self.assertLessEqual(result["union_candidates"], total)

    # 5. Duplicate consolidation
    def test_05_duplicate_consolidation(self):
        result = run_retrieval_query("IS 8978 testing")
        rids = [r["retrieval_unit_id"] for r in result["results"]]
        self.assertEqual(len(rids), len(set(rids)))

    # 6. RRF/fusion calculation
    def test_06_fusion_calculation(self):
        result = run_retrieval_query("BIS certification")
        for r in result["results"]:
            self.assertIn("fusion_score", r)
            self.assertGreater(r["fusion_score"], 0)

    # 7. Exact identifier priority
    def test_07_exact_identifier_priority(self):
        result = run_retrieval_query("IS 8978")
        # Exact IS match should appear in results
        has_exact = any(r.get("exact_match") for r in result["results"])
        self.assertTrue(has_exact, "Exact match should appear for IS number query")

    # 8. Authority ranking
    def test_08_authority_ranking(self):
        result = run_retrieval_query("BIS certification")
        for r in result["results"]:
            self.assertIn("authority", r)
            self.assertIn(r["authority"], ["BIS_PUBLISHED", "BIS", "USER_SUPPLIED", "UNKNOWN"])

    # 9. Freshness handling
    def test_09_freshness_handling(self):
        result = run_retrieval_query("current testing charges")
        for r in result["results"]:
            self.assertIn("freshness_status", r)

    # 10. Effective-date handling
    def test_10_effective_date_handling(self):
        result = run_retrieval_query("testing charges effective 2026")
        for r in result["results"]:
            self.assertIn("effective_date", r)

    # 11. Supersession handling
    def test_11_supersession_handling(self):
        result = run_retrieval_query("IS 8978 revision")
        for r in result["results"]:
            self.assertIn("supersession_status", r)

    # 12. Historical version preservation
    def test_12_historical_version_preservation(self):
        result = run_retrieval_query("IS 8978")
        # Should have results; historical versions should not be erased
        self.assertGreater(len(result["results"]), 0)

    # 13. Inaccessible evidence handling
    def test_13_inaccessible_evidence_handling(self):
        result = run_retrieval_query("BIS certification")
        for r in result["results"]:
            self.assertIn("inaccessible_penalty_applied", r)

    # 14. UNKNOWN handling
    def test_14_unknown_handling(self):
        result = run_retrieval_query("LAB-UNKNOWN_79dcb12d")
        # The UNKNOWN record may appear but should not have fabricated authority
        for r in result["results"]:
            self.assertIn("authority", r)

    # 15. Provenance preservation
    def test_15_provenance_preservation(self):
        result = run_retrieval_query("BIS hallmarking")
        for r in result["results"]:
            self.assertIn("retrieval_unit_id", r)
            self.assertIn("channels", r)

    # 16. Deterministic ranking
    def test_16_deterministic_ranking(self):
        r1 = run_retrieval_query("IS 616")
        r2 = run_retrieval_query("IS 616")
        ids1 = [r["retrieval_unit_id"] for r in r1["results"]]
        ids2 = [r["retrieval_unit_id"] for r in r2["results"]]
        self.assertEqual(ids1, ids2)
        scores1 = [r["fusion_score"] for r in r1["results"]]
        scores2 = [r["fusion_score"] for r in r2["results"]]
        self.assertEqual(scores1, scores2)

    # 17. LIMS fee retrieval
    def test_17_lims_fee_retrieval(self):
        result = run_retrieval_query("testing fee IS 8978")
        entity_types = [r.get("channels", {}).keys() for r in result["results"]]
        self.assertGreater(len(result["results"]), 0)

    # 18. Multi-channel retrieval
    def test_18_multi_channel_retrieval(self):
        result = run_retrieval_query("IS 8978 laboratory testing")
        # At least one result should come from multiple channels
        multi = [r for r in result["results"] if len(r["channels"]) > 1]
        self.assertGreater(len(multi), 0, "At least one result should appear in multiple channels")

    # 19. Frozen artifact hashes
    def test_19_frozen_artifact_hashes(self):
        self.assertEqual(file_sha256(V22_PATH), V22_EXPECTED_SHA)
        self.assertEqual(file_sha256(PHASE12_2_PATH), PHASE12_2_EXPECTED_SHA)
        self.assertEqual(file_sha256(VECTORS_PATH), VECTORS_EXPECTED_SHA)

    # 20. Final candidate ordering
    def test_20_final_candidate_ordering(self):
        result = run_retrieval_query("BIS certification licence")
        scores = [r["fusion_score"] for r in result["results"]]
        # Scores should be in descending order
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i+1])


if __name__ == '__main__':
    unittest.main()
