"""
Phase 5F: Incremental RAG Document-Level Indexer.
Performs selective chunk diffing, vector deletion, and upsertion for changed documents
without rebuilding or retraining the vector database.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHUNKS_DIR = DATA_DIR / "chunks"

from ai.chunking.chunker import StructureAwareChunker
from ai.chunking.chunk_diff import ChunkDiffEngine
from ai.embeddings.manager import EmbeddingManager
from ai.vectorstore.chroma_store import ChromaStoreManager
from ai.retrieval.exact_index import ExactInvertedIndex


class IncrementalIndexer:
    """
    Manages document-level vector indexing and chunk synchronization.
    """

    def __init__(self):
        self.chunker = StructureAwareChunker()
        self.diff_engine = ChunkDiffEngine()
        self.embedding_mgr = EmbeddingManager.get_instance()
        self.vector_store = ChromaStoreManager.get_instance()
        self.exact_index = ExactInvertedIndex()

    def update_document_index(
        self,
        document_id: str,
        normalized_doc: Dict[str, Any],
        previous_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Incrementally updates vectors and index postings for a single document.
        """
        logger.info(f"Incrementally updating RAG index for document {document_id}...")

        # 1. Generate new chunks
        new_chunks = self.chunker.chunk_document(normalized_doc)
        
        # 2. Compute Chunk Diff against previous chunks
        diff_report = self.diff_engine.compute_diff(
            old_chunks=previous_chunks or [],
            new_chunks=new_chunks
        )

        removed_ids = diff_report.get("removed_chunk_ids", [])
        added_chunks = diff_report.get("added_chunks", [])
        modified_chunks = diff_report.get("modified_chunks", [])
        unchanged_chunks = diff_report.get("unchanged_chunks", [])

        # 3. Delete removed chunks from ChromaDB
        if removed_ids:
            try:
                self.vector_store.delete_chunks(removed_ids)
                logger.info(f"  Deleted {len(removed_ids)} obsolete chunk vectors.")
            except Exception as e:
                logger.warning(f"Vector deletion notice: {e}")

        # 4. Embed & Upsert added + modified chunks
        chunks_to_upsert = added_chunks + modified_chunks
        if chunks_to_upsert:
            embeddings = self.embedding_mgr.embed_chunks(chunks_to_upsert)
            self.vector_store.upsert_chunks(chunks_to_upsert, embeddings)
            logger.info(f"  Upserted {len(chunks_to_upsert)} new/modified chunk vectors.")

        # 5. Save updated chunk file to data/chunks/
        chunk_file = CHUNKS_DIR / f"{document_id}.chunks.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(new_chunks, f, indent=2, ensure_ascii=False)

        return {
            "document_id": document_id,
            "total_chunks": len(new_chunks),
            "added": len(added_chunks),
            "modified": len(modified_chunks),
            "removed": len(removed_ids),
            "unchanged": len(unchanged_chunks),
            "status": "INDEX_SYNCHRONIZED"
        }
