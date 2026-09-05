"""
Deterministic unit test suite for Phase 4 Batch E:
Hallmarking (AHC Network, HUID, Purity Grades) and Consumer Services (BIS Care, Grievance Redressal, KYS/KYL).
"""
import pytest
from ai.acquisition.hallmarking.registry import HallmarkRegistry
from ai.acquisition.hallmarking.models import AHCStatus, MetalType
from ai.acquisition.consumer.registry import ConsumerRegistry
from ai.acquisition.consumer.models import ConsumerServiceCategory, ServiceChannel


@pytest.fixture(scope="module")
def hallmark_registry():
    return HallmarkRegistry()


@pytest.fixture(scope="module")
def consumer_registry():
    return ConsumerRegistry()


# ==============================================================================
# 1. Hallmarking Network & Purity Invariants
# ==============================================================================

def test_hallmarking_registry_count(hallmark_registry):
    """Verifies that 55 Assaying & Hallmarking Centres are indexed."""
    assert hallmark_registry.count() == 55


def test_huid_format_validation(hallmark_registry):
    """Verifies 6-digit alphanumeric HUID format validation rules."""
    # Valid 6-character uppercase alphanumeric codes
    assert hallmark_registry.validate_huid("ABC123") is True
    assert hallmark_registry.validate_huid("7K9M2P") is True
    assert hallmark_registry.validate_huid("ZZ99AA") is True
    assert hallmark_registry.validate_huid("123456") is True
    assert hallmark_registry.validate_huid("ABCDEF") is True

    # Invalid codes (length, special characters, empty)
    assert hallmark_registry.validate_huid("ABC12") is False       # 5 chars
    assert hallmark_registry.validate_huid("ABC1234") is False     # 7 chars
    assert hallmark_registry.validate_huid("AB-123") is False      # special char
    assert hallmark_registry.validate_huid("") is False            # empty
    assert hallmark_registry.validate_huid(None) is False          # None


def test_gold_purity_fineness_standards(hallmark_registry):
    """Verifies statutory gold purity grades under IS 1417 : 2016."""
    g24 = hallmark_registry.get_gold_purity_by_karat("24K")
    assert g24 is not None
    assert g24.fineness_ppt == 999

    g22 = hallmark_registry.get_gold_purity_by_karat("22K")
    assert g22 is not None
    assert g22.fineness_ppt == 916

    g18 = hallmark_registry.get_gold_purity_by_karat("18K")
    assert g18 is not None
    assert g18.fineness_ppt == 750

    g14 = hallmark_registry.get_gold_purity_by_karat("14K")
    assert g14 is not None
    assert g14.fineness_ppt == 585

    # Reverse lookup by fineness
    assert hallmark_registry.get_gold_purity_by_fineness(916).karat == "22K"
    assert hallmark_registry.get_gold_purity_by_fineness(750).karat == "18K"


def test_silver_purity_grades(hallmark_registry):
    """Verifies silver purity grades under IS 2112 : 2014."""
    silver_grades = hallmark_registry.silver_purity_grades
    assert len(silver_grades) >= 5
    fineness_values = {g["fineness_ppt"] for g in silver_grades}
    assert 999 in fineness_values
    assert 925 in fineness_values  # Sterling silver
    assert 900 in fineness_values


def test_zaveri_bazaar_ahc(hallmark_registry):
    """Verifies AHC-001 in Mumbai Zaveri Bazaar."""
    zaveri = hallmark_registry.get_by_ahc_id("AHC-001")
    assert zaveri is not None
    assert "Zaveri Bazaar" in zaveri.ahc_name
    assert zaveri.city == "Mumbai"
    assert zaveri.status == AHCStatus.ACTIVE
    assert "IS 1417" in zaveri.standards_covered
    assert zaveri.huid_supported is True
    assert zaveri.daily_capacity_pieces >= 2000


