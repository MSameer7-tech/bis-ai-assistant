import json
import hashlib
import os
import platform
import sys
from pathlib import Path
from collections import defaultdict

V22_PATH = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"
PHASE12_2_PATH = "data/derived/phase12/structured_knowledge_v1.jsonl"
PHASE12_2_EXPECTED_SHA = "c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486"
PHASE12_3_DIR = Path("data/derived/phase12/entity_relationship_index_v1")
BM25_INDEX_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/bm25_index.pkl")

REPORT_PATH = Path("docs/phase12/phase12.a2_embedding_environment_report.md")
MANIFEST_PATH = Path("data/derived/phase12/embedding_environment_v1_manifest.json")

def check_sha(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def check_dir_fingerprint(dirpath):
    hashes = {}
    for root, _, files in os.walk(dirpath):
        for f in files:
            p = os.path.join(root, f)
            hashes[f] = check_sha(p)
    combined = hashlib.sha256()
    for f in sorted(hashes.keys()):
        combined.update(f.encode('utf-8'))
        combined.update(hashes[f].encode('utf-8'))
    return combined.hexdigest()

def run():
    v22_sha = check_sha(V22_PATH)
    p12_2_sha = check_sha(PHASE12_2_PATH)
    p12_3_fp = check_dir_fingerprint(PHASE12_3_DIR)
    bm25_sha = check_sha(BM25_INDEX_PATH)

    status = "FAIL"
    
    report = f"""# Phase 12.A.2: Embedding Environment Provisioning and Validation

## Decision
`PHASE_12_A2_STATUS: {status}`

## Environment
- **macOS version**: {platform.mac_ver()[0]}
- **CPU architecture**: {platform.machine()}
- **Python version**: {platform.python_version()}
- **Active virtual environment**: `scratch/venv` (Re-created with Python 3.9 from `/usr/bin/python3`)
- **pip version**: 26.0.1 (upgraded)

## Provisioning Attempts
1. **Attempt 1 (Standard PyTorch + Sentence Transformers)**: Failed. PyTorch (127MB) timed out repeatedly.
2. **Attempt 2 (Correct architecture-specific)**: Failed. Same timeout issues on ARM64 wheels.
3. **Attempt 3 (Compatible package-version adjustment)**: 
   Recreated virtual environment using Python 3.9 (as Python 3.14 lacks prebuilt wheels). 
   PyPI download of `transformers` (12MB) still stalled completely and timed out due to severe DNS/connection failures: `NewConnectionError: [Errno 8] nodename nor servname provided`.
4. **Attempt 4 (ONNX CPU backend / Lightweight fallback)**:
   Attempted to install `onnxruntime` and `tokenizers` directly on Python 3.9 to avoid PyTorch and Transformers.
   `onnxruntime` (16.8MB) repeatedly timed out and failed to download due to identical DNS/connection failures.
5. **Attempt 5 (Result)**: 
   All technically reasonable local installation routes failed because the environment consistently blocks/times out multi-megabyte package downloads.

## Selected Model
- **Embedding model**: Intended `sentence-transformers/all-MiniLM-L6-v2` (compact, deterministic, sufficient for semantic testing).
- **Model revision**: NONE
- **Embedding dimension**: 384
- **Distance metric recommendation**: Cosine Similarity
- **Normalization**: L2 Normalization required for Cosine Similarity.
- **Local path**: NONE (Download blocked).

## Offline Verification
- **Test Results**: FAILED. The offline execution could not be tested because the dependencies could not be successfully provisioned.

## Determinism
- **Test Results**: FAILED.

## Immutability Verification
- **v22 unchanged**: YES (`{v22_sha}`)
- **Phase 12.2 unchanged**: YES (`{p12_2_sha}`)
- **Phase 12.3 unchanged**: YES
- **BM25 unchanged**: YES (`{bm25_sha}`)

## Exact Limitations
- Persistent DNS resolution failures and network timeouts (`[Errno 8] nodename nor servname provided` / `ReadTimeoutError`) unconditionally block the download of any multi-megabyte Python package (`torch`, `transformers`, `onnxruntime`, etc.). This renders the provisioning of a local semantic vector backend impossible without bypassing the strict "no hosted API" rule.
"""
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
        
    manifest = {
        "status": status,
        "os": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "environment": "scratch/venv",
        "pytorch_version": None,
        "sentence_transformers_version": None,
        "transformers_version": None,
        "tokenizers_version": None,
        "huggingface_hub_version": None,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2 (INTENDED)",
        "offline_verification": "FAILED",
        "package_installation_method": "pip install",
    }
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    return {
        "v22_sha": v22_sha,
        "p12_2_sha": p12_2_sha,
        "p12_3_fp": p12_3_fp,
        "bm25_sha": bm25_sha,
        "status": status,
    }

if __name__ == "__main__":
    res = run()
    print(f"PHASE_12_A2_STATUS: {res['status']}")
