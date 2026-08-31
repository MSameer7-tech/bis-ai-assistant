"""
Retrieval Benchmark Evaluation Runner for BIS Knowledge System (Step 15).
Measures Recall@5, Recall@10, Precision@1, and MRR (Mean Reciprocal Rank).
"""

import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.vectorstore.hybrid_search import HybridSearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")

EVAL_PATH = ROOT_DIR / "data" / "evaluation" / "retrieval_queries.json"


def evaluate():
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Evaluation benchmark file missing: {EVAL_PATH}")

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    engine = HybridSearchEngine()

    total_queries = len(queries)
    hits_at_1 = 0
    hits_at_5 = 0
    hits_at_10 = 0
    reciprocal_ranks = []

    print("\n" + "=" * 90)
    print(f"📊 BIS RETRIEVAL BENCHMARK EVALUATION ({total_queries} Test Queries)")
    print("=" * 90)

    for q in queries:
        qid = q["query_id"]
        question = q["question"]
        req_clause = q["required_clause"]
        req_std = q.get("required_standard")

        results = engine.search(query=question, top_k=10)

        found_rank = None
        for rank, res in enumerate(results, 1):
            clause_match = req_clause in str(res.get("clause_number", "")) or req_clause in str(res.get("chunk_id", ""))
            if clause_match:
                found_rank = rank
                break

        if found_rank is not None:
            reciprocal_ranks.append(1.0 / found_rank)
            if found_rank == 1:
                hits_at_1 += 1
            if found_rank <= 5:
                hits_at_5 += 1
            if found_rank <= 10:
                hits_at_10 += 1
            print(f"  ✅ [{qid}] Rank #{found_rank}: \"{question[:50]}...\"")
        else:
            reciprocal_ranks.append(0.0)
            print(f"  ❌ [{qid}] Miss: \"{question[:50]}...\" (Target Clause: {req_clause})")

    p_at_1 = hits_at_1 / total_queries if total_queries else 0.0
    r_at_5 = hits_at_5 / total_queries if total_queries else 0.0
    r_at_10 = hits_at_10 / total_queries if total_queries else 0.0
    mrr = sum(reciprocal_ranks) / total_queries if total_queries else 0.0

    print("-" * 90)
    print(f"📈 RETRIEVAL METRICS SUMMARY:")
    print(f"   • Precision@1:  {p_at_1:.2%} ({hits_at_1}/{total_queries})")
    print(f"   • Recall@5:     {r_at_5:.2%} ({hits_at_5}/{total_queries})")
    print(f"   • Recall@10:    {r_at_10:.2%} ({hits_at_10}/{total_queries})")
    print(f"   • MRR:          {mrr:.4f}")
    print("=" * 90 + "\n")

    return {
        "precision_at_1": p_at_1,
        "recall_at_5": r_at_5,
        "recall_at_10": r_at_10,
        "mrr": mrr,
    }


if __name__ == "__main__":
    evaluate()
