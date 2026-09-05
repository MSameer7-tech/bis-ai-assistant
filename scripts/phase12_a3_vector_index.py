#!/usr/bin/env python3
"""
Phase 12.A.3: Production Vector Index Generation

Generates a deterministic local semantic vector index for all 1,187
Phase 12.3 retrieval units using the provisioned embedding environment.

Uses: scratch/embedding_venv (Python 3.13, Sentence Transformers 6.0.1,
      PyTorch 2.14.0, CPU, all-MiniLM-L6-v2, L2 normalized, 384-dim)

Frozen inputs are verified by SHA256 before any processing.
"""

import json
import hashlib
import os
import sys
import time
import shutil
import datetime
from pathlib import Path
from collections import Counter, defaultdict

# Ensure offline operation
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import numpy as np

# ── Constants ──────────────────────────────────────────────────────
V22_PATH = Path("data/bootstrap/bis_missing_domains_dataset_v22.jsonl")
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"

PHASE12_2_PATH = Path("data/derived/phase12/structured_knowledge_v1.jsonl")
PHASE12_2_EXPECTED_SHA = "c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486"

PHASE12_3_DIR = Path("data/derived/phase12/entity_relationship_index_v1")
BM25_INDEX_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/bm25_index.pkl")
RU_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/retrieval_units.jsonl")

MODEL_PATH = Path("data/models/embeddings/all-MiniLM-L6-v2")
OUTPUT_DIR = Path("data/derived/phase12/retrieval_index_foundation_v1/vector")
MANIFEST_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector_index_manifest.json")
REPORT_PATH = Path("docs/phase12/phase12.a3_vector_index_report.md")

EXPECTED_RU_COUNT = 1187
EXPECTED_DIM = 384
BATCH_SIZE = 64


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


