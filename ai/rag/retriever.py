"""
Phase 4 Retriever Adapter for Phase 3 HybridSearchEngine.
Validates the retrieval contract and returns strongly-typed RetrievedChunk objects.
"""
import logging
from typing import List, Optional, Dict, Any
from ai.vectorstore.hybrid_search import HybridSearchEngine
from ai.rag.models import RetrievedChunk

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Adapter consuming Phase 3 HybridSearchEngine output and converting raw results
    into strongly-typed, validated RetrievedChunk models.
    """

    def __init__(self, search_engine: Optional[HybridSearchEngine] = None):
        self.engine = search_engine or HybridSearchEngine()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        as_of_date: Optional[str] = None,
        candidate_k: int = 20
    ) -> List[RetrievedChunk]:
        """
        Executes hybrid dense + sparse retrieval and maps results to validated RetrievedChunk models.

        Args:
            query: User natural language or keyword query
            top_k: Number of final fused chunks to return
            as_of_date: Optional temporal ISO date string (YYYY-MM-DD)
            candidate_k: Number of top candidates to pull from dense and sparse streams

        Returns:
            List of validated RetrievedChunk instances
        """
        raw_results = self.engine.search(
            query=query,
            top_k=top_k,
            as_of_date=as_of_date,
            candidate_k=candidate_k
        )

        retrieved_chunks: List[RetrievedChunk] = []

        for item in raw_results:
            # Strict contract validation - check mandatory provenance attributes
            chunk_id = item.get("chunk_id")
            doc_id = item.get("document_id")
            src_id = item.get("source_id")
            std_num = item.get("standard_number")
            clause = item.get("clause_number")
            pages = item.get("pages", [])
            text = item.get("text", "")
            c_hash = item.get("content_hash", "")

            if not chunk_id or not doc_id or not src_id or not text or not c_hash:
                logger.error(
                    "Retrieved item missing mandatory provenance! chunk_id=%s, doc_id=%s, src_id=%s",
                    chunk_id, doc_id, src_id
                )
                raise ValueError(
                    f"Retrieved chunk {chunk_id} violates Phase 3 contract: missing mandatory provenance."
                )

            # Standardize pages list
            if isinstance(pages, str):
                try:
                    pages = [int(p.strip()) for p in pages.split(",") if p.strip()]
                except Exception:
                    pages = []

            chunk_model = RetrievedChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                version_id=item.get("version_id"),
                source_id=src_id,
                standard_number=std_num or doc_id,
                clause_number=str(clause or "General"),
                pages=pages,
                chunk_type=item.get("chunk_type", "requirement"),
                normative_force=item.get("normative_force", "mandatory"),
                temporal_status=item.get("temporal_status", "current"),
                valid_from=item.get("valid_from"),
                valid_until=item.get("valid_until"),
                score=float(item.get("score", 0.0)),
                text=text,
                content_hash=c_hash,
                provenance=item.get("provenance", {})
            )
            retrieved_chunks.append(chunk_model)

        logger.info(
            "Retrieved %d validated chunks for query '%s' (as_of=%s)",
            len(retrieved_chunks), query, as_of_date
        )
        return retrieved_chunks
