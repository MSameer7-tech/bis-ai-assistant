"""
Automated Validation Test Suite for Data Freshness, Change Detection,
Semantic Diff, Chunk-Level Re-Embedding, and Temporal Versioning (Step 15).
"""

import json
from pathlib import Path
import pytest
from ai.chunking.chunk_diff import ChunkDiffEngine
from ai.ingestion.change_detector import ChangeDetector
from ai.ingestion.status import DocumentStatus
from ai.ingestion.versioning import DocumentVersion, make_version_id
from ai.versioning.amendment_processor import AmendmentProcessor
from ai.versioning.semantic_diff import SemanticDiffEngine
from ai.versioning.temporal_engine import TemporalEngine

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PDF = ROOT_DIR / "data" / "raw" / "standards" / "IS_16102_Part_1_2012.pdf"
SAMPLE_REV_PDF = ROOT_DIR / "data" / "raw" / "standards" / "IS_16102_Part_1_2026.pdf"
DOC_001_CHUNKS = ROOT_DIR / "data" / "chunks" / "DOC-001.json"


def test_same_pdf_is_unchanged():
    """Verify that scanning identical PDF returns has_changed=False and status unchanged."""
    detector = ChangeDetector()
    res = detector.check_document_change("DOC-001", current_file_path=SAMPLE_PDF, update_history=False)
    assert res["has_changed"] is False
    assert res["change_type"] == "identical"
    assert res["action_required"] == "none"


def test_modified_pdf_detected():
    """Verify that a modified PDF with a different SHA-256 hash is detected immediately."""
    detector = ChangeDetector()
    # Pass 2026 PDF under DOC-001 ID to simulate a modified file
    res = detector.check_document_change("DOC-001", current_file_path=SAMPLE_REV_PDF, update_history=False)
    assert res["has_changed"] is True
    assert res["change_type"] == "content_update"
    assert res["action_required"] == "reprocess_and_reembed"


def test_new_document_detected():
    """Verify that an unregistered document is flagged for registration and processing."""
    detector = ChangeDetector()
    res = detector.check_document_change("DOC-999-NEW", current_file_path=SAMPLE_PDF, update_history=False)
    assert res["has_changed"] is True
    assert res["change_type"] == "unregistered_document"


def test_version_created():
    """Verify standard incremental version ID creation: DOC-001-v002."""
    v_id = make_version_id("DOC-001", 2)
    assert v_id == "DOC-001-v002"

    v_obj = DocumentVersion(
        version_id=v_id,
        document_id="DOC-001",
        version_number=2,
        version_label="IS 16102 (Part 1) : 2026",
        sha256="ad4cf30f69320a2937b6c77a032ab528032fdb84f176b1a7ace7a0a7924d2465",
        local_path="data/raw/standards/IS_16102_Part_1_2026.pdf",
    )
    assert v_obj.version_id == "DOC-001-v002"
    assert v_obj.version_number == 2


def test_old_version_preserved():
    """Verify that old versions are marked superseded and not lost from history."""
    processor = AmendmentProcessor()
    base_doc = {
        "document_id": "DOC-001",
        "document_metadata": {"publication_date": "2012-08-01"},
        "requirements": [
            {
                "requirement_id": "REQ-001",
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 4.0,
                "unit": "MΩ",
                "temporal_status": "current",
            }
        ],
    }
    amd_doc = {
        "document_id": "DOC-012",
        "requirements": [
            {
                "requirement_id": "REQ-092",
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 5.0,
                "unit": "MΩ",
            }
        ],
    }

    consolidated = processor.apply_amendment_to_base(base_doc, amd_doc, effective_date="2026-07-01")

    # Both old and new exist in the requirements repository
    all_reqs = consolidated["requirements"]
    assert len(all_reqs) == 2

    old_req = next(r for r in all_reqs if r["requirement_id"] == "REQ-001")
    assert old_req["temporal_status"] == "superseded"
    assert old_req["valid_until"] == "2026-07-01"
    assert old_req["superseded_by"] == "REQ-092"

    new_req = next(r for r in all_reqs if r["requirement_id"] == "REQ-092")
    assert new_req["temporal_status"] == "current"
    assert new_req["valid_from"] == "2026-07-01"
    assert new_req["valid_until"] is None


def test_requirement_added():
    """Verify semantic diff detects added requirements."""
    engine = SemanticDiffEngine()
    old_doc = {"requirements": []}
    new_doc = {
        "requirements": [
            {"parameter": "rated_wattage", "clause": "1.2", "operator": "<=", "value": 60.0, "unit": "W"}
        ]
    }
    diff = engine.compare_documents(old_doc, new_doc)
    assert diff["requirements_diff"]["added_count"] == 1
    assert diff["requirements_diff"]["added"][0]["parameter"] == "rated_wattage"


