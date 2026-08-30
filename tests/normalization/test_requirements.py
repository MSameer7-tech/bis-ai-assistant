"""
Validation tests for Phase 2D Machine-Readable Requirement Statements.
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


def test_requirements_preserve_operators_values_units(doc_001):
    reqs = doc_001.get("requirements", [])
    assert len(reqs) > 0

    # 1. Insulation Resistance (>= 4 MΩ)
    req_ir = next((r for r in reqs if r.get("parameter") == "insulation_resistance"), None)
    assert req_ir is not None
    assert req_ir["operator"] == ">="
    assert req_ir["value"] == 4.0
    assert req_ir["unit"] == "MΩ"
    assert "conditions" in req_ir
    assert "test" in req_ir

    # 2. Cap Temperature Rise (<= 120 K)
    req_temp = next((r for r in reqs if r.get("parameter") == "cap_temperature_rise"), None)
    assert req_temp is not None
    assert req_temp["operator"] == "<="
    assert req_temp["value"] == 120.0
    assert req_temp["unit"] == "K"

    # 3. Sampling (25 lamps)
    req_itq = next((r for r in reqs if r.get("parameter") == "inspection_test_quantity"), None)
    assert req_itq is not None
    assert req_itq["value"] == 25
    assert req_itq["unit"] == "lamps"


def test_dual_value_representations(doc_001):
    reqs = doc_001.get("requirements", [])
    for r in reqs:
        assert "original_value" in r
        assert "normalized" in r
        assert "evidence" in r
        assert len(r["evidence"]) > 5
