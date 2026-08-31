"""
Tests for BIS Product Domain Taxonomy, Hierarchy Validation, and Golden Reference v1.
"""
import json
from pathlib import Path
import pytest
from ai.taxonomy.validator import TaxonomyValidator, get_taxonomy_validator


@pytest.fixture
def taxonomy_validator():
    return get_taxonomy_validator()


def test_taxonomy_file_structure(taxonomy_validator):
    assert taxonomy_validator.version == "1.0.0"
    domains = taxonomy_validator.get_valid_domains()
    assert "electrical" in domains
    assert "electronics_it" in domains
    assert "construction_civil" in domains
    assert "food_agriculture" in domains
    assert "mechanical_automotive" in domains
    assert "chemicals_polymers" in domains
    assert "batteries_storage" in domains


def test_taxonomy_validation_positive_cases(taxonomy_validator):
    # Electrical -> Fans -> Ceiling fans
    ok, err = taxonomy_validator.validate("electrical", "fans", "electric_ceiling_fans")
    assert ok is True
    assert err is None

    # Construction -> Cement -> 53 Grade OPC
    ok, err = taxonomy_validator.validate("construction_civil", "cement", "ordinary_portland_cement_53")
    assert ok is True
    assert err is None

    # Food -> Drinking Water -> Packaged Drinking Water
    ok, err = taxonomy_validator.validate("food_agriculture", "drinking_water", "packaged_drinking_water")
    assert ok is True
    assert err is None

    # Mechanical -> Personal Protective Equipment -> Motorcycle Helmets
    ok, err = taxonomy_validator.validate("mechanical_automotive", "personal_protective_equipment", "protective_helmets_motorcycle")
    assert ok is True
    assert err is None


def test_taxonomy_validation_negative_cases(taxonomy_validator):
    # Invalid domain
    ok, err = taxonomy_validator.validate("non_existent_domain")
    assert ok is False
    assert "Invalid domain" in err

    # Valid domain, invalid category
    ok, err = taxonomy_validator.validate("electrical", "invalid_category")
    assert ok is False
    assert "Invalid category" in err

    # Valid domain & category, invalid type
    ok, err = taxonomy_validator.validate("electrical", "fans", "invalid_fan_type")
    assert ok is False
    assert "Invalid product_type" in err


def test_golden_reference_v1_exists_and_valid():
    ref_path = Path(__file__).resolve().parent.parent / "data" / "metadata" / "golden_reference_v1.json"
    assert ref_path.exists(), "golden_reference_v1.json must exist"

    with open(ref_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["name"] == "golden_reference_v1"
    assert len(data["documents"]) >= 6
    doc_ids = [d["document_id"] for d in data["documents"]]
    assert "DOC-001" in doc_ids
    assert "DOC-002" in doc_ids
    assert "DOC-007" in doc_ids
    assert "DOC-012" in doc_ids
    assert data["total_pilot_chunks"] == 378
