"""
Incremental Indexer for BIS Vector Store & BM25 Index (Step 12).
Evaluates chunk_id and content_hash to selectively embed only added/modified chunks,
reusing unchanged vectors and purging obsolete chunks.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ai.chunking.schema import KnowledgeChunk
from ai.embeddings.manager import EmbeddingManager
from ai.ingestion.manifest import IngestionManifestManager
from ai.vectorstore.base import BaseVectorStore
from ai.vectorstore.bm25_index import BM25Index
from ai.vectorstore.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"


class IncrementalIndexer:
    """Orchestrates incremental chunk indexing into ChromaDB and BM25 with content-hash checking."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        bm25_index: Optional[BM25Index] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        manifest_manager: Optional[IngestionManifestManager] = None,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_index = bm25_index or BM25Index()
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.manifest_manager = manifest_manager or IngestionManifestManager()

    def load_all_chunks(self) -> List[KnowledgeChunk]:
        """Loads all valid chunk files from data/chunks/."""
        all_chunks: List[KnowledgeChunk] = []
        for cf in sorted(CHUNKS_DIR.glob("DOC-*.json")):
            if cf.name.endswith(".chunks.json"):
                continue
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    chunk_dicts = json.load(f)
                    for cd in chunk_dicts:
                        all_chunks.append(KnowledgeChunk.model_validate(cd))
            except Exception as e:
                logger.error("Failed loading chunk file %s: %s", cf.name, e)
        return all_chunks

    def index_chunks(
        self, chunks: Optional[List[KnowledgeChunk]] = None
    ) -> Dict[str, Any]:
        """
        Executes incremental indexing:
        - Unchanged (same chunk_id and content_hash) -> Reuse
        - Modified (same chunk_id, different content_hash) -> Re-embed & Update
        - Added (new chunk_id) -> Embed & Insert
        - Deleted (in index, not in chunks) -> Purge
        """
        if chunks is None:
            chunks = self.load_all_chunks()

        current_chunk_ids: Set[str] = {c.chunk_id for c in chunks}
        current_by_id: Dict[str, KnowledgeChunk] = {c.chunk_id: c for c in chunks}

        # Inspect existing vector store records
        chunks_to_embed: List[KnowledgeChunk] = []
        unchanged_count = 0
        modified_count = 0
        added_count = 0

        for chunk in chunks:
            existing_rec = self.vector_store.get_chunk(chunk.chunk_id)
            if not existing_rec:
                # New chunk
                chunks_to_embed.append(chunk)
                added_count += 1
            else:
                old_hash = existing_rec.get("metadata", {}).get("content_hash")
                if old_hash and old_hash == chunk.content_hash:
                    # Unchanged -> reuse
                    unchanged_count += 1
                else:
                    # Modified -> re-embed
                    chunks_to_embed.append(chunk)
                    modified_count += 1

        # Embed added/modified chunks
        embeddings_generated = 0
        if chunks_to_embed:
            vectors, emb_metrics = self.embedding_manager.get_or_create_embeddings(chunks_to_embed)
            self.vector_store.upsert_chunks(chunks_to_embed, vectors)
            embeddings_generated = emb_metrics["generated"]

        # Check for deleted chunks within the scope of indexed documents
        indexed_ids = set(self.vector_store.get_all_chunk_ids())
        indexed_doc_ids = {c.document_id for c in chunks}
        deleted_ids = [
            cid for cid in indexed_ids
            if any(cid.startswith(f"{doc_id}-") or cid.startswith(f"{doc_id}:") for doc_id in indexed_doc_ids)
            and cid not in current_chunk_ids
        ]

        if deleted_ids:
            self.vector_store.delete_chunks(deleted_ids)
            self.bm25_index.delete_chunks(deleted_ids)
            logger.info("🗑️ Purged %d obsolete chunks from vector store and BM25", len(deleted_ids))

        # Update BM25 Index
        self.bm25_index.build_or_update(chunks)

        # Update Ingestion Manifest
        self.manifest_manager.generate_manifest()

        metrics = {
            "total_chunks": len(chunks),
            "unchanged_count": unchanged_count,
            "modified_count": modified_count,
            "added_count": added_count,
            "deleted_count": len(deleted_ids),
            "embeddings_reused": unchanged_count,
            "embeddings_generated": embeddings_generated,
            "vector_store_count": self.vector_store.count(),
        }

        logger.info(
            "📊 Indexing Complete: %d total chunks | %d unchanged | %d modified | %d added | %d vectors generated",
            metrics["total_chunks"],
            metrics["unchanged_count"],
            metrics["modified_count"],
            metrics["added_count"],
            metrics["embeddings_generated"],
        )
        return metrics
