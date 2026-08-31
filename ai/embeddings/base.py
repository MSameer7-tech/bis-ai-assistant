"""
Abstract Base Embedding Provider Interface for BIS AI Assistant (Step 2).
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding generation."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a list of text passages."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generates a dense vector embedding for a search query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the dimensionality of the vector embeddings."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the identifier name of the embedding model."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Returns the version string of the embedding model."""
        pass
