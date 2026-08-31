"""
Diagnostic script for inspecting BM25, ChromaDB, and RRF retrieval behavior
across the 4 specific failing queries.
"""
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.vectorstore.hybrid_search import HybridSearchEngine

QUERIES = [
    ("Q1", "Which BIS standard applies to electric ceiling fans?"),
    ("Q2", "Which BIS standard specifies ordinary Portland cement?"),
    ("Q3", "Which BIS standard covers protective helmets for motorcycle riders?"),
    ("Q4", "Which BIS standard covers secondary lithium batteries?"),
]

def run_diagnostics():
    engine = HybridSearchEngine()
    
    for q_id, query in QUERIES:
        print("=" * 100)
        print(f"🔎 {q_id}: '{query}'")
        print("=" * 100)

        # 1. Raw Dense (ChromaDB)
        query_vector = engine.embedding_manager.embed_query(query)
        dense_results = engine.vector_store.query_dense(query_vector, top_k=10)
        print(f"\n--- 1. Raw Dense (ChromaDB) Top 10 ---")
        for rank, r in enumerate(dense_results, 1):
            meta = r.get("metadata", {})
            print(f"  {rank:2d}. Chunk: {r['chunk_id']:<35} | Doc: {meta.get('document_id')} | Std: {meta.get('standard_number')} | Dist/Score: {r.get('score'):.4f}")

        # 2. Raw BM25 (Sparse)
        bm25_results = engine.bm25_index.query_sparse(query, top_k=10)
        print(f"\n--- 2. Raw BM25 Top 10 ---")
        for rank, r in enumerate(bm25_results, 1):
            meta = r.get("metadata", {})
            print(f"  {rank:2d}. Chunk: {r['chunk_id']:<35} | Doc: {r.get('document_id')} | Std: {r.get('standard_number')} | BM25 Score: {r.get('score'):.4f}")

        # 3. Hybrid RRF Search
        hybrid_results = engine.search(query, top_k=5)
        print(f"\n--- 3. Hybrid RRF Top 5 ---")
        for rank, r in enumerate(hybrid_results, 1):
            print(f"  {rank:2d}. Chunk: {r['chunk_id']:<35} | Doc: {r.get('document_id')} | Std: {r.get('standard_number')} | Clause: {r.get('clause_number')} | RRF Score: {r.get('score')}")
            print(f"      Text preview: {r.get('text')[:120]}...")

if __name__ == "__main__":
    run_diagnostics()
