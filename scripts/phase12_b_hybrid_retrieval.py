#!/usr/bin/env python3
"""
Phase 12.B: Hybrid Retrieval Intelligence Engine

Combines structured, BM25, and vector retrieval with:
- Reciprocal Rank Fusion
- Authority ranking
- Freshness/effective-date signals
- Supersession/version handling
- Exact identifier priority

All configuration is externalized to retrieval_config.json.
All frozen artifacts are read-only.
"""

import json
import hashlib
import os
import re
import pickle
import datetime
from pathlib import Path
from collections import defaultdict

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import numpy as np

# ── Paths ──
V22_PATH = Path("data/bootstrap/bis_missing_domains_dataset_v22.jsonl")
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"
PHASE12_2_PATH = Path("data/derived/phase12/structured_knowledge_v1.jsonl")
PHASE12_2_EXPECTED_SHA = "c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486"
VECTORS_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy")
VECTORS_EXPECTED_SHA = "ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad"
PHASE12_3_DIR = Path("data/derived/phase12/entity_relationship_index_v1")
BM25_INDEX_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/bm25_index.pkl")
RU_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/retrieval_units.jsonl")
METADATA_PATH = Path("data/derived/phase12/retrieval_index_foundation_v1/vector/vector_metadata.jsonl")
MODEL_PATH = Path("data/models/embeddings/all-MiniLM-L6-v2")
CONFIG_PATH = Path("data/derived/phase12/hybrid_retrieval_v1/retrieval_config.json")


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


# ── Query Normalization ──
IS_PATTERN = re.compile(r'\b(IS)\s*(\d+)\b', re.IGNORECASE)
LAB_CODE_PATTERN = re.compile(r'\b(?:lab(?:oratory)?)\s*(\d+)\b', re.IGNORECASE)


def normalize_query(query):
    """Deterministic query normalization preserving semantic intent."""
    q = ' '.join(query.strip().split())  # whitespace normalization
    return q


def extract_identifiers(query):
    """Extract structured identifiers from query text."""
    ids = {"is_numbers": [], "lab_codes": [], "source_ids": []}
    for m in IS_PATTERN.finditer(query):
        ids["is_numbers"].append(f"IS {m.group(2)}")
    for m in LAB_CODE_PATTERN.finditer(query):
        ids["lab_codes"].append(m.group(1))
    # Check for direct source_record_id patterns
    for token in query.split():
        if re.match(r'^(CON|HM|LIC|LAB|FAQ|GUIDE|SCOPE|REG|STD|SRC)-', token, re.IGNORECASE):
            ids["source_ids"].append(token)
    return ids


