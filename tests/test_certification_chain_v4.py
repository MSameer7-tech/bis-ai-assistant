"""
Phase 4 Batch C: Certification, QCO, Product Manual, SIT, Scheme and Procedure Unit Tests.
Tests deterministic certification logic, QCO exemptions, SIT testing schedules, scheme distinctness,
and end-to-end evidence chain integrity.
"""

import pytest
from ai.acquisition.qco.registry import QCORegistry
from ai.acquisition.qco.models import QCOStatus, MandatoryStatus
from ai.acquisition.manuals.registry import ProductManualRegistry
from ai.acquisition.sit.registry import SITRegistry
from ai.acquisition.tests.registry import TestRegistry
from ai.acquisition.schemes.registry import SchemeRegistry
from ai.acquisition.procedures.registry import ProcedureRegistry
from ai.acquisition.products.builder import ProductRegistryBuilder


@pytest.fixture
def qco_registry():
    return QCORegistry()


@pytest.fixture
def manuals_registry():
    return ProductManualRegistry()


@pytest.fixture
def sit_registry():
    return SITRegistry()


@pytest.fixture
def tests_registry():
    return TestRegistry()


@pytest.fixture
def schemes_registry():
    return SchemeRegistry()


@pytest.fixture
def procedures_registry():
    return ProcedureRegistry()


# ---------------------------------------------------------------------------
# Invariant: IS exists != mandatory BIS certification
# ---------------------------------------------------------------------------
def test_mandatory_vs_voluntary_distinction(qco_registry):
    """Verifies that an Indian Standard does not automatically become mandatory without explicit QCO."""
    # Mandatory standards under active statutory QCOs
    assert qco_registry.is_mandatory("IS 1786") is True
    assert qco_registry.is_mandatory("IS 269") is True
    assert qco_registry.is_mandatory("IS 374") is True
    assert qco_registry.is_mandatory("IS 14543") is True
    assert qco_registry.is_mandatory("IS 16046 (PART 1)") is True
    assert qco_registry.is_mandatory("IS 1417") is True

    # Voluntary standards without statutory QCO
    assert qco_registry.is_mandatory("IS 1079") is False
    assert qco_registry.is_mandatory("IS 15477") is False
    assert qco_registry.is_mandatory("IS 544") is False


# ---------------------------------------------------------------------------
# QCO Statutory Tracking & Exemption Preservation
# ---------------------------------------------------------------------------
def test_qco_exemptions_and_effective_dates(qco_registry):
    """Verifies QCOs preserve statutory exemptions, ministries, and effective dates."""
    steel_qcos = qco_registry.get_by_standard("IS 1786")
    assert len(steel_qcos) > 0
    qco = steel_qcos[0]
    assert qco.issuing_authority == "Ministry of Steel"
    assert qco.mandatory_status == MandatoryStatus.MANDATORY_QCO
    assert qco.status == QCOStatus.ACTIVE
    assert any("export" in ex.lower() for ex in qco.exemptions)
    assert any("r&d" in ex.lower() for ex in qco.exemptions)


def test_gold_hallmarking_order(qco_registry):
    """Verifies Gold Hallmarking statutory order rules and exemptions."""
    gold_qcos = qco_registry.get_by_standard("IS 1417")
    assert len(gold_qcos) > 0
    qco = gold_qcos[0]
    assert qco.mandatory_status == MandatoryStatus.MANDATORY_HALLMARKING
    assert qco.scheme == "HALLMARKING"
    assert any("40 lakh" in ex for ex in qco.exemptions)


# ---------------------------------------------------------------------------
# Product Manual & Grouping Guidelines
# ---------------------------------------------------------------------------
def test_product_manual_registry(manuals_registry):
    """Verifies Product Manuals link to correct standards and retain grouping/sampling rules."""
    fan_manuals = manuals_registry.get_by_standard("IS 374")
    assert len(fan_manuals) > 0
    pm = fan_manuals[0]
    assert "Ceiling" in pm.scope
    assert pm.sit_reference == "SIT-IS-374-2019"
    assert "3 complete fan sets" in pm.sampling_requirements
    assert "ISI" in pm.marking_requirements
    assert "Air delivery" in pm.tests[0]


def test_tmt_steel_product_manual(manuals_registry):
    """Verifies TMT steel product manual requirements and UTM equipment."""
    steel_manuals = manuals_registry.get_by_standard("IS 1786")
    assert len(steel_manuals) > 0
    pm = steel_manuals[0]
    assert "High Strength Deformed Steel" in pm.scope
    assert any("Universal Testing Machine" in eq for eq in pm.test_equipment)
    assert any("Proof stress" in t for t in pm.tests)