def test_requirement_removed():
    """Verify semantic diff detects removed requirements."""
    engine = SemanticDiffEngine()
    old_doc = {
        "requirements": [
            {"parameter": "rated_wattage", "clause": "1.2", "operator": "<=", "value": 60.0, "unit": "W"}
        ]
    }
    new_doc = {"requirements": []}
    diff = engine.compare_documents(old_doc, new_doc)
    assert diff["requirements_diff"]["removed_count"] == 1
    assert diff["requirements_diff"]["removed"][0]["parameter"] == "rated_wattage"


def test_requirement_modified():
    """Verify semantic diff detects modified requirements with exact values (old 4 MΩ vs new 5 MΩ)."""
    engine = SemanticDiffEngine()
    old_doc = {
        "requirements": [
            {
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 4.0,
                "unit": "MΩ",
            }
        ]
    }
    new_doc = {
        "requirements": [
            {
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 5.0,
                "unit": "MΩ",
            }
        ]
    }
    diff = engine.compare_documents(old_doc, new_doc)
    assert diff["requirements_diff"]["modified_count"] == 1
    mod = diff["requirements_diff"]["modified"][0]
    assert mod["parameter"] == "insulation_resistance"
    assert mod["old_value"] == 4.0
    assert mod["new_value"] == 5.0


def test_chunk_added():
    """Verify chunk diff engine detects newly added chunks."""
    engine = ChunkDiffEngine()
    old_chunks = []
    new_chunks = [
        {"chunk_id": "C-001", "chunk_type": "req", "clause": {"number": "1.1"}, "content_hash": "h1"}
    ]
    diff = engine.compare_chunk_sets(old_chunks, new_chunks)
    assert diff["added_count"] == 1
    assert diff["reembed_required_count"] == 1


def test_chunk_removed():
    """Verify chunk diff engine detects removed chunks to delete from vector index."""
    engine = ChunkDiffEngine()
    old_chunks = [
        {"chunk_id": "C-001", "chunk_type": "req", "clause": {"number": "1.1"}, "content_hash": "h1"}
    ]
    new_chunks = []
    diff = engine.compare_chunk_sets(old_chunks, new_chunks)
    assert diff["deleted_count"] == 1
    assert diff["reembed_required_count"] == 0


def test_chunk_modified():
    """Verify chunk diff engine detects content hash mismatches for the same clause."""
    engine = ChunkDiffEngine()
    old_chunks = [
        {"chunk_id": "C-001", "chunk_type": "req", "clause": {"number": "8.1.1"}, "content_hash": "hash_OLD"}
    ]
    new_chunks = [
        {"chunk_id": "C-001", "chunk_type": "req", "clause": {"number": "8.1.1"}, "content_hash": "hash_NEW"}
    ]
    diff = engine.compare_chunk_sets(old_chunks, new_chunks)
    assert diff["modified_count"] == 1
    assert diff["reembed_required_count"] == 1


def test_unchanged_chunks_reuse_embeddings():
    """Verify that unchanged chunks are flagged to reuse existing embeddings (0 re-embed)."""
    engine = ChunkDiffEngine()
    chunks = [
        {"chunk_id": "C-001", "chunk_type": "req", "clause": {"number": "1"}, "content_hash": "h1"},
        {"chunk_id": "C-002", "chunk_type": "def", "clause": {"number": "3"}, "content_hash": "h2"},
    ]
    diff = engine.compare_chunk_sets(chunks, chunks)
    assert diff["unchanged_count"] == 2
    assert diff["reembed_required_count"] == 0
    assert diff["can_skip_full_reindex"] is True


def test_changed_chunks_reembedded():
    """Verify that only the modified chunk out of 100 chunks is marked for re-embedding."""
    engine = ChunkDiffEngine()
    old_chunks = [{"chunk_id": f"C-{i}", "chunk_type": "req", "clause": {"number": str(i)}, "content_hash": f"hash_{i}"} for i in range(100)]
    new_chunks = [dict(c) for c in old_chunks]
    # Modify only chunk #42
    new_chunks[42]["content_hash"] = "hash_MODIFIED_42"

    diff = engine.compare_chunk_sets(old_chunks, new_chunks)
    assert diff["unchanged_count"] == 99
    assert diff["modified_count"] == 1
    assert diff["reembed_required_count"] == 1  # 99 embeddings reused, only 1 regenerated!


def test_superseded_document_not_returned_as_current():
    """Verify TemporalEngine excludes superseded requirements when querying current status."""
    engine = TemporalEngine()
    reqs = [
        {
            "requirement_id": "REQ-001",
            "parameter": "insulation_resistance",
            "value": 4.0,
            "valid_from": "2012-08-01",
            "valid_until": "2026-06-30",
            "temporal_status": "superseded",
        },
        {
            "requirement_id": "REQ-092",
            "parameter": "insulation_resistance",
            "value": 5.0,
            "valid_from": "2026-07-01",
            "valid_until": None,
            "temporal_status": "current",
        },
    ]

    current_reqs = engine.filter_effective_requirements(reqs, query_date="2026-08-30")
    assert len(current_reqs) == 1
    assert current_reqs[0]["requirement_id"] == "REQ-092"
    assert current_reqs[0]["value"] == 5.0
