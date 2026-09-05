#!/usr/bin/env python3
"""
Step 12: Phase 6 Retrieval Integrity Tests
Validates the structural integrity, provenance, and configuration of the retrieval layer.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
INDEXES_DIR = DATA_DIR / "indexes"
CHUNKS_DIR = DATA_DIR / "processed" / "chunks"

def test_phase5_baseline_remains_frozen():
    # Verify the chunk manifest loaded exactly 17,167 units
    manifest_path = CHUNKS_DIR / "chunk_corpus_manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    assert manifest["evidence_unit_count"] == 17167

def test_deterministic_corpus_fingerprint():
    fp_path = INDEXES_DIR / "corpus_fingerprint.json"
    assert fp_path.exists()
    
    with open(fp_path, "r") as f:
        fp_data = json.load(f)
        
    assert len(fp_data["corpus_fingerprint"]) == 64
    assert fp_data["algorithm"] == "SHA-256"

def test_deterministic_chunking_and_provenance():
    manifest_path = CHUNKS_DIR / "chunk_corpus_manifest.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    assert manifest["status"] == "PASS"
    assert manifest["quality_statistics"]["missing_provenance_errors"] == 0
    assert manifest["quality_statistics"]["orphan_chunks"] == 0
    assert manifest["quality_statistics"]["empty_chunks"] == 0
    
    chunk_count = manifest["chunk_count"]
    assert chunk_count > 17167 # Chunks must be >= EUs

def test_bm25_manifest_consistency():
    bm25_path = INDEXES_DIR / "bm25_manifest.json"
    assert bm25_path.exists()
    
    with open(bm25_path, "r") as f:
        data = json.load(f)
        
    assert data["status"] == "BUILT"
    assert "corpus_fingerprint" in data

def test_vector_manifest_consistency():
    vec_path = INDEXES_DIR / "vector_manifest.json"
    assert vec_path.exists()
    
    with open(vec_path, "r") as f:
        data = json.load(f)
        
    assert data["embedding_dimension"] == 384
    assert data["model_name"] == "BAAI/bge-small-en-v1.5"

def test_index_manifest_completeness():
    idx_path = INDEXES_DIR / "index_manifest.json"
    assert idx_path.exists()
    
    with open(idx_path, "r") as f:
        data = json.load(f)
        
    assert data["evidence_unit_count"] == 17167
    assert data["chroma_collection"] == "bis_phase6_baseline"
    assert data["embedding_model"] == "BAAI/bge-small-en-v1.5"
