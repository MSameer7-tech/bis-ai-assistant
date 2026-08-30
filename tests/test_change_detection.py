"""
Validation tests for Data Freshness and Change Detection Gate (Step 1).
"""

import json
from pathlib import Path
import pytest
from ai.ingestion.change_detector import ChangeDetector, compute_sha256

ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
SAMPLE_PDF = ROOT_DIR / "data" / "raw" / "standards" / "IS_16102_Part_1_2012.pdf"


def test_source_registry_has_current_version_and_history():
    """Verify that every entry in source_registry.json contains structured current_version and history."""
    assert REGISTRY_PATH.exists()
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    assert len(registry) >= 6
    for item in registry:
        assert "current_version" in item
        cur_ver = item["current_version"]
        assert "sha256" in cur_ver
        assert "last_modified" in cur_ver
        assert "history" in item
        assert len(item["history"]) >= 1
        assert "detected_at" in item["history"][0]


def test_change_detector_identifies_identical_document():
    """Verify that ChangeDetector reports has_changed=False for existing untouched files."""
    detector = ChangeDetector()
    report = detector.check_document_change("DOC-001", update_history=False)

    assert report["has_changed"] is False
    assert report["change_type"] == "identical"
    assert report["action_required"] == "none"
    assert report["current_hash"] == report["previous_hash"]


def test_change_detector_scan_all_sources():
    """Verify that scan_all_sources scans all acquired pilot documents and reports 0 missing."""
    detector = ChangeDetector()
    summary = detector.scan_all_sources()

    assert summary["scanned_count"] >= 6
    assert summary["unchanged_count"] >= 6
    assert summary["missing_count"] == 0
    assert summary["changed_count"] == 0
