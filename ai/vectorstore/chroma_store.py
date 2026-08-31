"""
ChromaDB Vector Store Implementation (Steps 4 & 5).
Persists dense vector embeddings with flattened metadata for high-precision query filtering.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from ai.chunking.schema import KnowledgeChunk
from ai.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = ROOT_DIR / "data" / "vector_store" / "chroma"
DEFAULT_COLLECTION = "bis_standards_knowledge"


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation of BaseVectorStore with persistent on-disk storage."""

    def __init__(
        self,
        persist_directory: Path = CHROMA_PATH,
        collection_name: str = DEFAULT_COLLECTION,
    ):
        self.persist_directory = persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "BIS Indian Standards Knowledge Chunks with Provenance"},
        )

    def _extract_metadata(self, chunk: KnowledgeChunk) -> Dict[str, Any]:
        """Flattens chunk metadata to comply with ChromaDB scalar requirements (Step 5)."""
        pages_str = ",".join(map(str, chunk.pages or chunk.page_refs or [1]))
        return {
            "document_id": str(chunk.document_id),
            "version_id": str(chunk.version_id or ""),
            "source_id": str(chunk.source_id),
            "standard_number": str(chunk.standard_number or ""),
            "clause_number": str(chunk.clause_number or chunk.clause.number),
            "parent_clause": str(chunk.parent_clause or ""),
            "section_number": str(chunk.section_number or ""),
            "chunk_type": str(chunk.chunk_type.value if hasattr(chunk.chunk_type, "value") else chunk.chunk_type),
            "normative_force": str(chunk.normative_force or "informative"),
            "temporal_status": str(chunk.temporal_status or "current"),
            "valid_from": str(chunk.valid_from or ""),
            "valid_until": str(chunk.valid_until or ""),
            "pages": pages_str,
            "content_hash": str(chunk.content_hash or ""),
            "title": str(chunk.title or ""),
        }

    def upsert_chunks(
        self, chunks: List[KnowledgeChunk], embeddings: List[List[float]]
    ) -> None:
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [self._extract_metadata(c) for c in chunks]

        # Chroma upsert handles batches
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("✅ Upserted %d vectors to ChromaDB collection '%s'", len(ids), self.collection.name)

    def delete_chunks(self, chunk_ids: List[str]) -> None:
        if not chunk_ids:
            return
        self.collection.delete(ids=chunk_ids)
        logger.info("🗑️ Deleted %d vectors from ChromaDB", len(chunk_ids))

    def query_dense(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        where_clause = None
        if filters:
            # Build Chroma where clause
            conditions = [{k: {"$eq": v}} for k, v in filters.items()]
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$and": conditions}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0] if results["documents"] else []
            metas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []

            for i in range(len(ids)):
                dist = distances[i] if i < len(distances) else 1.0
                # Cosine similarity conversion
                score = 1.0 - (dist / 2.0) if dist <= 2.0 else 0.0

                formatted_results.append({
                    "chunk_id": ids[i],
                    "text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "score": score,
                    "distance": dist,
                })

        return formatted_results

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        res = self.collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas", "embeddings"],
        )
        if res and res.get("ids") and len(res["ids"]) > 0:
            embs = res.get("embeddings")
            emb = embs[0] if (embs is not None and len(embs) > 0) else None
            return {
                "chunk_id": res["ids"][0],
                "text": res["documents"][0] if res.get("documents") else "",
                "metadata": res["metadatas"][0] if res.get("metadatas") else {},
                "embedding": emb,
            }
        return None

    def count(self) -> int:
        return self.collection.count()

    def get_all_chunk_ids(self) -> List[str]:
        res = self.collection.get(include=[])
        return res.get("ids", []) if res else []
