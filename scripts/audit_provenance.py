#!/usr/bin/env python3
"""
Provenance & Grounding Integrity Auditor (Phase 6.5).
Audits end-to-end traceability of the BIS Intelligence System:
1. Knowledge Graph Edge Traceability (evidence, source_document, clause/table, verification status)
2. Product Registry Traceability (standard, edition, evidence source)
3. Document Chunk Traceability (document_id, page boundaries, clause numbers)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
CHUNKS_DIR = DATA_DIR / "chunks"


def audit_system_provenance() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("🔍 BIS SYSTEM PROVENANCE & GROUNDING AUDIT (PHASE 6.5)")
    print("=" * 80)

    # 1. Audit Knowledge Graph Provenance
    rel_file = REGISTRY_DIR / "relationships.jsonl"
    total_edges = 0
    edges_with_evidence = 0
    edges_verified = 0

    if rel_file.exists():
        with open(rel_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    edge = json.loads(line)
                    total_edges += 1
                    ev = edge.get("evidence", {})
                    if ev.get("source_type") and ev.get("source_document"):
                        edges_with_evidence += 1
                    if edge.get("verification_status") == "verified":
                        edges_verified += 1

    kg_evidence_pct = (edges_with_evidence / total_edges * 100) if total_edges else 0
    kg_verified_pct = (edges_verified / total_edges * 100) if total_edges else 0

    print("1. KNOWLEDGE GRAPH PROVENANCE")
    print(f"  • Total Relational Edges:              {total_edges:>6d}")
    print(f"  • Edges with Full Evidence Block:      {edges_with_evidence:>6d} ({kg_evidence_pct:.1f}%)")
    print(f"  • Verified Edges:                      {edges_verified:>6d} ({kg_verified_pct:.1f}%)")

    # 2. Audit Product Registry Provenance
    prod_file = REGISTRY_DIR / "products.jsonl"
    total_products = 0
    products_with_evidence = 0

    if prod_file.exists():
        with open(prod_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    p = json.loads(line)
                    total_products += 1
                    if p.get("evidence_source"):
                        products_with_evidence += 1

    prod_evidence_pct = (products_with_evidence / total_products * 100) if total_products else 0

    print("-" * 80)
    print("2. PRODUCT ONTOLOGY PROVENANCE")
    print(f"  • Total Product Terms:                 {total_products:>6d}")
    print(f"  • Terms with Authoritative Evidence:   {products_with_evidence:>6d} ({prod_evidence_pct:.1f}%)")

    # 3. Audit Chunk Grounding & Clause Provenance
    chunk_files = list(CHUNKS_DIR.glob("*.json")) if CHUNKS_DIR.exists() else []
    total_chunks = 0
    chunks_with_clause = 0
    chunks_with_pages = 0

    for cf in chunk_files:
        try:
            with open(cf, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                for ch in chunks:
                    total_chunks += 1
                    if ch.get("clause_number") or ch.get("clause"):
                        chunks_with_clause += 1
                    if ch.get("page_start") or ch.get("page"):
                        chunks_with_pages += 1
        except Exception:
            pass

    chunk_clause_pct = (chunks_with_clause / total_chunks * 100) if total_chunks else 0
    chunk_page_pct = (chunks_with_pages / total_chunks * 100) if total_chunks else 0

    print("-" * 80)
    print("3. VECTOR RAG CHUNK PROVENANCE")
    print(f"  • Total Indexed Chunks:                {total_chunks:>6d}")
    print(f"  • Chunks with Clause Reference:        {chunks_with_clause:>6d} ({chunk_clause_pct:.1f}%)")
    print(f"  • Chunks with Page Provenance:         {chunks_with_pages:>6d} ({chunk_page_pct:.1f}%)")
    print("=" * 80 + "\n")

    return {
        "knowledge_graph": {"total": total_edges, "evidence_pct": kg_evidence_pct},
        "product_ontology": {"total": total_products, "evidence_pct": prod_evidence_pct},
        "vector_chunks": {"total": total_chunks, "clause_pct": chunk_clause_pct, "page_pct": chunk_page_pct}
    }


if __name__ == "__main__":
    audit_system_provenance()