def test_geographic_ahc_clustering(hallmark_registry):
    """Verifies AHC presence across major jewellery hubs."""
    delhi_ahcs = hallmark_registry.get_ahcs_by_city("New Delhi")
    assert len(delhi_ahcs) >= 1
    assert any("Karol Bagh" in a.ahc_name for a in delhi_ahcs)

    chennai_ahcs = hallmark_registry.get_ahcs_by_city("Chennai")
    assert len(chennai_ahcs) >= 1
    assert any("T. Nagar" in a.ahc_name for a in chennai_ahcs)

    kolkata_ahcs = hallmark_registry.get_ahcs_by_city("Kolkata")
    assert len(kolkata_ahcs) >= 1
    assert any("Bowbazar" in a.ahc_name for a in kolkata_ahcs)


# ==============================================================================
# 2. Consumer Services & Grievance Redressal
# ==============================================================================

def test_consumer_registry_count(consumer_registry):
    """Verifies that 34 consumer services and workflows are indexed."""
    assert consumer_registry.count() == 34


def test_bis_care_verify_isi_cml(consumer_registry):
    """Verifies CONS-001 for BIS Care CM/L Licence Verification."""
    svc = consumer_registry.get_by_id("CONS-001")
    assert svc is not None
    assert svc.channel == ServiceChannel.BIS_CARE_APP
    assert svc.target_mark == "ISI_MARK"
    assert any("CM/L" in p for p in svc.input_parameters)
    assert svc.resolution_tat_days == 15
    assert any("Section 29" in p for p in svc.statutory_provisions)


def test_bis_care_verify_huid(consumer_registry):
    """Verifies CONS-002 for BIS Care Gold / Silver HUID Verification."""
    svc = consumer_registry.get_by_id("CONS-002")
    assert svc is not None
    assert svc.target_mark == "HUID_HALLMARK"
    assert any("HUID" in p for p in svc.input_parameters)
    assert "Section 14 (Hallmarking of precious metals)" in svc.statutory_provisions
    assert any("2 times" in c or "2x" in c for c in svc.consumer_rights + [svc.penalty_clause or ""])


def test_bis_care_verify_crs_r_number(consumer_registry):
    """Verifies CONS-003 for BIS Care CRS R-Number Verification."""
    svc = consumer_registry.get_by_id("CONS-003")
    assert svc is not None
    assert svc.target_mark == "CRS_REGISTRATION"
    assert any("R-XXXXXXXX" in p or "Registration Number" in p for p in svc.input_parameters)


def test_bis_care_quality_complaint_redressal(consumer_registry):
    """Verifies CONS-004 for direct mobile consumer quality complaints."""
    svc = consumer_registry.get_by_id("CONS-004")
    assert svc is not None
    assert svc.category == ConsumerServiceCategory.COMPLAINT_REDRESSAL
    assert svc.resolution_tat_days == 30
    assert any("Photo" in p for p in svc.input_parameters)
    assert any("Section 31" in p for p in svc.statutory_provisions)


def test_know_your_standard_kys(consumer_registry):
    """Verifies CONS-005 for Know Your Standard (KYS) public access."""
    svc = consumer_registry.get_by_id("CONS-005")
    assert svc is not None
    assert svc.category == ConsumerServiceCategory.STANDARDS_ACCESS
    assert svc.channel == ServiceChannel.MANAKONLINE_PORTAL


def test_consumer_compensation_under_section_31(consumer_registry):
    """Verifies CONS-007 for statutory consumer compensation claims."""
    svc = consumer_registry.get_by_id("CONS-007")
    assert svc is not None
    assert svc.category == ConsumerServiceCategory.COMPENSATION_CLAIM
    assert "Section 31 (Compensation for non-conforming goods)" in svc.statutory_provisions
    assert any("refund" in r.lower() or "replacement" in r.lower() for r in svc.consumer_rights)


# ==============================================================================
# 3. Cross-Domain Identification & Penalty Invariants
# ==============================================================================

def test_identification_code_isolation(hallmark_registry, consumer_registry):
    """
    Enforces distinct identification code formats across BIS schemes:
    - ISI Mark: CM/L-XXXXXXX (7 digits)
    - CRS: R-XXXXXXXX (8 digits)
    - Hallmarking: XXXXXX (6 alphanumeric chars)
    """
    assert hallmark_registry.validate_huid("CM/L-8100123") is False
    assert hallmark_registry.validate_huid("R-41001234") is False
    assert hallmark_registry.validate_huid("7K9M2P") is True
