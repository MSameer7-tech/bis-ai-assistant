"""
Validation tests for Data Freshness, Document Versioning, and Semantic Diff (Steps 1-5).
"""

import json
from pathlib import Path
import pytest
from ai.ingestion.change_detector import ChangeDetector, compute_sha256
from ai.ingestion.semantic_diff import SemanticDiffEngine
from ai.ingestion.versioning import DocumentVersion, make_version_id

ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"
DOC_012_PATH = ROOT_DIR / "data" / "normalized" / "DOC-012.json"


def test_step1_source_registry_has_current_version_and_history():
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


def test_step2_sha256_change_detector_identifies_identical_document():
    """Verify that ChangeDetector reports has_changed=False for existing untouched files (Step 2)."""
    detector = ChangeDetector()
    report = detector.check_document_change("DOC-001", update_history=False)

    assert report["has_changed"] is False
    assert report["change_type"] == "identical"
    assert report["action_required"] == "none"
    assert report["current_hash"] == report["previous_hash"]


def test_step3_http_metadata_etag_and_last_modified():
    """Verify fast pre-check with HTTP ETag and Last-Modified (Step 3)."""
    detector = ChangeDetector()
    # When headers match
    rep_match = detector.check_http_metadata("DOC-001", last_modified="2026-08-30T14:47:43.081517+00:00")
    assert rep_match["can_skip_download"] is True

    # When headers differ
    rep_diff = detector.check_http_metadata("DOC-001", last_modified="2026-09-01T00:00:00Z")
    assert rep_diff["can_skip_download"] is False


def test_step4_document_version_id_generation():
    """Verify standardized version ID generation: DOC-001-v001 (Step 4)."""
    v_id = make_version_id("DOC-001", 2)
    assert v_id == "DOC-001-v002"

    v_obj = DocumentVersion(
        version_id="DOC-001-v001",
        document_id="DOC-001",
        version_number=1,
        version_label="IS 16102 (Part 1) : 2012",
        sha256="5f458e6ed584317d97e0335c829bba2827831f1595566e44231cd125dfc7c02b",
        local_path="data/raw/standards/IS_16102_Part_1_2012.pdf",
    )
    assert v_obj.version_id == "DOC-001-v001"
    assert v_obj.status == "active"


def test_step5_semantic_diff_engine():
    """Verify that SemanticDiffEngine computes structured requirement and definition differences (Step 5)."""
    diff_engine = SemanticDiffEngine()

    old_doc = {
        "document_id": "DOC-001-v001",
        "requirements": [
            {
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 4.0,
                "unit": "MΩ",
                "status": "mandatory",
            },
            {
                "parameter": "cap_temperature_rise",
                "clause": "10",
                "operator": "<=",
                "value": 120.0,
                "unit": "K",
                "status": "mandatory",
            },
        ],
        "definitions": [
            {"term": "Self-Ballasted LED Lamp", "definition": "Unit which cannot be dismantled..."}
        ],
        "tables": [],
        "cross_references": [],
    }

    new_doc = {
        "document_id": "DOC-001-v002",
        "requirements": [
            {
                "parameter": "insulation_resistance",
                "clause": "8.1.1",
                "operator": ">=",
                "value": 5.0,  # Modified limit!
                "unit": "MΩ",
                "status": "mandatory",
            },
            {
                "parameter": "glow_wire_temperature",  # Added!
                "clause": "12.1",
                "operator": ">=",
                "value": 650.0,
                "unit": "°C",
                "status": "mandatory",
            },
        ],
        "definitions": [
            {"term": "Self-Ballasted LED Lamp", "definition": "Unit which cannot be dismantled..."},
            {"term": "LED Module", "definition": "Light source containing LED elements..."}  # Added!
        ],
        "tables": [],
        "cross_references": [],
    }

    diff = diff_engine.compare_documents(old_doc, new_doc)

    assert diff["has_semantic_changes"] is True
    # Check modified requirement
    assert diff["requirements_diff"]["modified_count"] == 1
    mod_req = diff["requirements_diff"]["modified"][0]
    assert mod_req["parameter"] == "insulation_resistance"
    assert mod_req["old_value"] == 4.0
    assert mod_req["new_value"] == 5.0

    # Check added and removed
    assert diff["requirements_diff"]["added_count"] == 1
    assert diff["requirements_diff"]["removed_count"] == 1

    # Check definitions
    assert diff["definitions_diff"]["added_count"] == 1
