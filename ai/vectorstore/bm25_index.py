"""
BM25 Sparse Lexical Index for BIS Standards (Step 6).
Preserves specialized technical terminology, units, standard numbers, and cap style codes:
e.g. 'IS 16102', 'GX53', 'B22d', '4 MΩ', '120 K', '1.5 Nm', '8.1.1'.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rank_bm25 import BM25Plus

from ai.chunking.schema import KnowledgeChunk

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BM25_STORAGE_PATH = ROOT_DIR / "data" / "vector_store" / "bm25_index.json"

# Regex tokenization pattern that keeps compound standard codes and alphanumeric technical terms intact
TECHNICAL_TOKEN_PATTERN = re.compile(
    r"[A-Z]{1,4}\s+\d+(?:\s*\([^\)]+\))?(?::\s*\d{4})?"  # Matches "IS 16102 (Part 1) : 2012"
    r"|\d+(?:\.\d+)+"                                      # Matches "8.1.1", "10.2"
    r"|\d+(?:\.\d+)?\s*(?:MΩ|kΩ|Ω|Nm|K|°C|V|W|Hz|mm|kg|h|min|s|percent|%)" # Matches "4 MΩ", "120 K", "1.5 Nm"
    r"|[A-Z0-9]+[a-z]*\d*"                                # Matches "GX53", "B22d", "E17", "E27"
    r"|\w+",
    re.IGNORECASE,
)


QUESTION_STOPWORDS = {
    "which", "what", "where", "who", "when", "why", "how",
    "is", "are", "was", "were", "does", "do", "did",
    "the", "a", "an", "of", "to", "for", "in", "on", "by", "with",
    "and", "or", "as", "at", "from", "under", "covers", "applies", "specifies"
}


def tokenize_bis_text(text: str, is_query: bool = False) -> List[str]:
    """Tokenizes text preserving domain-specific BIS terminology and numerical units."""
    matches = TECHNICAL_TOKEN_PATTERN.findall(text)
    tokens = []
    for m in matches:
        clean = m.strip().lower()
        if len(clean) > 0:
            if is_query and clean in QUESTION_STOPWORDS:
                continue
            tokens.append(clean)
            parts = clean.split()
            if len(parts) > 1:
                for p in parts:
                    if is_query and p in QUESTION_STOPWORDS:
                        continue
                    if len(p) > 0:
                        tokens.append(p)
    return tokens


class BM25Index:
    """Persistent BM25 sparse index for exact technical and clause-level keyword retrieval."""

    def __init__(self, storage_path: Path = BM25_STORAGE_PATH):
        self.storage_path = storage_path
        self.chunk_ids: List[str] = []
        self.corpus: List[List[str]] = []
        self.chunk_records: Dict[str, Dict[str, Any]] = {}
        self.bm25: Optional[BM25Okapi] = None
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.chunk_ids = data.get("chunk_ids", [])
                self.chunk_records = data.get("chunk_records", {})
                self.corpus = [tokenize_bis_text(self.chunk_records[cid]["text"]) for cid in self.chunk_ids]
                if self.corpus:
                    self.bm25 = BM25Plus(self.corpus)
                logger.info("Loaded BM25 index with %d documents from %s", len(self.chunk_ids), self.storage_path.name)
            except Exception as e:
                logger.warning("Could not load BM25 index: %s", e)

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunk_ids": self.chunk_ids,
            "chunk_records": self.chunk_records,
            "total_documents": len(self.chunk_ids),
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def build_or_update(self, chunks: List[KnowledgeChunk]):
        """Builds or incrementally updates the BM25 index."""
        for c in chunks:
            self.chunk_records[c.chunk_id] = {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "version_id": c.version_id or "",
                "standard_number": c.standard_number or "",
                "clause_number": c.clause_number or c.clause.number,
                "parent_clause": c.parent_clause or "",
                "section_number": c.section_number or "",
                "chunk_type": c.chunk_type.value if hasattr(c.chunk_type, "value") else str(c.chunk_type),
                "normative_force": c.normative_force or "informative",
                "temporal_status": c.temporal_status or "current",
                "valid_from": c.valid_from or "",
                "valid_until": c.valid_until or "",
                "pages": ",".join(map(str, c.pages or c.page_refs or [1])),
                "content_hash": c.content_hash or "",
                "title": c.title or "",
                "text": c.text,
            }

        self.chunk_ids = list(self.chunk_records.keys())
        self.corpus = [tokenize_bis_text(self.chunk_records[cid]["text"]) for cid in self.chunk_ids]
        if self.corpus:
            self.bm25 = BM25Plus(self.corpus)
        self._save()
        logger.info("✅ Built BM25 index with %d chunks", len(self.chunk_ids))

    def delete_chunks(self, chunk_ids: List[str]):
        for cid in chunk_ids:
            self.chunk_records.pop(cid, None)
        self.chunk_ids = list(self.chunk_records.keys())
        self.corpus = [tokenize_bis_text(self.chunk_records[cid]["text"]) for cid in self.chunk_ids]
        if self.corpus:
            self.bm25 = BM25Plus(self.corpus)
        else:
            self.bm25 = None
        self._save()

    def query_sparse(
        self, query_text: str, top_k: int = 20, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Queries the BM25 index with tokenized query."""
        if not self.bm25 or not self.chunk_ids:
            return []

        tokens = tokenize_bis_text(query_text, is_query=True)
        if not tokens:
            tokens = tokenize_bis_text(query_text, is_query=False)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []

        for idx, score in scored_indices:
            if score <= 0.0:
                continue
            cid = self.chunk_ids[idx]
            rec = self.chunk_records[cid]

            # Apply filters if present
            if filters:
                match = True
                for k, v in filters.items():
                    if rec.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append({
                "chunk_id": cid,
                "text": rec.get("text", ""),
                "metadata": rec,
                "score": float(score),
            })
            if len(results) >= top_k:
                break

        return results
