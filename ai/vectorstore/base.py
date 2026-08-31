"""
Abstract Vector Store Interface for BIS AI Assistant (Step 4).
Decouples retrieval and ingestion orchestration from specific vector DB implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ai.chunking.schema import KnowledgeChunk


class BaseVectorStore(ABC):
    """Abstract interface for dense vector persistence and querying."""

    @abstractmethod
    def upsert_chunks(
        self, chunks: List[KnowledgeChunk], embeddings: List[List[float]]
    ) -> None:
        """Upserts knowledge chunks with their corresponding dense vector embeddings."""
        pass

    @abstractmethod
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """Removes chunks by their unique chunk_id from the vector index."""
        pass

    @abstractmethod
    def query_dense(
        self,
        query_embedding: List[float],
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Queries nearest neighbor chunks with optional metadata filtering."""
        pass

    @abstractmethod
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single chunk record by ID."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns the total number of indexed vectors."""
        pass

    @abstractmethod
    def get_all_chunk_ids(self) -> List[str]:
        """Returns all indexed chunk_id keys."""
        pass
