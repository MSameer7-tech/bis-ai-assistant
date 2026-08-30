"""
Validation tests for the Incremental Update Pipeline (Steps 11 & 12).
"""

from pathlib import Path
import pytest
from ai.ingestion.status import DocumentStatus
from ai.ingestion.update_pipeline import IncrementalUpdatePipeline

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PDF = ROOT_DIR / "data" / "raw" / "standards" / "IS_16102_Part_1_2012.pdf"


def test_update_pipeline_unchanged_detection():
    """Verify that update pipeline skips re-embedding when document hash is identical."""
    pipeline = IncrementalUpdatePipeline()
    res = pipeline.process_updated_document(
        document_id="DOC-001",
        new_pdf_path=SAMPLE_PDF,
        force=False,
    )

    assert res["status"] == DocumentStatus.UNCHANGED.value
    assert res["reembed_required_count"] == 0


def test_update_pipeline_forced_run_executes_phases():
    """Verify that forced update pipeline runs 2C -> 2D -> 2E and yields chunk diff."""
    pipeline = IncrementalUpdatePipeline()
    res = pipeline.process_updated_document(
        document_id="DOC-001",
        new_pdf_path=SAMPLE_PDF,
        force=True,
    )

    assert res["status"] == DocumentStatus.CHUNKED.value
    assert res["total_chunks"] == 129
    assert res["ready_for_vector_db"] is True
    assert "chunk_diff" in res
    assert "semantic_diff" in res
