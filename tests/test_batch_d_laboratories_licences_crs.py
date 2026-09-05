"""
Deterministic unit test suite for Phase 4 Batch D:
Laboratories, CM/L Manufacturer Licences, and CRS Electronics Registrations.
"""
import pytest
from ai.acquisition.laboratories.registry import LaboratoryRegistry
from ai.acquisition.laboratories.models import LabType, LabStatus
from ai.acquisition.licences.registry import LicenceRegistry
from ai.acquisition.licences.models import LicenceStatus
from ai.acquisition.crs.registry import CRSRegistry
from ai.acquisition.crs.models import CRSStatus


@pytest.fixture(scope="module")
def lab_registry():
    return LaboratoryRegistry()


@pytest.fixture(scope="module")
def licence_registry():
    return LicenceRegistry()


@pytest.fixture(scope="module")
def crs_registry():
    return CRSRegistry()


# ==============================================================================
# 1. Laboratory Network & Capability Verification
# ==============================================================================

def test_laboratory_discovery_universe_count(lab_registry):
    """Verifies that the complete 840-node laboratory universe is indexed."""
    assert lab_registry.count() == 840
    assert lab_registry.count_evidence_backed() >= 20


def test_bis_central_and_regional_laboratories(lab_registry):
    """Verifies BIS owned Central (CL Sahibabad) and Regional laboratories."""
    cl = lab_registry.get_by_id("LAB-001")
    assert cl is not None
    assert cl.short_code == "CL"
    assert cl.is_bis_owned is True
    assert cl.lab_type == LabType.CENTRAL
    assert "Sahibabad" in cl.address
    assert "Chemical" in cl.disciplines
    assert "Electrical" in cl.disciplines
    assert "Mechanical" in cl.disciplines
    assert "IS 374" in cl.standards_tested
    assert "IS 1786" in cl.standards_tested

    wrol = lab_registry.get_by_id("LAB-002")
    assert wrol is not None
    assert wrol.short_code == "WROL"
    assert wrol.lab_type == LabType.REGIONAL
    assert "Mumbai" in wrol.city
    assert "Gold Assay" in wrol.disciplines

    srol = lab_registry.get_by_id("LAB-004")
    assert srol is not None
    assert srol.short_code == "SROL"
    assert "Chennai" in srol.city
    assert "IS 16046 (Part 2)" in srol.standards_tested


def test_specialized_partner_institutes(lab_registry):
    """Verifies specialized testing institutes (CPRI, ARAI, NCB, NPL, CIPET, SIIR)."""
    # CPRI: High Voltage Electrical & Solar Inverters
    cpri = lab_registry.get_by_id("LAB-010")
    assert cpri is not None
    assert cpri.short_code == "CPRI"
    assert "High Voltage Electrical" in cpri.disciplines
    assert "IS 16242" in cpri.standards_tested

    # ARAI: Automotive & Helmets
    arai = lab_registry.get_by_id("LAB-014")
    assert arai is not None
    assert arai.short_code == "ARAI"
    assert "IS 4151" in arai.standards_tested

    # NCB: Cement & Concrete
    ncb = lab_registry.get_by_id("LAB-016")
    assert ncb is not None
    assert ncb.short_code == "NCB"
    assert "IS 269" in ncb.standards_tested

    # CIPET: Plastics & Pipes
    cipet = lab_registry.get_by_id("LAB-017")
    assert cipet is not None
    assert cipet.short_code == "CIPET"
    assert "IS 4985" in cipet.standards_tested


def test_standard_to_laboratory_mapping(lab_registry):
    """Verifies retrieval of accredited laboratories for key standard queries."""
    fans_labs = lab_registry.get_labs_for_standard("IS 374")
    assert len(fans_labs) >= 5
    short_codes = {l.short_code for l in fans_labs}
    assert "CL" in short_codes
    assert "CPRI" in short_codes

    li_ion_labs = lab_registry.get_labs_for_standard("IS 16046 (Part 2)")
    assert len(li_ion_labs) >= 4
    li_short_codes = {l.short_code for l in li_ion_labs}
    assert "BNBO" in li_short_codes or "UL" in li_short_codes or "TUV-SUD" in li_short_codes


# ==============================================================================
# 2. Manufacturer CM/L Licence Verification
# ==============================================================================

def test_licence_registry_total_count(licence_registry):
    """Verifies that 450+ manufacturer licences are indexed."""
    assert licence_registry.count() >= 450
    assert licence_registry.count_operative() >= 400


def test_havells_fans_licence(licence_registry):
    """Verifies CM/L-8100123 for Havells ceiling fans."""
    lic = licence_registry.get_by_cml("CM/L-8100123")
    assert lic is not None
    assert "Havells" in lic.licensee_name
    assert "IS 374" in lic.standard_number
    assert lic.status == LicenceStatus.OPERATIVE
    assert "HAVELLS" in lic.brand_names
    assert lic.scheme_code == "SCHEME-I"