# ── Data Loading ──
class RetrievalData:
    """Loads and caches all retrieval data structures."""

    def __init__(self):
        self.config = json.load(open(CONFIG_PATH, 'r'))

        # Load retrieval units
        self.units = []
        with open(RU_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    self.units.append(json.loads(line))
        self.unit_by_id = {u["retrieval_unit_id"]: u for u in self.units}

        # Load Phase 12.2 structured knowledge (for authority/freshness/supersession)
        self.knowledge = {}
        with open(PHASE12_2_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    self.knowledge[rec["source_record_id"]] = rec

        # Load Phase 12.3 entities by type
        self.entities_by_type = {}
        etype_dir = PHASE12_3_DIR / "entities_by_type"
        for fname in os.listdir(etype_dir):
            if fname.endswith('.jsonl'):
                etype = fname.replace('.jsonl', '').upper()
                entities = []
                with open(etype_dir / fname, 'r') as f:
                    for line in f:
                        if line.strip():
                            entities.append(json.loads(line))
                self.entities_by_type[etype] = entities

        # Load relationships
        self.relationships = []
        rel_path = PHASE12_3_DIR / "relationships.jsonl"
        with open(rel_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.relationships.append(json.loads(line))

        # Load BM25
        with open(BM25_INDEX_PATH, 'rb') as f:
            self.bm25 = pickle.load(f)

        # Load vectors
        self.vectors = np.load(str(VECTORS_PATH))
        self.vector_metadata = []
        with open(METADATA_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    self.vector_metadata.append(json.loads(line))

        # Build structured indexes
        self._build_structured_indexes()

    def _build_structured_indexes(self):
        """Build lookup indexes for structured retrieval."""
        self.is_number_index = defaultdict(list)    # IS number → [retrieval_unit_id]
        self.lab_code_index = defaultdict(list)      # lab code → [retrieval_unit_id]
        self.domain_index = defaultdict(list)        # domain → [retrieval_unit_id]
        self.entity_type_index = defaultdict(list)   # entity_type → [retrieval_unit_id]
        self.source_id_index = {}                    # source_record_id → retrieval_unit_id

        for u in self.units:
            rid = u["retrieval_unit_id"]
            etype = u["entity_type"]
            sid = u["source_record_id"]

            self.entity_type_index[etype].append(rid)
            self.source_id_index[sid] = rid

            # Get knowledge record for richer indexing
            krec = self.knowledge.get(sid, {})
            domain = krec.get("domain", "")
            if domain:
                self.domain_index[domain].append(rid)

            # Extract IS numbers from text
            text = u.get("text", "")
            for m in IS_PATTERN.finditer(text):
                is_num = f"IS {m.group(2)}"
                self.is_number_index[is_num].append(rid)

            # Extract lab codes
            for m in LAB_CODE_PATTERN.finditer(text):
                self.lab_code_index[m.group(1)].append(rid)

            # Direct lab code from entity
            if etype == "LABORATORIES":
                for m in re.finditer(r'\b(\d{2,4})\b', text[:50]):
                    self.lab_code_index[m.group(1)].append(rid)


# ── Retrieval Channels ──

def structured_search(data, query, top_k=20):
    """Deterministic structured retrieval over entity indexes."""
    ids = extract_identifiers(query)
    candidates = {}  # retrieval_unit_id → score

    # IS number exact match
    for is_num in ids["is_numbers"]:
        for rid in data.is_number_index.get(is_num, []):
            candidates[rid] = candidates.get(rid, 0) + 1.0

    # Lab code exact match
    for lc in ids["lab_codes"]:
        for rid in data.lab_code_index.get(lc, []):
            candidates[rid] = candidates.get(rid, 0) + 1.0

    # Source ID exact match
    for sid in ids["source_ids"]:
        rid = data.source_id_index.get(sid)
        if rid:
            candidates[rid] = candidates.get(rid, 0) + 1.0

    # Sort by score desc, then ID for determinism
    ranked = sorted(candidates.items(), key=lambda x: (-x[1], x[0]))[:top_k]
    results = []
    for rank, (rid, score) in enumerate(ranked, 1):
        results.append({
            "retrieval_unit_id": rid,
            "rank": rank,
            "score": float(score),
            "exact_match": True,
        })
    return results


def bm25_search(data, query, top_k=20):
    """BM25 lexical retrieval using the frozen index."""
    tokens = query.lower().split()
    scores = data.bm25.get_scores(tokens)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for rank, idx in enumerate(top_indices, 1):
        idx = int(idx)
        if scores[idx] <= 0:
            break
        u = data.units[idx]
        results.append({
            "retrieval_unit_id": u["retrieval_unit_id"],
            "rank": rank,
            "score": float(scores[idx]),
            "exact_match": False,
        })
    return results


def vector_search(data, query, model, top_k=20):
    """Vector semantic retrieval using the frozen vector index."""
    q_emb = model.encode([query], normalize_embeddings=True,
                         convert_to_numpy=True).astype(np.float32)
    scores = (data.vectors @ q_emb.T).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for rank, idx in enumerate(top_indices, 1):
        idx = int(idx)
        meta = data.vector_metadata[idx]
        results.append({
            "retrieval_unit_id": meta["retrieval_unit_id"],
            "rank": rank,
            "score": float(scores[idx]),
            "exact_match": False,
        })
    return results


# ── Fusion ──

def candidate_union(structured, bm25, vector):
    """Create union of candidates from all channels, deduplicated by retrieval_unit_id."""
    union = {}
    for channel_name, channel_results in [("structured", structured),
                                           ("bm25", bm25),
                                           ("vector", vector)]:
        for r in channel_results:
            rid = r["retrieval_unit_id"]
            if rid not in union:
                union[rid] = {"retrieval_unit_id": rid, "channels": {}, "exact_match": False}
            union[rid]["channels"][channel_name] = {
                "rank": r["rank"],
                "score": r["score"],
            }
            if r.get("exact_match"):
                union[rid]["exact_match"] = True
    return union


def reciprocal_rank_fusion(candidates, config):
    """Apply RRF fusion across channels."""
    k = config["fusion"]["rrf_k"]
    weights = config["fusion"]["channel_weights"]
    boost = config["exact_match_boost"]["boost_factor"] if config["exact_match_boost"]["enabled"] else 1.0

    for rid, cand in candidates.items():
        rrf_score = 0.0
        for channel, info in cand["channels"].items():
            w = weights.get(channel, 1.0)
            rrf_score += w * (1.0 / (k + info["rank"]))
        # Exact match boost
        if cand["exact_match"] and boost > 1.0:
            rrf_score *= boost
        cand["fusion_score"] = rrf_score

    return candidates


# ── Authority / Freshness / Supersession ──

def apply_authority(candidates, data, config):
    """Apply authority ranking adjustments."""
    authority_levels = config["authority"]["levels"]

    for rid, cand in candidates.items():
        unit = data.unit_by_id.get(rid, {})
        sid = unit.get("source_record_id", "")
        krec = data.knowledge.get(sid, {})

        authority = krec.get("authority", "UNKNOWN")
        auth_info = authority_levels.get(authority, authority_levels.get("UNKNOWN", {"rank": 4, "weight": 0.6}))

        cand["authority"] = authority
        cand["authority_rank"] = auth_info["rank"]
        cand["authority_weight"] = auth_info["weight"]
        cand["fusion_score"] *= auth_info["weight"]

        # Accessibility penalty
        accessibility = krec.get("accessibility", "ACCESSIBLE")
        cand["accessibility"] = accessibility
        if accessibility == "INACCESSIBLE_SOURCE":
            penalty = config["inaccessible_evidence"]["penalty_factor"]
            cand["fusion_score"] *= penalty
            cand["inaccessible_penalty_applied"] = True
        else:
            cand["inaccessible_penalty_applied"] = False

    return candidates


def apply_freshness(candidates, data, config):
    """Apply freshness signals from explicit temporal metadata."""
    for rid, cand in candidates.items():
        unit = data.unit_by_id.get(rid, {})
        sid = unit.get("source_record_id", "")
        krec = data.knowledge.get(sid, {})

        effective_date = krec.get("effective_date", "UNKNOWN")
        validity = krec.get("validity", "UNKNOWN")

        cand["effective_date"] = str(effective_date) if effective_date else "UNKNOWN"
        cand["validity"] = str(validity) if validity else "UNKNOWN"

        if effective_date and effective_date != "UNKNOWN":
            cand["freshness_status"] = "HAS_DATE"
        elif validity and validity not in ("UNKNOWN", "-"):
            cand["freshness_status"] = "HAS_VALIDITY"
        else:
            cand["freshness_status"] = "UNKNOWN"

    return candidates


def apply_supersession(candidates, data, config):
    """Apply supersession and version handling."""
    superseded_penalty = config["supersession"]["superseded_penalty"]

    for rid, cand in candidates.items():
        unit = data.unit_by_id.get(rid, {})
        sid = unit.get("source_record_id", "")
        krec = data.knowledge.get(sid, {})

        sup = krec.get("supersession", {})
        is_superseded = sup.get("is_superseded", False) if isinstance(sup, dict) else False
        superseded_by = sup.get("superseded_by", "UNKNOWN") if isinstance(sup, dict) else "UNKNOWN"

        if is_superseded and superseded_by != "UNKNOWN":
            cand["supersession_status"] = "SUPERSEDED"
            cand["superseded_by"] = superseded_by
            cand["fusion_score"] *= superseded_penalty
        elif is_superseded:
            cand["supersession_status"] = "SUPERSESSION_CANDIDATE"
        else:
            cand["supersession_status"] = "UNKNOWN"

    return candidates


# ── Final Ranking ──

def final_ranking(candidates, config):
    """Produce deterministic final ranking."""
    ranked = sorted(
        candidates.values(),
        key=lambda c: (-c["fusion_score"], c.get("authority_rank", 4), c["retrieval_unit_id"])
    )

    top_k = config["final_output"]["top_k"]
    results = []
    for i, cand in enumerate(ranked[:top_k], 1):
        cand["final_rank"] = i
        channels = list(cand["channels"].keys())
        reasons = []
        if cand.get("exact_match"):
            reasons.append("EXACT_IDENTIFIER_MATCH")
        if "structured" in channels:
            reasons.append("STRUCTURED_MATCH")
        if "bm25" in channels:
            reasons.append("BM25_MATCH")
        if "vector" in channels:
            reasons.append("VECTOR_MATCH")
        if cand.get("authority") in ("BIS_PUBLISHED", "BIS"):
            reasons.append("AUTHORITATIVE_SOURCE")
        if cand.get("inaccessible_penalty_applied"):
            reasons.append("INACCESSIBLE_PENALTY")
        if cand.get("supersession_status") == "SUPERSEDED":
            reasons.append("SUPERSEDED_PENALTY")
        cand["ranking_reasons"] = reasons

        results.append(cand)
    return results


# ── Main Pipeline ──

def hybrid_retrieve(data, query, model=None, config=None):
    """Execute full hybrid retrieval pipeline for a single query."""
    if config is None:
        config = data.config

    q = normalize_query(query)

    # Channel retrieval
    s_top_k = config["structured_retrieval"]["top_k"]
    b_top_k = config["bm25_retrieval"]["top_k"]
    v_top_k = config["vector_retrieval"]["top_k"]

    structured = structured_search(data, q, s_top_k) if config["structured_retrieval"]["enabled"] else []
    bm25 = bm25_search(data, q, b_top_k) if config["bm25_retrieval"]["enabled"] else []
    vector = vector_search(data, q, model, v_top_k) if config["vector_retrieval"]["enabled"] and model else []

    # Union + Fusion
    candidates = candidate_union(structured, bm25, vector)
    candidates = reciprocal_rank_fusion(candidates, config)

    # Authority / Freshness / Supersession
    candidates = apply_authority(candidates, data, config)
    candidates = apply_freshness(candidates, data, config)
    candidates = apply_supersession(candidates, data, config)

    # Final ranking
    results = final_ranking(candidates, config)

    return {
        "query": query,
        "normalized_query": q,
        "identifiers": extract_identifiers(q),
        "structured_candidates": len(structured),
        "bm25_candidates": len(bm25),
        "vector_candidates": len(vector),
        "union_candidates": len(candidates),
        "results": results,
    }


# ── Execution ──

def run():
    """Execute Phase 12.B: build and validate hybrid retrieval."""
    # Verify frozen inputs
    assert file_sha256(V22_PATH) == V22_EXPECTED_SHA
    assert file_sha256(PHASE12_2_PATH) == PHASE12_2_EXPECTED_SHA
    assert file_sha256(VECTORS_PATH) == VECTORS_EXPECTED_SHA

    hashes_before = {
        "v22": file_sha256(V22_PATH),
        "p12_2": file_sha256(PHASE12_2_PATH),
        "vectors": file_sha256(VECTORS_PATH),
        "p12_3": dir_fingerprint(PHASE12_3_DIR),
        "bm25": file_sha256(BM25_INDEX_PATH),
    }

    # Load data
    data = RetrievalData()

    # Load embedding model
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(str(MODEL_PATH), device='cpu')

    # Test queries
    test_queries = {
        "A_exact_IS": "IS 616",
        "B_laboratory": "Which laboratories can test cement products?",
        "C_testing_fee": "What is the testing fee for IS 8978?",
        "D_hallmarking": "How does BIS hallmarking work for gold jewellery?",
        "E_licence": "How to apply for a BIS product certification licence?",
        "F_consumer": "How can I file a complaint through BIS Care?",
        "G_faq": "What is the process for getting a BIS certification mark?",
        "H_date": "What are the current testing charges effective in 2026?",
        "I_version": "What is the latest revision of IS 8978?",
        "J_unknown": "LAB-UNKNOWN_79dcb12d",
    }

    all_results = {}
    for name, query in test_queries.items():
        result = hybrid_retrieve(data, query, model)
        all_results[name] = result

    # Determinism check: run query A twice
    r1 = hybrid_retrieve(data, test_queries["A_exact_IS"], model)
    r2 = hybrid_retrieve(data, test_queries["A_exact_IS"], model)
    det_ids_1 = [r["retrieval_unit_id"] for r in r1["results"]]
    det_ids_2 = [r["retrieval_unit_id"] for r in r2["results"]]
    det_scores_1 = [r["fusion_score"] for r in r1["results"]]
    det_scores_2 = [r["fusion_score"] for r in r2["results"]]
    deterministic = (det_ids_1 == det_ids_2 and det_scores_1 == det_scores_2)

    # Verify frozen inputs unchanged
    hashes_after = {
        "v22": file_sha256(V22_PATH),
        "p12_2": file_sha256(PHASE12_2_PATH),
        "vectors": file_sha256(VECTORS_PATH),
        "p12_3": dir_fingerprint(PHASE12_3_DIR),
        "bm25": file_sha256(BM25_INDEX_PATH),
    }
    immutable = hashes_before == hashes_after

    # Build report
    report_lines = [
        "# Phase 12.B: Hybrid Retrieval Intelligence Report\n",
        f"## Decision\n`PHASE_12_B_STATUS: {'PASS' if deterministic and immutable else 'FAIL'}`\n",
        "## 1. Retrieval Architecture\n",
        "```\nUSER QUERY → Query Normalization → Identifier Extraction\n",
        "  ├── Structured Retrieval (exact field match)\n",
        "  ├── BM25 Retrieval (lexical)\n",
        "  └── Vector Retrieval (semantic, all-MiniLM-L6-v2)\n",
        "        ↓\n",
        "  Candidate Union (deduplicated by retrieval_unit_id)\n",
        "        ↓\n",
        "  Reciprocal Rank Fusion (k=60, equal weights)\n",
        "        ↓\n",
        "  Exact Identifier Boost (×2.0)\n",
        "        ↓\n",
        "  Authority Adjustment (BIS_PUBLISHED=1.0, BIS=0.95, USER=0.8, UNKNOWN=0.6)\n",
        "        ↓\n",
        "  Inaccessible Evidence Penalty (×0.5)\n",
        "        ↓\n",
        "  Freshness Signals (date-aware, no inference)\n",
        "        ↓\n",
        "  Supersession Handling (explicit evidence only)\n",
        "        ↓\n",
        "  Final Deterministic Sort (score desc → authority asc → ID asc)\n",
        "```\n",
        "## 2. Fusion Formula\n",
        "Reciprocal Rank Fusion:\n",
        "```\nRRF_score(d) = Σ w_channel × 1/(k + rank_channel(d))\n",
        "             × exact_match_boost (if applicable)\n",
        "             × authority_weight\n",
        "             × inaccessible_penalty (if applicable)\n",
        "             × superseded_penalty (if applicable)\n",
        "```\n",
        f"- k = {data.config['fusion']['rrf_k']}\n",
        f"- Channel weights: structured={data.config['fusion']['channel_weights']['structured']}, "
        f"bm25={data.config['fusion']['channel_weights']['bm25']}, "
        f"vector={data.config['fusion']['channel_weights']['vector']}\n",
        f"- Exact match boost: {data.config['exact_match_boost']['boost_factor']}\n\n",
    ]

    # Test query results
    report_lines.append("## 3. Test Query Results\n")
    for name, result in all_results.items():
        report_lines.append(f"### {name}: `{result['query']}`\n")
        report_lines.append(f"- Structured candidates: {result['structured_candidates']}\n")
        report_lines.append(f"- BM25 candidates: {result['bm25_candidates']}\n")
        report_lines.append(f"- Vector candidates: {result['vector_candidates']}\n")
        report_lines.append(f"- Union candidates: {result['union_candidates']}\n")
        report_lines.append(f"- Identifiers: {json.dumps(result['identifiers'])}\n\n")
        report_lines.append("| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |\n")
        report_lines.append("|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|\n")
        for r in result["results"][:5]:
            u = data.unit_by_id.get(r["retrieval_unit_id"], {})
            channels = ",".join(r["channels"].keys())
            reasons = ",".join(r.get("ranking_reasons", []))
            report_lines.append(
                f"| {r['final_rank']} | {r['fusion_score']:.4f} | {u.get('entity_type','')} | "
                f"{u.get('source_record_id','')} | {r.get('authority','')} | "
                f"{r.get('supersession_status','')} | {channels} | {reasons} |\n"
            )
        report_lines.append("\n")

    # Determinism
    report_lines.append("## 4. Determinism\n")
    report_lines.append(f"- **Identical results on repeated query**: {deterministic}\n\n")

    # Immutability
    report_lines.append("## 5. Immutability\n")
    report_lines.append(f"- v22 unchanged: {hashes_before['v22'] == hashes_after['v22']}\n")
    report_lines.append(f"- Phase 12.2 unchanged: {hashes_before['p12_2'] == hashes_after['p12_2']}\n")
    report_lines.append(f"- Phase 12.3 unchanged: {hashes_before['p12_3'] == hashes_after['p12_3']}\n")
    report_lines.append(f"- BM25 unchanged: {hashes_before['bm25'] == hashes_after['bm25']}\n")
    report_lines.append(f"- Vectors unchanged: {hashes_before['vectors'] == hashes_after['vectors']}\n\n")

    # Hashes
    report_lines.append("## 6. Frozen Artifact Hashes\n")
    report_lines.append(f"- v22: `{hashes_after['v22']}`\n")
    report_lines.append(f"- Phase 12.2: `{hashes_after['p12_2']}`\n")
    report_lines.append(f"- Vectors: `{hashes_after['vectors']}`\n")
    report_lines.append(f"- BM25: `{hashes_after['bm25']}`\n\n")

    report_lines.append("## 7. Limitations\n")
    report_lines.append("- Channel weights and RRF constant are baseline defaults, not optimized.\n")
    report_lines.append("- Freshness signals rely on explicit metadata; most records have UNKNOWN dates.\n")
    report_lines.append("- Supersession is UNKNOWN for all records (no explicit supersession evidence in v22).\n")
    report_lines.append("- Authority weights are reasonable defaults, not empirically calibrated.\n")
    report_lines.append("- Production quality thresholds will be established in Phase 12.D.\n")

    report_path = Path("docs/phase12/phase12.b_hybrid_retrieval_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.writelines(report_lines)

    status = "PASS" if deterministic and immutable else "FAIL"
    return {
        "status": status,
        "deterministic": deterministic,
        "immutable": immutable,
        "hashes": hashes_after,
        "test_queries": {k: len(v["results"]) for k, v in all_results.items()},
    }


if __name__ == "__main__":
    result = run()
    print(f"PHASE_12_B_STATUS: {result['status']}")
