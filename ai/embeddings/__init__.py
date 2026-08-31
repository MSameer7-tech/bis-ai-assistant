"""
Embeddings Subpackage for BIS AI Assistant.
Provides configurable dense embedding providers and content-hash caching managers.
"""

from ai.embeddings.base import BaseEmbeddingProvider
from ai.embeddings.manager import EmbeddingManager
from ai.embeddings.provider import (
    DeterministicEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    get_embedding_provider,
)

__all__ = [
    "BaseEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "DeterministicEmbeddingProvider",
    "get_embedding_provider",
    "EmbeddingManager",
]