def test_tata_steel_rebars_licence(licence_registry):
    """Verifies CM/L-8300301 for Tata Tiscon TMT rebar licence."""
    lic = licence_registry.get_by_cml("CM/L-8300301")
    assert lic is not None
    assert "Tata Steel" in lic.licensee_name
    assert "IS 1786" in lic.standard_number
    assert "TATA TISCON" in lic.brand_names
    assert any("Fe 500D" in v for v in lic.varieties_covered)


def test_bisleri_water_licence(licence_registry):
    """Verifies CM/L-8500501 for Bisleri packaged drinking water."""
    lic = licence_registry.get_by_cml("CM/L-8500501")
    assert lic is not None
    assert "Bisleri" in lic.licensee_name
    assert "IS 14543" in lic.standard_number
    assert "BISLERI" in lic.brand_names


def test_hawkins_pressure_cooker_licence(licence_registry):
    """Verifies CM/L-8900901 for Hawkins pressure cooker licence."""
    lic = licence_registry.get_by_cml("CM/L-8900901")
    assert lic is not None
    assert "Hawkins" in lic.licensee_name
    assert "IS 2347" in lic.standard_number
    assert "HAWKINS" in lic.brand_names


def test_studds_helmet_licence(licence_registry):
    """Verifies CM/L-9001001 for Studds motorcycle helmet licence."""
    lic = licence_registry.get_by_cml("CM/L-9001001")
    assert lic is not None
    assert "Studds" in lic.licensee_name
    assert "IS 4151" in lic.standard_number
    assert "STUDDS" in lic.brand_names


def test_brand_licence_lookup(licence_registry):
    """Verifies looking up licences by brand name."""
    tata_lics = licence_registry.get_licences_by_brand("TATA TISCON")
    assert len(tata_lics) >= 1
    assert tata_lics[0].cml_number == "CM/L-8300301"

    havells_lics = licence_registry.get_licences_by_brand("HAVELLS")
    assert len(havells_lics) >= 1
    assert any("IS 374" in l.standard_number for l in havells_lics)


# ==============================================================================
# 3. Compulsory Registration Scheme (CRS) Verification
# ==============================================================================

def test_crs_registry_total_count(crs_registry):
    """Verifies that 78 electronics CRS records are indexed."""
    assert crs_registry.count() == 78
    assert crs_registry.count_active() >= 70


def test_samsung_li_ion_crs_registration(crs_registry):
    """Verifies R-41001234 for Samsung Li-ion secondary cells."""
    crs = crs_registry.get_by_r_number("R-41001234")
    assert crs is not None
    assert crs.brand_name == "SAMSUNG"
    assert "IS 16046 (Part 2)" in crs.standard_number
    assert crs.scheme_code == "SCHEME-II"
    assert crs.status == CRSStatus.ACTIVE
    assert "EB-BA515ABY" in crs.model_numbers
    assert crs.manufacturing_country == "Vietnam"
    assert "UL India" in crs.testing_laboratory


def test_philips_led_lamp_crs_registration(crs_registry):
    """Verifies R-41002201 for Philips self-ballasted LED lamps."""
    crs = crs_registry.get_by_r_number("R-41002201")
    assert crs is not None
    assert crs.brand_name == "PHILIPS"
    assert "IS 16102 (Part 1)" in crs.standard_number
    assert "9W-B22-6500K" in crs.model_numbers
    assert "ERDA" in crs.testing_laboratory


def test_model_to_r_number_resolution(crs_registry):
    """Verifies lookup of CRS registration directly by electronic model number."""
    record = crs_registry.get_by_model("EB-BA515ABY")
    assert record is not None
    assert record.registration_number == "R-41001234"
    assert record.brand_name == "SAMSUNG"

    led_record = crs_registry.get_by_model("9W-B22-6500K")
    assert led_record is not None
    assert led_record.registration_number == "R-41002201"
    assert led_record.brand_name == "PHILIPS"


# ==============================================================================
# 4. Scheme & Identification Invariants
# ==============================================================================

def test_isi_mark_vs_crs_scheme_distinctness(licence_registry, crs_registry):
    """
    Enforces that ISI Mark licences use SCHEME-I with CM/L numbers,
    while Electronics CRO registrations use SCHEME-II with R-numbers.
    """
    for lic in licence_registry.licences.values():
        assert lic.cml_number.startswith("CM/L-")
        assert lic.scheme_code in ("SCHEME-I", "FMCS")

    for crs in crs_registry.registrations.values():
        assert crs.registration_number.startswith("R-")
        assert crs.scheme_code == "SCHEME-II"
