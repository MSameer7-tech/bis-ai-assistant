"""
Vector Store Subpackage for BIS AI Assistant.
Provides persistent vector databases, sparse BM25 indices, incremental indexing engines, and hybrid retrieval.
"""

from ai.vectorstore.base import BaseVectorStore
from ai.vectorstore.bm25_index import BM25Index, tokenize_bis_text
from ai.vectorstore.chroma_store import ChromaVectorStore
from ai.vectorstore.hybrid_search import HybridSearchEngine
from ai.vectorstore.indexer import IncrementalIndexer

__all__ = [
    "BaseVectorStore",
    "ChromaVectorStore",
    "BM25Index",
    "tokenize_bis_text",
    "HybridSearchEngine",
    "IncrementalIndexer",
]
