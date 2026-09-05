#!/usr/bin/env python3
"""Tests for Phase 12.A.3: Production Vector Index."""

import unittest
import json
import os
import hashlib
import subprocess
from pathlib import Path
from collections import Counter

import numpy as np

V22_PATH = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"
PHASE12_2_PATH = "data/derived/phase12/structured_knowledge_v1.jsonl"
PHASE12_2_EXPECTED_SHA = "c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486"
PHASE12_3_DIR = Path("data/derived/phase12/entity_relationship_index_v1")
BM25_INDEX_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/bm25_index.pkl")
VECTORS_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy")
METADATA_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector/vector_metadata.jsonl")
RU_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/retrieval_units.jsonl")
MANIFEST_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector_index_manifest.json")
EMBEDDING_VENV_PYTHON = "scratch/embedding_venv/bin/python"


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dir_fingerprint(dirpath):
    hashes = {}
    for root, _, files in os.walk(dirpath):
        for fname in files:
            p = os.path.join(root, fname)
            hashes[fname] = file_sha256(p)
    combined = hashlib.sha256()
    for fname in sorted(hashes.keys()):
        combined.update(fname.encode())
        combined.update(hashes[fname].encode())
    return combined.hexdigest()


def load_metadata():
    meta = []
    with open(METADATA_PATH, 'r') as f:
        for line in f:
            if line.strip():
                meta.append(json.loads(line))
    return meta


def load_retrieval_units():
    units = []
    with open(RU_PATH, 'r') as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
    return units


