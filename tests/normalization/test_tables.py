"""
Validation tests for Phase 2D Table Normalization.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOC_001_PATH = ROOT_DIR / "data" / "normalized" / "DOC-001.json"


@pytest.fixture(scope="module")
def doc_001():
    assert DOC_001_PATH.exists()
    with open(DOC_001_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_table_2_and_3_normalized(doc_001):
    tables = doc_001.get("tables", [])
    assert len(tables) >= 2

    # Table 3 Torque
    t3 = next((t for t in tables if t["table_id"] == "TABLE-003"), None)
    assert t3 is not None
    assert t3["clause"] == "9.1"
    assert len(t3["rows"]) >= 8

    # Check B22d torque
    r_b22 = next((r for r in t3["rows"] if r["cap"] == "B22d"), None)
    assert r_b22["torsion_moment"]["value"] == 3.0
    assert r_b22["torsion_moment"]["unit"] == "Nm"

    # Check GX53 status
    r_gx53 = next((r for r in t3["rows"] if r["cap"] == "GX53"), None)
    assert r_gx53["status"] == "under_consideration"
