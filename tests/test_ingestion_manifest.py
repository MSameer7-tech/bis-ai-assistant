"""
Validation tests for Ingestion Manifest and Document Status Lifecycle (Steps 9 & 10).
"""

import json
from pathlib import Path
import pytest
from ai.ingestion.manifest import IngestionManifestManager
from ai.ingestion.status import DocumentStatus

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "data" / "metadata" / "ingestion_manifest.json"


def test_step9_document_status_enum_values():
    """Verify standard document lifecycle statuses exist."""
    assert DocumentStatus.DISCOVERED.value == "DISCOVERED"
    assert DocumentStatus.DOWNLOADED.value == "DOWNLOADED"
    assert DocumentStatus.UNCHANGED.value == "UNCHANGED"
    assert DocumentStatus.CHANGED.value == "CHANGED"
    assert DocumentStatus.CHUNKED.value == "CHUNKED"
    assert DocumentStatus.INDEXED.value == "INDEXED"


def test_step10_ingestion_manifest_structure_and_coverage():
    """Verify that ingestion_manifest.json tracks all 6 documents with valid statuses and chunk counts."""
    manager = IngestionManifestManager()
    manifest = manager.generate_manifest()

    assert MANIFEST_PATH.exists()
    assert manifest["total_documents"] >= 6
    assert "last_run" in manifest
    assert "documents" in manifest

    doc_001 = manifest["documents"]["DOC-001"]
    assert doc_001["source_id"] == "SRC-001"
    assert doc_001["status"] == DocumentStatus.CHUNKED.value
    assert doc_001["total_chunks"] == 129
    assert doc_001["requires_reindex"] is False
