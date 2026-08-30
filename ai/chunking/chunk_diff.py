"""
Chunk-Level Change Detection and Hash Diff Engine (Step 8).
Compares individual knowledge chunks between standard editions to enable granular,
incremental vector re-embedding (only re-embedding modified/added chunks rather than the entire document).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def get_chunk_semantic_key(chunk: Dict[str, Any]) -> str:
    """Computes a semantic identifier key for a chunk across versions."""
    c_type = chunk.get("chunk_type", "gen")
    c_num = str(chunk.get("clause", {}).get("number", "0"))
    title = str(chunk.get("title", "") or chunk.get("term", "") or chunk.get("table_number", ""))
    return f"{c_type}::{c_num}::{title}".strip()


class ChunkDiffEngine:
    """Computes delta across chunk sets using cryptographic content hashes."""

    def compare_chunk_sets(
        self, old_chunks: List[Dict[str, Any]], new_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        old_by_key: Dict[str, Dict[str, Any]] = {get_chunk_semantic_key(c): c for c in old_chunks}
        new_by_key: Dict[str, Dict[str, Any]] = {get_chunk_semantic_key(c): c for c in new_chunks}

        unchanged: List[Dict[str, Any]] = []
        modified: List[Dict[str, Any]] = []
        added: List[Dict[str, Any]] = []
        deleted: List[Dict[str, Any]] = []

        for key, n_chunk in new_by_key.items():
            if key not in old_by_key:
                added.append(n_chunk)
            else:
                o_chunk = old_by_key[key]
                o_hash = o_chunk.get("content_hash")
                n_hash = n_chunk.get("content_hash")

                if o_hash and n_hash and o_hash == n_hash:
                    unchanged.append({
                        "chunk_id": n_chunk.get("chunk_id"),
                        "clause": n_chunk.get("clause", {}).get("number"),
                        "content_hash": n_hash,
                    })
                else:
                    modified.append({
                        "old_chunk_id": o_chunk.get("chunk_id"),
                        "new_chunk_id": n_chunk.get("chunk_id"),
                        "clause": n_chunk.get("clause", {}).get("number"),
                        "old_content_hash": o_hash,
                        "new_content_hash": n_hash,
                        "title": n_chunk.get("title"),
                    })

        for key, o_chunk in old_by_key.items():
            if key not in new_by_key:
                deleted.append(o_chunk)

        reembed_required_count = len(modified) + len(added)

        return {
            "total_old_chunks": len(old_chunks),
            "total_new_chunks": len(new_chunks),
            "unchanged_count": len(unchanged),
            "modified_count": len(modified),
            "added_count": len(added),
            "deleted_count": len(deleted),
            "reembed_required_count": reembed_required_count,
            "can_skip_full_reindex": len(unchanged) > 0 and len(unchanged) == len(new_chunks),
            "unchanged_chunks": unchanged,
            "modified_chunks": modified,
            "added_chunks": added,
            "deleted_chunks": deleted,
        }

    def compare_chunk_files(self, old_chunks_path: Path, new_chunks_path: Path) -> Dict[str, Any]:
        with open(old_chunks_path, "r", encoding="utf-8") as f:
            old_chunks = json.load(f)
        with open(new_chunks_path, "r", encoding="utf-8") as f:
            new_chunks = json.load(f)
        return self.compare_chunk_sets(old_chunks, new_chunks)


def compare_chunks(old_path: Path, new_path: Path) -> Dict[str, Any]:
    """Convenience helper function to compare two chunk JSON files."""
    engine = ChunkDiffEngine()
    return engine.compare_chunk_files(old_path, new_path)