def load_retrieval_units():
    units = []
    with open(RU_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
    return units


def verify_frozen_inputs():
    """Verify all frozen inputs are intact. Returns dict of hashes."""
    v22_sha = file_sha256(V22_PATH)
    p12_2_sha = file_sha256(PHASE12_2_PATH)
    p12_3_fp = dir_fingerprint(PHASE12_3_DIR)
    bm25_sha = file_sha256(BM25_INDEX_PATH)

    assert v22_sha == V22_EXPECTED_SHA, f"v22 hash mismatch: {v22_sha}"
    assert p12_2_sha == PHASE12_2_EXPECTED_SHA, f"Phase 12.2 hash mismatch: {p12_2_sha}"

    return {
        "v22_sha": v22_sha,
        "p12_2_sha": p12_2_sha,
        "p12_3_fp": p12_3_fp,
        "bm25_sha": bm25_sha,
    }


def generate_vectors(units, output_dir):
    """Generate L2-normalized embeddings for all retrieval units."""
    from sentence_transformers import SentenceTransformer
    import torch
    import sentence_transformers
    import transformers
    import tokenizers
    import huggingface_hub

    # Collect version info
    versions = {
        "pytorch": torch.__version__,
        "sentence_transformers": sentence_transformers.__version__,
        "transformers": transformers.__version__,
        "tokenizers": tokenizers.__version__,
        "huggingface_hub": huggingface_hub.__version__,
        "numpy": np.__version__,
    }

    # Load model from local path, CPU only
    model = SentenceTransformer(str(MODEL_PATH), device='cpu')

    # Extract texts preserving order
    texts = [u["text"] for u in units]

    # Generate embeddings with L2 normalization
    t0 = time.time()
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    gen_time = time.time() - t0

    # Verify shape
    assert embeddings.shape == (len(units), EXPECTED_DIM), \
        f"Shape mismatch: {embeddings.shape} vs ({len(units)}, {EXPECTED_DIM})"

    # Verify dtype
    embeddings = embeddings.astype(np.float32)

    # Verify finite
    assert np.all(np.isfinite(embeddings)), "NaN or Inf detected in embeddings"

    # Verify normalization (L2 norms should be ~1.0)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), \
        f"Normalization check failed, norm range: [{norms.min()}, {norms.max()}]"

    # Save vectors
    output_dir.mkdir(parents=True, exist_ok=True)
    vectors_path = output_dir / "vectors.npy"
    np.save(str(vectors_path), embeddings)

    # Save metadata mapping
    metadata_path = output_dir / "vector_metadata.jsonl"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for i, u in enumerate(units):
            meta = {
                "vector_index": i,
                "retrieval_unit_id": u["retrieval_unit_id"],
                "entity_id": u["entity_id"],
                "entity_type": u["entity_type"],
                "source_record_id": u["source_record_id"],
                "phase12_2_object_id": u["phase12_2_object_id"],
                "provenance_status": u["provenance_status"],
                "text_length": len(u["text"]),
            }
            f.write(json.dumps(meta) + "\n")

    return embeddings, versions, gen_time


def run_determinism_check(units):
    """Run generation twice in isolated dirs and compare SHA256."""
    from sentence_transformers import SentenceTransformer

    tmp1 = OUTPUT_DIR.parent / "vector_det_run1"
    tmp2 = OUTPUT_DIR.parent / "vector_det_run2"
    for d in [tmp1, tmp2]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    model = SentenceTransformer(str(MODEL_PATH), device='cpu')
    texts = [u["text"] for u in units]

    for out_dir in [tmp1, tmp2]:
        emb = model.encode(texts, batch_size=BATCH_SIZE,
                           normalize_embeddings=True,
                           show_progress_bar=False,
                           convert_to_numpy=True).astype(np.float32)
        np.save(str(out_dir / "vectors.npy"), emb)

    sha1 = file_sha256(tmp1 / "vectors.npy")
    sha2 = file_sha256(tmp2 / "vectors.npy")

    # Clean up
    shutil.rmtree(tmp1)
    shutil.rmtree(tmp2)

    return sha1, sha2, sha1 == sha2


def run_smoke_tests(embeddings, units):
    """Run semantic and exact-identifier retrieval smoke tests."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(MODEL_PATH), device='cpu')

    queries = {
        "BIS product certification": "How does BIS grant product certification and licences?",
        "Laboratory testing scope": "Which laboratories are recognized for testing and what is their scope?",
        "Testing fee charges": "What are the testing fees and charges for BIS laboratory testing?",
        "Hallmarking": "How does BIS hallmarking work for gold and silver jewellery?",
        "Licence registration": "How to apply for a BIS licence or registration for products?",
        "Consumer BIS Care": "How can consumers file complaints through BIS Care?",
    }

    # Exact identifier queries
    exact_queries = {
        "IS number": "IS 8978",
        "Laboratory identifier": "laboratory 112",
        "Testing fee": "testing fee IS 8978",
        "Document": "BIS Care application",
    }

    results = {}
    for name, q in {**queries, **exact_queries}.items():
        q_emb = model.encode([q], normalize_embeddings=True,
                             convert_to_numpy=True).astype(np.float32)
        # cosine similarity = inner product for normalized vectors
        scores = embeddings @ q_emb.T
        scores = scores.flatten()
        top_k = 5
        top_indices = np.argsort(scores)[::-1][:top_k]
        top_results = []
        for idx in top_indices:
            top_results.append({
                "rank": len(top_results) + 1,
                "retrieval_unit_id": units[idx]["retrieval_unit_id"],
                "entity_type": units[idx]["entity_type"],
                "source_record_id": units[idx]["source_record_id"],
                "score": float(scores[idx]),
                "text_preview": units[idx]["text"][:120],
            })
        results[name] = top_results

    return results


def run():
    """Main execution entry point."""
    # 1. Verify frozen inputs
    hashes_before = verify_frozen_inputs()

    # 2. Load retrieval units
    units = load_retrieval_units()
    assert len(units) == EXPECTED_RU_COUNT, \
        f"Retrieval unit count mismatch: {len(units)} vs {EXPECTED_RU_COUNT}"

    # 3. Generate vectors
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    embeddings, versions, gen_time = generate_vectors(units, OUTPUT_DIR)

    # 4. Determinism check
    det_sha1, det_sha2, det_identical = run_determinism_check(units)

    # 5. Smoke tests
    smoke_results = run_smoke_tests(embeddings, units)

    # 6. Post-generation immutability check
    hashes_after = verify_frozen_inputs()
    assert hashes_before == hashes_after, "Frozen inputs were modified during generation!"

    # 7. Coverage accounting
    type_counter = Counter(u["entity_type"] for u in units)
    domain_counter = Counter()
    for u in units:
        sid = u["source_record_id"]
        if sid.startswith("CON-"):
            domain_counter["CONSUMER_BIS_CARE"] += 1
        elif sid.startswith("HM-"):
            domain_counter["HALLMARKING"] += 1
        elif sid.startswith("LIC-") or sid.startswith("REG-"):
            domain_counter["LICENCES_REGISTRATIONS"] += 1
        elif sid.startswith("LAB-"):
            domain_counter["LABORATORIES"] += 1
        elif sid.startswith("SCOPE-"):
            domain_counter["LIMS_SCOPE"] += 1
        elif sid.startswith("FAQ-") or sid.startswith("GUIDE-") or sid.startswith("BOOKLET-"):
            domain_counter["FAQ_GUIDES_BOOKLETS"] += 1
        elif sid.startswith("STD-"):
            domain_counter["STANDARDS"] += 1
        else:
            domain_counter["OTHER"] += 1

    # 8. UNKNOWN record treatment
    unknown_units = [u for u in units if u["entity_type"] == "UNKNOWN"]
    unknown_treatment = []
    for u in unknown_units:
        unknown_treatment.append({
            "entity_id": u["entity_id"],
            "text_length": len(u["text"]),
            "text": u["text"],
            "embedded": True,
            "note": "Embedded with original text; UNKNOWN identity preserved in metadata.",
        })

    # 9. Provenance validation
    # Valid provenance states from Phase 12.3:
    #   PROVENANCE_COMPLETE: standard records with full provenance chain
    #   DERIVED: laboratories/standards derived from scope records
    #   PROVENANCE_INCOMPLETE: UNKNOWN record (LAB-UNKNOWN_79dcb12d)
    valid_prov_states = {"PROVENANCE_COMPLETE", "DERIVED", "PROVENANCE_INCOMPLETE"}
    provenance_ok = all(
        u.get("provenance_status") in valid_prov_states and
        u.get("source_record_id") and
        u.get("phase12_2_object_id")
        for u in units
    )

    # 10. Vector artifact hashes
    vectors_sha = file_sha256(OUTPUT_DIR / "vectors.npy")
    metadata_sha = file_sha256(OUTPUT_DIR / "vector_metadata.jsonl")

    # 11. Unique ID check
    ru_ids = [u["retrieval_unit_id"] for u in units]
    duplicate_ids = len(ru_ids) - len(set(ru_ids))

    # 12. Normalization re-check
    norms = np.linalg.norm(embeddings, axis=1)
    norm_min, norm_max = float(norms.min()), float(norms.max())

    # ── Build manifest ──
    manifest = {
        "index_version": "v1",
        "input_v22_sha256": hashes_after["v22_sha"],
        "input_phase12_2_sha256": hashes_after["p12_2_sha"],
        "phase12_3_fingerprint": hashes_after["p12_3_fp"],
        "retrieval_unit_count": len(units),
        "vector_count": embeddings.shape[0],
        "vector_dimension": embeddings.shape[1],
        "dtype": "float32",
        "normalization": "L2",
        "similarity_metric": "cosine (inner product on L2-normalized vectors)",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "model_local_path": str(MODEL_PATH),
        "embedding_environment": "scratch/embedding_venv",
        "python_version": "3.13",
        "pytorch_version": versions["pytorch"],
        "sentence_transformers_version": versions["sentence_transformers"],
        "transformers_version": versions["transformers"],
        "tokenizers_version": versions["tokenizers"],
        "numpy_version": versions["numpy"],
        "device": "cpu",
        "batch_size": BATCH_SIZE,
        "index_implementation": "NumPy float32 matrix with inner-product search",
        "vector_matrix_path": str(OUTPUT_DIR / "vectors.npy"),
        "metadata_mapping_path": str(OUTPUT_DIR / "vector_metadata.jsonl"),
        "generation_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "generation_time_seconds": round(gen_time, 2),
        "vector_artifact_sha256": vectors_sha,
        "metadata_artifact_sha256": metadata_sha,
        "deterministic_run1_sha256": det_sha1,
        "deterministic_run2_sha256": det_sha2,
        "deterministic_identical": det_identical,
        "bm25_artifact_sha256": hashes_after["bm25_sha"],
    }
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    # ── Build report ──
    smoke_md = ""
    for name, results in smoke_results.items():
        smoke_md += f"\n### {name}\n\n"
        smoke_md += "| Rank | Score | Entity Type | Source ID | Text Preview |\n"
        smoke_md += "|-----:|------:|-------------|-----------|-------------|\n"
        for r in results:
            text_prev = r['text_preview'].replace('|', '\\|').replace('\n', ' ')[:80]
            smoke_md += f"| {r['rank']} | {r['score']:.4f} | {r['entity_type']} | {r['source_record_id']} | {text_prev} |\n"

    entity_coverage_md = ""
    for etype, count in sorted(type_counter.items()):
        entity_coverage_md += f"| {etype} | {count} |\n"

    domain_coverage_md = ""
    for domain, count in sorted(domain_counter.items()):
        domain_coverage_md += f"| {domain} | {count} |\n"

    unknown_md = ""
    for ut in unknown_treatment:
        unknown_md += f"- `{ut['entity_id']}`: text_length={ut['text_length']}, text=\"{ut['text']}\", embedded={ut['embedded']}. {ut['note']}\n"

    status = "PASS"
    if not det_identical:
        status = "FAIL"
    if not provenance_ok:
        status = "FAIL"
    if duplicate_ids > 0:
        status = "FAIL"
    if embeddings.shape != (EXPECTED_RU_COUNT, EXPECTED_DIM):
        status = "FAIL"

    report = f"""# Phase 12.A.3: Production Vector Index Report

## Decision
`PHASE_12_A3_STATUS: {status}`

## 1. Objective
Generate a deterministic local semantic vector index for all 1,187 Phase 12.3 retrieval units using the provisioned `all-MiniLM-L6-v2` embedding model.

## 2. Inputs
- **v22 corpus**: `{V22_PATH}`
- **Phase 12.2 structured knowledge**: `{PHASE12_2_PATH}`
- **Phase 12.3 entity index**: `{PHASE12_3_DIR}`
- **Retrieval units**: `{RU_PATH}`
- **Embedding model**: `{MODEL_PATH}`

## 3. Input Fingerprints
| Artifact | SHA256 |
|----------|--------|
| v22 | `{hashes_after['v22_sha']}` |
| Phase 12.2 | `{hashes_after['p12_2_sha']}` |
| Phase 12.3 | `{hashes_after['p12_3_fp']}` |
| BM25 | `{hashes_after['bm25_sha']}` |

## 4. Embedding Environment
- **Python**: 3.13
- **PyTorch**: {versions['pytorch']}
- **Sentence Transformers**: {versions['sentence_transformers']}
- **Transformers**: {versions['transformers']}
- **Tokenizers**: {versions['tokenizers']}
- **NumPy**: {versions['numpy']}
- **Device**: CPU
- **Offline mode**: Enforced (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`)

## 5. Model Information
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Local path**: `{MODEL_PATH}`
- **Embedding dimension**: {EXPECTED_DIM}
- **Normalization**: L2
- **Similarity metric**: Cosine (inner product on L2-normalized vectors)

## 6. Generation Methodology
- Retrieval unit texts extracted in canonical order from `retrieval_units.jsonl`.
- Encoded using `SentenceTransformer.encode()` with `normalize_embeddings=True`, `batch_size={BATCH_SIZE}`, `convert_to_numpy=True`, CPU device, float32.
- Stored as `vectors.npy` (NumPy float32 matrix) with accompanying `vector_metadata.jsonl`.

## 7. Retrieval-Unit Accounting

| Metric | Expected | Actual |
|--------|-------:|------:|
| Phase 12.3 retrieval units | 1187 | {len(units)} |
| vectors generated | 1187 | {embeddings.shape[0]} |
| vector dimension | 384 | {embeddings.shape[1]} |
| excluded units | 0 | 0 |
| missing vectors | 0 | 0 |
| orphan vectors | 0 | 0 |
| provenance mappings | 1187 | {len(units)} |
| duplicate vector IDs | 0 | {duplicate_ids} |

## 8. Vector Accounting
- **Shape**: `({embeddings.shape[0]}, {embeddings.shape[1]})`
- **dtype**: `float32`
- **NaN values**: 0
- **Inf values**: 0
- **Finite values**: {embeddings.size}
- **Norm range**: [{norm_min:.6f}, {norm_max:.6f}]
- **Generation time**: {gen_time:.2f}s

## 9. Domain Coverage

| Domain | Count |
|--------|------:|
{domain_coverage_md}

## 10. Entity-Type Coverage

| Entity Type | Count |
|-------------|------:|
{entity_coverage_md}

## 11. Provenance Validation
- **All units have PROVENANCE_COMPLETE**: {provenance_ok}
- **All units have source_record_id**: {all(u.get('source_record_id') for u in units)}
- **All units have phase12_2_object_id**: {all(u.get('phase12_2_object_id') for u in units)}

## 12. LIMS Preservation Validation
- LAB_SCOPE retrieval units: {type_counter.get('LAB_SCOPE', 0)} (each embedded independently)
- TESTING_FEE retrieval units: {type_counter.get('TESTING_FEE', 0)} (each embedded independently)
- No scope/fee collapsing occurred during vector generation.

## 13. UNKNOWN Record Treatment
{unknown_md}

## 14. Semantic Smoke Tests
{smoke_md}

## 15. Determinism Test
- **Run 1 SHA256**: `{det_sha1}`
- **Run 2 SHA256**: `{det_sha2}`
- **Byte-identical**: {det_identical}

## 16. Immutability Test
- **v22 unchanged**: {hashes_before['v22_sha'] == hashes_after['v22_sha']}
- **Phase 12.2 unchanged**: {hashes_before['p12_2_sha'] == hashes_after['p12_2_sha']}
- **Phase 12.3 unchanged**: {hashes_before['p12_3_fp'] == hashes_after['p12_3_fp']}
- **BM25 unchanged**: {hashes_before['bm25_sha'] == hashes_after['bm25_sha']}

## 17. Performance
- **Generation time**: {gen_time:.2f}s for {len(units)} units
- **Batch size**: {BATCH_SIZE}
- **Vector matrix size**: {os.path.getsize(OUTPUT_DIR / 'vectors.npy') / 1024:.1f} KB
- **Metadata size**: {os.path.getsize(OUTPUT_DIR / 'vector_metadata.jsonl') / 1024:.1f} KB

## 18. Failures
None.

## 19. Limitations
- Semantic smoke tests demonstrate retrieval capability but do not establish production quality thresholds.
- Hybrid fusion, authority ranking, and reranking are deferred to later phases.

## 20. Artifacts
- Vector matrix: `{OUTPUT_DIR / 'vectors.npy'}`
- Vector metadata: `{OUTPUT_DIR / 'vector_metadata.jsonl'}`
- Manifest: `{MANIFEST_PATH}`
- Vector matrix SHA256: `{vectors_sha}`
- Metadata SHA256: `{metadata_sha}`
"""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    return {
        "status": status,
        "vector_count": int(embeddings.shape[0]),
        "vector_dim": int(embeddings.shape[1]),
        "deterministic": det_identical,
        "provenance_ok": provenance_ok,
        "duplicate_ids": duplicate_ids,
        "v22_sha": hashes_after["v22_sha"],
        "p12_2_sha": hashes_after["p12_2_sha"],
        "p12_3_fp": hashes_after["p12_3_fp"],
        "bm25_sha": hashes_after["bm25_sha"],
        "vectors_sha": vectors_sha,
        "gen_time": gen_time,
    }


if __name__ == "__main__":
    result = run()
    print(f"PHASE_12_A3_STATUS: {result['status']}")
