"""
Validation tests for Chunk-Level Hash Diff Engine (Step 8).
"""

import pytest
from ai.chunking.chunk_diff import ChunkDiffEngine


def test_chunk_diff_engine_identical_chunks():
    """Verify that identical chunk sets report 0 re-embedding required."""
    chunks = [
        {
            "chunk_id": "DOC-001-v001::8.1.1::REQ-001",
            "chunk_type": "requirement",
            "title": "Insulation Resistance",
            "clause": {"number": "8.1.1"},
            "content_hash": "hash_123456",
        },
        {
            "chunk_id": "DOC-001-v001::3.1::DEF-001",
            "chunk_type": "definition",
            "title": "Definition: Self-Ballasted LED Lamp",
            "clause": {"number": "3.1"},
            "content_hash": "hash_abcdef",
        },
    ]

    engine = ChunkDiffEngine()
    diff = engine.compare_chunk_sets(chunks, chunks)

    assert diff["total_old_chunks"] == 2
    assert diff["total_new_chunks"] == 2
    assert diff["unchanged_count"] == 2
    assert diff["modified_count"] == 0
    assert diff["added_count"] == 0
    assert diff["deleted_count"] == 0
    assert diff["reembed_required_count"] == 0
    assert diff["can_skip_full_reindex"] is True


def test_chunk_diff_engine_modified_and_added_chunks():
    """Verify granular re-embedding detection when a single chunk is modified and one is added."""
    old_chunks = [
        {
            "chunk_id": "DOC-001-v001::8.1.1::REQ-001",
            "chunk_type": "requirement",
            "title": "Insulation Resistance",
            "clause": {"number": "8.1.1"},
            "content_hash": "hash_123456",
        },
        {
            "chunk_id": "DOC-001-v001::3.1::DEF-001",
            "chunk_type": "definition",
            "title": "Definition: Self-Ballasted LED Lamp",
            "clause": {"number": "3.1"},
            "content_hash": "hash_abcdef",
        },
    ]

    new_chunks = [
        {
            "chunk_id": "DOC-001-v002::8.1.1::REQ-001",
            "chunk_type": "requirement",
            "title": "Insulation Resistance",
            "clause": {"number": "8.1.1"},
            "content_hash": "hash_MODIFIED_999",  # Modified!
        },
        {
            "chunk_id": "DOC-001-v002::3.1::DEF-001",
            "chunk_type": "definition",
            "title": "Definition: Self-Ballasted LED Lamp",
            "clause": {"number": "3.1"},
            "content_hash": "hash_abcdef",  # Unchanged!
        },
        {
            "chunk_id": "DOC-001-v002::12.1::REQ-002",
            "chunk_type": "requirement",
            "title": "Resistance to Flame",
            "clause": {"number": "12.1"},
            "content_hash": "hash_NEW_777",  # Added!
        },
    ]

    engine = ChunkDiffEngine()
    diff = engine.compare_chunk_sets(old_chunks, new_chunks)

    assert diff["unchanged_count"] == 1
    assert diff["modified_count"] == 1
    assert diff["added_count"] == 1
    assert diff["reembed_required_count"] == 2  # Only 2 out of 3 need re-embedding!
    assert diff["can_skip_full_reindex"] is False