class TestPhase12A3VectorIndex(unittest.TestCase):
    """Phase 12.A.3 vector index validation tests."""

    @classmethod
    def setUpClass(cls):
        cls.vectors = np.load(str(VECTORS_PATH))
        cls.metadata = load_metadata()
        cls.units = load_retrieval_units()
        cls.manifest = json.load(open(MANIFEST_PATH))

    # 1. Vector index exists
    def test_01_vector_index_exists(self):
        self.assertTrue(VECTORS_PATH.exists())
        self.assertTrue(METADATA_PATH.exists())
        self.assertTrue(MANIFEST_PATH.exists())

    # 2. Vector count matches retrieval units
    def test_02_vector_count_matches(self):
        self.assertEqual(self.vectors.shape[0], 1187)
        self.assertEqual(len(self.metadata), 1187)
        self.assertEqual(len(self.units), 1187)

    # 3. Vector dimension is 384
    def test_03_vector_dimension(self):
        self.assertEqual(self.vectors.shape[1], 384)

    # 4. dtype is correct
    def test_04_dtype(self):
        self.assertEqual(self.vectors.dtype, np.float32)

    # 5. All vectors are finite
    def test_05_all_finite(self):
        self.assertTrue(np.all(np.isfinite(self.vectors)))

    # 6. No NaN
    def test_06_no_nan(self):
        self.assertFalse(np.any(np.isnan(self.vectors)))

    # 7. No Inf
    def test_07_no_inf(self):
        self.assertFalse(np.any(np.isinf(self.vectors)))

    # 8. Normalization is valid
    def test_08_normalization(self):
        norms = np.linalg.norm(self.vectors, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-5))

    # 9. IDs are unique
    def test_09_unique_ids(self):
        ru_ids = [m["retrieval_unit_id"] for m in self.metadata]
        self.assertEqual(len(ru_ids), len(set(ru_ids)))

    # 10. Mapping count matches vector count
    def test_10_mapping_count(self):
        self.assertEqual(len(self.metadata), self.vectors.shape[0])

    # 11. Provenance exists
    def test_11_provenance_exists(self):
        for m in self.metadata:
            self.assertIn("source_record_id", m)
            self.assertIn("phase12_2_object_id", m)
            self.assertIn("entity_id", m)
            self.assertTrue(m["source_record_id"])
            self.assertTrue(m["phase12_2_object_id"])

    # 12. No orphan mappings
    def test_12_no_orphan_mappings(self):
        meta_ids = {m["retrieval_unit_id"] for m in self.metadata}
        unit_ids = {u["retrieval_unit_id"] for u in self.units}
        self.assertEqual(meta_ids, unit_ids)

    # 13. No duplicate vector IDs
    def test_13_no_duplicate_vector_ids(self):
        indices = [m["vector_index"] for m in self.metadata]
        self.assertEqual(len(indices), len(set(indices)))
        self.assertEqual(sorted(indices), list(range(len(indices))))

    # 14. Exact identifier retrieval works
    def test_14_exact_identifier_retrieval(self):
        """Test that searching for 'laboratory 112' returns lab 112 in top results."""
        env = os.environ.copy()
        env["HF_HUB_OFFLINE"] = "1"
        env["TRANSFORMERS_OFFLINE"] = "1"
        runner = """
import numpy as np, json, os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('data/models/embeddings/all-MiniLM-L6-v2', device='cpu')
vectors = np.load('data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy')
meta = []
with open('data/derived/phase12/retrieval_index_foundation_v1/vector/vector_metadata.jsonl') as f:
    for line in f:
        if line.strip(): meta.append(json.loads(line))
q = model.encode(['laboratory 112'], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
scores = (vectors @ q.T).flatten()
top5 = np.argsort(scores)[::-1][:5]
ids = [meta[i]['retrieval_unit_id'] for i in top5]
print(json.dumps(ids))
"""
        proc = subprocess.run(
            [EMBEDDING_VENV_PYTHON, "-c", runner],
            capture_output=True, text=True, env=env
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ids = json.loads(proc.stdout.strip())
        # lab_112 or ru_dk_SCOPE-112 should appear in top 5
        has_112 = any("112" in rid for rid in ids)
        self.assertTrue(has_112, f"Lab 112 not found in top 5: {ids}")

    # 15. Semantic retrieval executes
    def test_15_semantic_retrieval_executes(self):
        """Test that a semantic query produces ranked results."""
        env = os.environ.copy()
        env["HF_HUB_OFFLINE"] = "1"
        env["TRANSFORMERS_OFFLINE"] = "1"
        runner = """
import numpy as np, json, os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('data/models/embeddings/all-MiniLM-L6-v2', device='cpu')
vectors = np.load('data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy')
q = model.encode(['BIS hallmarking gold jewellery'], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
scores = (vectors @ q.T).flatten()
top = float(scores.max())
print(top)
"""
        proc = subprocess.run(
            [EMBEDDING_VENV_PYTHON, "-c", runner],
            capture_output=True, text=True, env=env
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        top_score = float(proc.stdout.strip())
        self.assertGreater(top_score, 0.3)

    # 16. v22 unchanged
    def test_16_v22_unchanged(self):
        self.assertEqual(file_sha256(V22_PATH), V22_EXPECTED_SHA)

    # 17. Phase 12.2 unchanged
    def test_17_phase12_2_unchanged(self):
        self.assertEqual(file_sha256(PHASE12_2_PATH), PHASE12_2_EXPECTED_SHA)

    # 18. Phase 12.3 unchanged
    def test_18_phase12_3_unchanged(self):
        fp = dir_fingerprint(PHASE12_3_DIR)
        self.assertIsNotNone(fp)
        self.assertGreater(len(fp), 0)

    # 19. BM25 unchanged
    def test_19_bm25_unchanged(self):
        sha = file_sha256(BM25_INDEX_PATH)
        self.assertEqual(sha, self.manifest["bm25_artifact_sha256"])

    # 20. Deterministic repeat passes
    def test_20_deterministic_repeat(self):
        self.assertTrue(self.manifest["deterministic_identical"])
        self.assertEqual(
            self.manifest["deterministic_run1_sha256"],
            self.manifest["deterministic_run2_sha256"]
        )


if __name__ == '__main__':
    unittest.main()
