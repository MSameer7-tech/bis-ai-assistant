"""
Validation tests for Amendment Processing and Temporal Validity (Steps 13 & 14).
"""

import json
from pathlib import Path
import pytest
from ai.versioning.amendment_processor import AmendmentProcessor
from ai.versioning.temporal_engine import TemporalEngine

ROOT_DIR = Path(__file__).resolve().parent.parent
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"
DOC_012_PATH = ROOT_DIR / "data" / "normalized" / "DOC-012.json"


def test_step13_and_14_amendment_consolidation_and_temporal_windows():
    """Verify that AmendmentProcessor consolidates base standard and tracks superseded requirements."""
    assert DOC_001_PATH.exists()
    assert DOC_012_PATH.exists()

    with open(DOC_001_PATH, "r", encoding="utf-8") as f:
        base_doc = json.load(f)
    with open(DOC_012_PATH, "r", encoding="utf-8") as f:
        amd_doc = json.load(f)

    processor = AmendmentProcessor()
    effective_date = "2026-07-01"

    consolidated = processor.apply_amendment_to_base(
        base_norm_doc=base_doc,
        amendment_norm_doc=amd_doc,
        effective_date=effective_date,
        amendment_label="Amendment No. 1",
    )

    summary = consolidated["consolidation_summary"]
    assert summary["base_document_id"] == "DOC-001"
    assert summary["effective_date"] == effective_date
    assert summary["total_active_requirements"] > 0
    assert summary["total_superseded_requirements"] >= 2

    # Verify superseded requirements have valid_until set
    superseded = [r for r in consolidated["requirements"] if r.get("temporal_status") == "superseded"]
    for s in superseded:
        assert s["valid_until"] == effective_date
        assert s["superseded_by"] is not None

    # Verify temporal engine queries
    engine = TemporalEngine()

    # Query in 2015 -> should return base requirements, none with valid_from in 2026
    reqs_2015 = engine.filter_effective_requirements(consolidated["requirements"], query_date="2015-01-01")
    for r in reqs_2015:
        assert r["valid_from"] <= "2015-01-01"

    # Query in 2026 -> should return new active requirements and exclude superseded ones
    reqs_2026 = engine.filter_effective_requirements(consolidated["requirements"], query_date="2026-08-01")
    active_ids = {r["requirement_id"] for r in reqs_2026}
    for s in superseded:
        assert s["requirement_id"] not in active_ids