# ---------------------------------------------------------------------------
# SIT Requirements & Numerical Limits
# ---------------------------------------------------------------------------
def test_sit_testing_schedules(sit_registry):
    """Verifies SIT captures exact test frequencies, sample sizes, and requirements."""
    fan_sits = sit_registry.get_by_standard("IS 374")
    assert len(fan_sits) > 0
    sit = fan_sits[0]
    assert "Air Delivery" in sit.test_name
    assert "210 m3/min" in sit.requirement
    assert "500 fans" in sit.frequency
    assert "3 complete fan sets" in sit.sample_size
    assert "DOC-SIT-IS-374" in sit.document_id


def test_cement_sit_requirements(sit_registry):
    """Verifies OPC cement compressive strength SIT requirements."""
    cement_sits = sit_registry.get_by_standard("IS 269")
    assert len(cement_sits) > 0
    sit = cement_sits[0]
    assert "53.0 MPa" in sit.requirement
    assert "6 standard mortar cubes" in sit.sample_size
    assert "500 tonnes" in sit.frequency


# ---------------------------------------------------------------------------
# Normalized Discrete Tests
# ---------------------------------------------------------------------------
def test_discrete_tests_registry(tests_registry):
    """Verifies discrete test entities retain physical units, clauses, and methods."""
    fan_tests = tests_registry.get_by_standard("IS 374")
    assert len(fan_tests) >= 2
    air_test = next(t for t in fan_tests if "Air Delivery" in t.test_name)
    assert air_test.unit == "m3/min"
    assert "Clause 10.4" in air_test.test_method

    steel_tests = tests_registry.get_by_standard("IS 1786")
    yield_test = next(t for t in steel_tests if "Proof Stress" in t.test_name)
    assert yield_test.unit == "N/mm2"
    assert "500.0" in yield_test.requirement


# ---------------------------------------------------------------------------
# Conformity Assessment Schemes Distinctness
# ---------------------------------------------------------------------------
def test_scheme_distinctness(schemes_registry):
    """Verifies that Scheme I, Scheme II (CRS), FMCS, and Hallmarking remain distinct."""
    scheme_i = schemes_registry.get_by_id("SCHEME-I")
    assert scheme_i is not None
    assert "ISI Mark" in scheme_i.scheme_name
    assert "Factory audit" in scheme_i.certification_path

    scheme_ii = schemes_registry.get_by_id("SCHEME-II")
    assert scheme_ii is not None
    assert "Compulsory Registration" in scheme_ii.scheme_name
    assert "Self-declaration" in scheme_ii.certification_path

    fmcs = schemes_registry.get_by_id("FMCS")
    assert fmcs is not None
    assert "Foreign Manufacturers" in fmcs.scheme_name
    assert "Overseas physical factory audit" in fmcs.certification_path

    hallmarking = schemes_registry.get_by_id("HALLMARKING")
    assert hallmarking is not None
    assert "HUID" in hallmarking.marking_requirements


# ---------------------------------------------------------------------------
# Certification Procedures & SLA Timelines
# ---------------------------------------------------------------------------
def test_certification_procedures(procedures_registry):
    """Verifies certification lifecycle procedures, required documents, and SLA timelines."""
    normal_grant = procedures_registry.get_by_id("PROC-SCHEME-I-NORMAL-GRANT")
    assert normal_grant is not None
    assert "Normal Procedure" in normal_grant.title
    assert "90 to 120 days" in normal_grant.timelines_days
    assert any("machinery" in d.lower() for d in normal_grant.required_documents)

    simplified_grant = procedures_registry.get_by_id("PROC-SCHEME-I-SIMPLIFIED-GRANT")
    assert simplified_grant is not None
    assert "30 working days" in simplified_grant.timelines_days

    crs_reg = procedures_registry.get_by_id("PROC-SCHEME-II-CRS-REGISTRATION")
    assert crs_reg is not None
    assert crs_reg.scheme_id == "SCHEME-II"
    assert "20 working days" in crs_reg.timelines_days


# ---------------------------------------------------------------------------
# Cross-Domain Boundary Protection
# ---------------------------------------------------------------------------
def test_cross_domain_boundary_protection(qco_registry, manuals_registry):
    """Verifies that products from one domain do not inherit rules from another domain."""
    # Fans (Electrical) must not be linked to Steel or Cement QCOs
    fan_qcos = qco_registry.get_by_standard("IS 374")
    assert all("Steel" not in q.title and "Cement" not in q.title for q in fan_qcos)

    # Steel TMT must not be linked to Electrical Appliance manual
    steel_manuals = manuals_registry.get_by_standard("IS 1786")
    assert all("Fan" not in m.scope and "Heater" not in m.scope for m in steel_manuals)
