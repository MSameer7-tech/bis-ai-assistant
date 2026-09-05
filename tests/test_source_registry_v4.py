"""
Unit Tests for Phase 4 Batch A: BIS Source Registry & Coverage Matrix Management.
"""

import os
import pytest
from pathlib import Path
from ai.acquisition.source_registry import (
    SourceRegistry,
    SourceRecord,
    SourcePriority,
    SourceStatus,
    UpdateStrategy,
    SOURCES_REGISTRY_PATH
)


@pytest.fixture
def source_registry():
    return SourceRegistry(registry_path=SOURCES_REGISTRY_PATH)


def test_sources_jsonl_exists_and_loads(source_registry):
    """Test that data/registry/sources.jsonl exists and contains at least 18 source families."""
    sources = source_registry.list_sources()
    assert len(sources) >= 18, f"Expected at least 18 sources, got {len(sources)}"
    
    source_ids = {s.source_id for s in sources}
    expected_ids = {
        "BIS-KYS",
        "BIS-STANDARDS",
        "BIS-AMENDMENTS",
        "BIS-GAZETTE",
        "BIS-QCO",
        "BIS-PRODUCT-MANUALS",
        "BIS-SIT",
        "BIS-GROUPING",
        "BIS-LABS",
        "BIS-LICENCES",
        "BIS-CRS",
        "BIS-HALLMARKING",
        "BIS-SCHEMES",
        "BIS-PROCEDURES",
        "BIS-CONSUMER",
        "BIS-OFFICES",
        "BIS-TRAINING",
        "BIS-SIMPLIFIED"
    }
    assert expected_ids.issubset(source_ids), f"Missing source IDs: {expected_ids - source_ids}"


def test_source_provenance_and_urls(source_registry):
    """Test that every source has a valid official government/BIS URL and authority."""
    sources = source_registry.list_sources()
    for s in sources:
        assert s.base_url.startswith("http://") or s.base_url.startswith("https://")
        assert len(s.authority.strip()) > 0
        assert len(s.name.strip()) > 0
        assert len(s.description.strip()) > 0
        assert s.priority in list(SourcePriority)
        assert s.update_strategy in list(UpdateStrategy)


def test_source_coverage_matrix_monotonicity(source_registry):
    """Test that coverage metrics satisfy standard pipeline monotonicity (discovered >= acquired >= indexed)."""
    sources = source_registry.list_sources()
    for s in sources:
        cov = s.coverage
        assert cov.discovered >= 0
        assert cov.accessible >= 0
        assert cov.acquired >= 0
        assert cov.parsed >= 0
        assert cov.normalized >= 0
        assert cov.indexed >= 0
        assert cov.acquired <= cov.discovered or cov.discovered == 0
        assert cov.indexed <= cov.acquired or cov.acquired == 0


def test_source_filtering(source_registry):
    """Test querying sources by family and enabled status."""
    kys_sources = source_registry.list_sources(family="know_your_standard")
    assert len(kys_sources) == 1
    assert kys_sources[0].source_id == "BIS-KYS"

    enabled_sources = source_registry.list_sources(enabled_only=True)
    assert len(enabled_sources) >= 18


def test_update_coverage_metrics(tmp_path):
    """Test updating live coverage metrics for a source."""
    temp_jsonl = tmp_path / "sources.jsonl"
    reg = SourceRegistry(registry_path=temp_jsonl)
    
    test_rec = SourceRecord(
        source_id="BIS-TEST",
        source_family="testing",
        name="Test Source",
        authority="BIS Test Authority",
        source_type="test_portal",
        base_url="https://test.bis.gov.in",
        discovery_method="test_crawler",
        priority=SourcePriority.TIER_1A,
        description="Test description for unit testing"
    )
    reg.register_source(test_rec)
    
    # Update coverage
    updated = reg.update_coverage(
        source_id="BIS-TEST",
        discovered=500,
        accessible=450,
        acquired=400,
        parsed=390,
        normalized=380,
        indexed=375,
        status=SourceStatus.ACTIVE
    )
    assert updated.coverage.discovered == 500
    assert updated.coverage.indexed == 375
    assert updated.coverage.last_checked is not None
    assert updated.coverage.last_success is not None

    # Reload from disk
    reg2 = SourceRegistry(registry_path=temp_jsonl)
    loaded = reg2.get_source("BIS-TEST")
    assert loaded is not None
    assert loaded.coverage.discovered == 500
    assert loaded.coverage.indexed == 375


def test_generate_coverage_matrix_table(source_registry):
    """Test markdown coverage matrix table generation."""
    table_md = source_registry.generate_coverage_matrix_table()
    assert "| Source ID" in table_md
    assert "| BIS-KYS" in table_md
    assert "| BIS-STANDARDS" in table_md
    assert "| BIS-QCO" in table_md
    assert "| BIS-LABS" in table_md
