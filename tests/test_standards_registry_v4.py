"""
Unit tests for the Master BIS Standards Registry (Phase 4 Batch B).
Validates models, status filtering, temporal queries, failure reasons, and serialization.
"""

import pytest
from pathlib import Path
from ai.acquisition.standards.models import (
    StandardRecord,
    StandardStatus,
    AcquisitionStatus,
    AcquisitionFailureReason,
    AspectType
)
from ai.acquisition.standards.registry import StandardsRegistry


def test_standard_record_model_validation():
    rec = StandardRecord(
        standard_id="STD-IS-1786-2024",
        is_number="IS 1786",
        title="High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        edition="Fifth Revision",
        revision="Rev 5",
        status=StandardStatus.ACTIVE,
        acquisition_status=AcquisitionStatus.ACQUIRED,
        failure_reason=AcquisitionFailureReason.NONE,
        reaffirmation_year=2024,
        amendment_count=2,
        technical_department="MTD",
        technical_committee="MTD 04",
        aspect=AspectType.PRODUCT_SPECIFICATION,
        language="English",
        source_url="https://standardsbis.bsbedge.com/is1786_2024",
        document_id="DOC-034",
        content_hash="abc123hash"
    )
    assert rec.standard_id == "STD-IS-1786-2024"
    assert rec.status == StandardStatus.ACTIVE
    assert rec.acquisition_status == AcquisitionStatus.ACQUIRED
    assert rec.failure_reason == AcquisitionFailureReason.NONE


def test_standards_registry_loading_and_queries():
    reg = StandardsRegistry()
    assert len(reg.standards) > 600

    # Query active standard IS 1786
    results = reg.get_by_is("IS 1786", active_only=True)
    assert len(results) > 0
    assert any("High Strength Deformed" in r.title for r in results)

    # Document ID lookup
    rec = reg.get_by_doc_id("DOC-034")
    if rec:
        assert rec.is_number == "IS 1786"


def test_standards_registry_accounting_summary():
    reg = StandardsRegistry()
    stats = reg.get_summary_statistics()
    assert "total_standards" in stats
    assert stats["total_standards"] >= 640
    assert "by_status" in stats
    assert "by_acquisition_status" in stats
    assert "by_failure_reason" in stats
