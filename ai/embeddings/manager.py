"""
Embedding Manager with Incremental Content-Hash Caching (Step 3).
Caches embeddings keyed by (content_hash, embedding_model, embedding_model_version)
to guarantee zero redundant embedding generation across standard updates.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai.chunking.schema import KnowledgeChunk
from ai.embeddings.base import BaseEmbeddingProvider
from ai.embeddings.provider import get_embedding_provider

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_DIR = ROOT_DIR / "data" / "vector_store"
CACHE_FILE = VECTOR_DIR / "embedding_cache.json"


class EmbeddingManager:
    """Manages embedding generation with persistent content-hash caching."""

    def __init__(
        self,
        provider: Optional[BaseEmbeddingProvider] = None,
        cache_path: Path = CACHE_FILE,
    ):
        self.provider = provider or get_embedding_provider()
        self.cache_path = cache_path
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not read embedding cache: %s. Starting fresh.", e)
        return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def _make_cache_key(self, content_hash: str) -> str:
        """Cache key: content_hash::model_name::model_version"""
        m_name = self.provider.model_name
        m_ver = self.provider.model_version
        return f"{content_hash}::{m_name}::{m_ver}"

    def get_or_create_embeddings(
        self, chunks: List[KnowledgeChunk]
    ) -> Tuple[List[List[float]], Dict[str, int]]:
        """
        Retrieves cached embeddings for unchanged chunks and generates new embeddings only for uncached chunks.
        Returns: (embeddings_list, metrics_dict)
        """
        embeddings: List[Optional[List[float]]] = [None] * len(chunks)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        reused_count = 0
        generated_count = 0

        for idx, chunk in enumerate(chunks):
            c_hash = chunk.content_hash
            cache_key = self._make_cache_key(c_hash)

            if cache_key in self.cache:
                embeddings[idx] = self.cache[cache_key]["embedding"]
                reused_count += 1
            else:
                missing_indices.append(idx)
                missing_texts.append(chunk.text)

        # Batch embed missing texts
        if missing_texts:
            logger.info("Generating embeddings for %d new/modified chunks...", len(missing_texts))
            new_vectors = self.provider.embed_texts(missing_texts)
            now_iso = datetime.now(timezone.utc).isoformat()

            for i, vec in enumerate(new_vectors):
                orig_idx = missing_indices[i]
                embeddings[orig_idx] = vec
                c_hash = chunks[orig_idx].content_hash
                cache_key = self._make_cache_key(c_hash)

                self.cache[cache_key] = {
                    "embedding": vec,
                    "content_hash": c_hash,
                    "model_name": self.provider.model_name,
                    "model_version": self.provider.model_version,
                    "dimension": len(vec),
                    "created_at": now_iso,
                }
                generated_count += 1

            self._save_cache()

        metrics = {
            "reused": reused_count,
            "generated": generated_count,
            "total": len(chunks),
        }
        return [e for e in embeddings if e is not None], metrics

    def embed_query(self, query: str) -> List[float]:
        """Embeds a user query using the active embedding model."""
        return self.provider.embed_query(query)
