"""
Hybrid Retrieval Engine for BIS Standards (Phase 2E Hardened).
Combines Dense Semantic Embeddings + BM25 Sparse Exact Matching + Temporal Filtering
+ Exact Inverted Index + Canonical Parameter Matching using Reciprocal Rank Fusion (RRF).
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from ai.embeddings.manager import EmbeddingManager
from ai.retrieval.exact_index import ExactInvertedIndex
from ai.retrieval.query_parser import QueryParser, StructuredQuery
from ai.vectorstore.base import BaseVectorStore
from ai.vectorstore.bm25_index import BM25Index
from ai.vectorstore.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """Orchestrates multi-modal retrieval: Dense (Chroma) + Sparse (BM25) + Exact Index + Parameter Matching + Temporal Gate + RRF."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        bm25_index: Optional[BM25Index] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        exact_index: Optional[ExactInvertedIndex] = None,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0,
        exact_weight: float = 1.5,
        param_weight: float = 1.2,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_index = bm25_index or BM25Index()
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.exact_index = exact_index or ExactInvertedIndex()
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.exact_weight = exact_weight
        self.param_weight = param_weight
        self.rrf_k = rrf_k

    def _apply_temporal_filter(
        self, candidate: Dict[str, Any], as_of_date: Optional[str] = None
    ) -> bool:
        """Filters candidate chunks based on effective date window."""
        meta = candidate.get("metadata", {})
        temp_status = meta.get("temporal_status", "current")

        if temp_status == "superseded" and as_of_date is None:
            return False

        today_str = datetime.now().strftime("%Y-%m-%d")
        target_str = as_of_date.split("T")[0] if as_of_date else today_str
        try:
            target = datetime.fromisoformat(target_str)
        except ValueError:
            target = datetime.now()

        v_from_str = meta.get("valid_from")
        v_until_str = meta.get("valid_until")

        try:
            v_from = datetime.fromisoformat(v_from_str.split("T")[0]) if v_from_str else datetime.min
        except ValueError:
            v_from = datetime.min

        try:
            v_until = datetime.fromisoformat(v_until_str.split("T")[0]) if v_until_str else datetime.max
        except ValueError:
            v_until = datetime.max

        return v_from <= target <= v_until

    def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 25,
        as_of_date: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes parameter-aware hybrid search across dense, sparse, and exact inverted indices,
        fuses with RRF, and returns provenance-rich results.
        """
        # 1. Parse Structured Query
        sq: StructuredQuery = QueryParser.parse(query, as_of_date=as_of_date)

        # Immediate abstention for out-of-scope queries
        if sq.intent == "OUT_OF_SCOPE":
            logger.info("Query '%s' classified as OUT_OF_SCOPE -> returning empty candidates", query)
            return []

        # 2. Dense Semantic Retrieval
        query_vector = self.embedding_manager.embed_query(query)
        dense_candidates = self.vector_store.query_dense(
            query_embedding=query_vector,
            top_k=candidate_k,
            filters=filters,
        )

        # 3. BM25 Sparse Retrieval
        bm25_candidates = self.bm25_index.query_sparse(
            query_text=query,
            top_k=candidate_k,
            filters=filters,
        )

        # 4. Temporal Pre-Filtering
        filtered_dense = [c for c in dense_candidates if self._apply_temporal_filter(c, as_of_date)]
        filtered_bm25 = [c for c in bm25_candidates if self._apply_temporal_filter(c, as_of_date)]

        # 5. Exact Identifier & Canonical Parameter Match
        exact_matching_cids = self.exact_index.get_matching_chunks(
            exact_identifiers=sq.exact_identifiers,
            grade=sq.grade,
            standard_code=sq.standard_code,
        )
        param_matching_cids = (
            self.exact_index.get_matching_chunks(parameter=sq.parameter)
            if sq.parameter
            else set()
        )

        # 6. Reciprocal Rank Fusion (RRF) with Multi-Factor Boosting
        rrf_scores: Dict[str, float] = {}
        chunk_lookup: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(filtered_dense, 1):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.dense_weight / (self.rrf_k + rank))
            chunk_lookup[cid] = item

        for rank, item in enumerate(filtered_bm25, 1):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (self.bm25_weight / (self.rrf_k + rank))
            if cid not in chunk_lookup:
                chunk_lookup[cid] = item

        # Multi-Factor Score Adjustments
        for cid in list(rrf_scores.keys()):
            item = chunk_lookup[cid]
            text = item.get("text", "").lower()
            meta = item.get("metadata", {})
            clause_str = str(meta.get("clause_number") or item.get("clause_number") or "")

            # Exact Identifier Match Boost (e.g. GX53, B22d, E17, Fe 500)
            if cid in exact_matching_cids:
                rrf_scores[cid] += (self.exact_weight / self.rrf_k)

            # Canonical Parameter Match Boost (e.g. insulation resistance, yield stress, elongation)
            if cid in param_matching_cids:
                rrf_scores[cid] += (self.param_weight / self.rrf_k)
                # Specific parameter disambiguation boosts
                if sq.parameter == "insulation_resistance" and (clause_str.startswith("8") or "4 m" in text or "500 v" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 2))
                elif sq.parameter == "yield_stress" and ("proof stress" in text or "yield stress" in text or "500 mpa" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 2))
                elif sq.parameter == "percentage_elongation" and "elongation" in text:
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 2))
                elif sq.parameter == "torque_moment" and (clause_str.startswith("9") or "table 2" in text or "table 3" in text or "3.0 nm" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 2))

            # Product / Domain Alignment Boost
            if sq.product:
                prod_lower = sq.product.lower()
                # Check for domain keywords
                if "led" in prod_lower and ("16102" in text or "self-ballasted" in text or "led" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "ceiling fan" in prod_lower and ("374" in text or "ceiling fan" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "cement" in prod_lower and ("269" in text or "portland cement" in text or "opc" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "helmet" in prod_lower and ("4151" in text or "helmet" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "lithium" in prod_lower and ("16046" in text or "lithium" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "cooker" in prod_lower and ("2347" in text or "cooker" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "water" in prod_lower and ("14543" in text or "drinking water" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))
                elif "steel" in prod_lower and ("1786" in text or "deformed steel" in text or "rebar" in text):
                    rrf_scores[cid] += (self.param_weight / (self.rrf_k / 3))

            # Steel grade disambiguation: Fe 500D vs Fe 500
            if sq.grade:
                grade_clean = sq.grade.lower().replace(" ", "")
                if grade_clean in text.replace(" ", ""):
                    rrf_scores[cid] += (0.8 / self.rrf_k)
                if "steel" in text:
                    rrf_scores[cid] += (0.5 / self.rrf_k)

            # Standard Code Alignment Boost
            if sq.standard_code:
                std_clean = sq.standard_code.lower().replace(" ", "")
                meta_std = str(meta.get("standard_number") or item.get("standard_number") or "").lower().replace(" ", "")
                if std_clean in meta_std:
                    rrf_scores[cid] += (0.8 / self.rrf_k)

        # Rank by fused RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # 7. Format Provenance Results
        final_results = []
        for cid in sorted_cids[:top_k]:
            item = chunk_lookup[cid]
            meta = item.get("metadata", {})
            doc_id = meta.get("document_id") or item.get("document_id") or "DOC-UNKNOWN"
            src_id = meta.get("source_id") or item.get("source_id") or f"SRC-{doc_id.split('-')[-1] if '-' in doc_id else '001'}"
            std_num = meta.get("standard_number") or item.get("standard_number") or doc_id
            clause = str(meta.get("clause_number") or item.get("clause_number") or "General")
            c_hash = meta.get("content_hash") or item.get("content_hash") or ""

            pages_raw = meta.get("pages") or item.get("pages") or "1"
            if isinstance(pages_raw, list):
                pages_list = pages_raw
            elif isinstance(pages_raw, str):
                pages_list = [int(p) for p in pages_raw.split(",") if p.strip().isdigit()]
            else:
                pages_list = [1]

            result_entry = {
                "chunk_id": cid,
                "text": item.get("text", ""),
                "score": round(rrf_scores[cid], 5),
                "document_id": doc_id,
                "version_id": meta.get("version_id") or item.get("version_id"),
                "source_id": src_id,
                "standard_number": std_num,
                "clause_number": clause,
                "chunk_type": meta.get("chunk_type") or item.get("chunk_type", "requirement"),
                "normative_force": meta.get("normative_force") or item.get("normative_force", "mandatory"),
                "temporal_status": meta.get("temporal_status") or item.get("temporal_status", "current"),
                "valid_from": meta.get("valid_from") or item.get("valid_from"),
                "valid_until": meta.get("valid_until") or item.get("valid_until"),
                "pages": pages_list,
                "content_hash": c_hash,
                "provenance": {
                    "document_id": doc_id,
                    "source_id": src_id,
                    "standard_number": std_num,
                    "clause": clause,
                    "pages": pages_list,
                },
            }
            final_results.append(result_entry)

        return final_results
