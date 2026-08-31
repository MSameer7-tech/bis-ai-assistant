"""
Embedding Provider Implementations for BIS AI Assistant (Step 2).
Provides configurable providers: SentenceTransformers (local dense embeddings)
and DeterministicEmbeddingProvider (fast unit test & offline fallback).
"""

import hashlib
import logging
import math
import os
from typing import List, Optional

from ai.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """Local embedding provider using sentence-transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", model_version: str = "1.0.0"):
        self._model_name = model_name
        self._model_version = model_version
        self._model = None
        self._dimension = 384

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading SentenceTransformer model: %s", self._model_name)
                self._model = SentenceTransformer(self._model_name)
                if hasattr(self._model, "get_embedding_dimension"):
                    self._dimension = self._model.get_embedding_dimension()
                else:
                    self._dimension = self._model.get_sentence_embedding_dimension()
            except Exception as e:
                logger.warning("Could not load SentenceTransformer (%s): %s. Falling back to deterministic embeddings.", self._model_name, e)
                self._model = None

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        if not texts:
            return []
        if self._model is not None:
            embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [e.tolist() for e in embeddings]
        # Fallback to deterministic
        det = DeterministicEmbeddingProvider(dimension=self._dimension, model_name=self._model_name)
        return det.embed_texts(texts)

    def embed_query(self, text: str) -> List[float]:
        self._load_model()
        if self._model is not None:
            emb = self._model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
            return emb.tolist()
        det = DeterministicEmbeddingProvider(dimension=self._dimension, model_name=self._model_name)
        return det.embed_query(text)


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Fast, reproducible, zero-dependency embedding provider for unit tests and CI."""

    def __init__(self, dimension: int = 384, model_name: str = "deterministic-v1", model_version: str = "1.0.0"):
        self._dimension = dimension
        self._model_name = model_name
        self._model_version = model_version

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def _hash_text_to_vector(self, text: str) -> List[float]:
        vec = [0.0] * self._dimension
        words = text.lower().split()
        for idx, word in enumerate(words):
            h_int = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            slot = h_int % self._dimension
            sign = 1.0 if (h_int // self._dimension) % 2 == 0 else -1.0
            vec[slot] += sign * (1.0 / math.sqrt(idx + 1))

        # Normalize L2
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_text_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._hash_text_to_vector(text)


def get_embedding_provider(
    provider_type: Optional[str] = None,
    model_name: Optional[str] = None,
    dimension: int = 384,
) -> BaseEmbeddingProvider:
    """Factory to instantiate the configured embedding provider."""
    p_type = provider_type or os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
    m_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if p_type in ("sentence_transformers", "local", "st"):
        return SentenceTransformerEmbeddingProvider(model_name=m_name)
    elif p_type in ("deterministic", "mock", "test"):
        return DeterministicEmbeddingProvider(dimension=dimension, model_name=m_name)
    else:
        return SentenceTransformerEmbeddingProvider(model_name=m_name)
