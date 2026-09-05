"""
Unit tests for the Master BIS Amendments and Gazette Registries (Phase 4 Batch B).
Validates schema validation, standard linkages, statutory gazette references, and query lookups.
"""

import pytest
from pathlib import Path
from ai.acquisition.amendments.models import AmendmentRecord
from ai.acquisition.amendments.registry import AmendmentsRegistry
from ai.acquisition.gazette.models import GazetteRecord
from ai.acquisition.gazette.registry import GazetteRegistry


def test_amendments_registry():
    reg = AmendmentsRegistry()
    assert len(reg.amendments) >= 200

    # Test lookup by standard
    amds = reg.get_by_standard("IS 1786")
    assert len(amds) > 0
    assert amds[0].is_number == "IS 1786"
    assert amds[0].amendment_number >= 1


def test_gazette_registry():
    reg = GazetteRegistry()
    assert len(reg.notifications) == 45

    # Test lookup of mandatory steel QCO gazette
    gz = reg.get_by_id("GAZ-2024-STEEL-QCO-01")
    assert gz is not None
    assert gz.is_mandatory_qco is True
    assert "IS 1786" in gz.related_standards

    # Test lookup by standard
    steel_gzs = reg.get_by_standard("IS 1786")
    assert len(steel_gzs) > 0
    assert steel_gzs[0].ministry == "Ministry of Steel"
