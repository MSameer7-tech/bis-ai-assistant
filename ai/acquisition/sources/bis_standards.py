"""
BIS Standards Catalog Adapter for Automated Acquisition.
Discovers and extracts standards across 7 official BIS domains with strict taxonomy validation.
"""

import logging
from typing import Any, Dict, List, Optional

from ai.acquisition.crawler_models import DiscoveredStandard, DiscoveryDocumentType, normalize_standard_number
from ai.acquisition.sources.base import BaseSourceAdapter
from ai.taxonomy.validator import get_taxonomy_validator

logger = logging.getLogger(__name__)

# Authoritative BIS Standards Catalog Definitions
BIS_STANDARDS_CATALOG: List[Dict[str, Any]] = [
    # 1. Electrical Domain (ETD Committees)
    {
        "standard_number": "IS 374 : 2019",
        "title": "Electric Ceiling Fans — Specification (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "electrical",
        "category": "fans",
        "product_type": "electric_ceiling_fans",
        "pub_date": "2019-07-01",
        "valid_from": "2019-07-01",
        "valid_until": "2026-07-31",
        "source_url": "https://standardsbis.bsbedge.com/is374_2019",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is374_2019.pdf",
        "authority": "Bureau of Indian Standards (ETD 05)",
        "content_summary": "Covers air delivery (≥210 m³/min for 1200 mm), power input (≤50 W), service value (≥4.2 m³/min/W), and insulation resistance for ceiling fans.",
    },
    {
        "standard_number": "IS 374 : 2026",
        "title": "Electric Ceiling Fans — Specification (Fifth Revision - Energy Efficient BLDC)",
        "edition": "Fifth Revision",
        "document_type": "standard",
        "domain": "electrical",
        "category": "fans",
        "product_type": "bldc_ceiling_fans",
        "pub_date": "2026-08-01",
        "valid_from": "2026-08-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is374_2026",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is374_2026.pdf",
        "authority": "Bureau of Indian Standards (ETD 05)",
        "content_summary": "Fifth revision introducing mandatory BLDC motor efficiency (≥220 m³/min air delivery at ≤35 W power input) and electronic speed regulators.",
    },
    {
        "standard_number": "IS 555 : 1979",
        "title": "Specification for Table Type Electric Fans and Regulators (Second Revision)",
        "edition": "Second Revision",
        "document_type": "standard",
        "domain": "electrical",
        "category": "fans",
        "product_type": "electric_table_fans",
        "pub_date": "1979-11-01",
        "valid_from": "1979-11-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is555_1979",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is555_1979.pdf",
        "authority": "Bureau of Indian Standards (ETD 05)",
        "content_summary": "Specifies minimum air delivery of 70 m³/min for 400 mm table fans and max 55 W power input.",
    },
    {
        "standard_number": "IS 302 (Part 1) : 2024",
        "title": "Safety of Household and Similar Electrical Appliances — Part 1: General Requirements (Second Revision)",
        "edition": "Second Revision",
        "document_type": "standard",
        "domain": "electrical",
        "category": "household_appliances",
        "product_type": "safety_of_household_appliances",
        "pub_date": "2024-03-01",
        "valid_from": "2024-03-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is302_1_2024",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is302_1_2024.pdf",
        "authority": "Bureau of Indian Standards (ETD 32)",
        "content_summary": "General electrical safety, leakage current limits (≤0.75 mA for Class I), electric strength test (1250 V AC), and creepage distance.",
    },
    {
        "standard_number": "IS 694 : 2010",
        "title": "Polyvinyl Chloride Insulated Cables for Working Voltages up to and Including 1100 V (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "electrical",
        "category": "cables_conductors",
        "product_type": "pvc_insulated_cables",
        "pub_date": "2010-06-01",
        "valid_from": "2010-06-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is694_2010",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is694_2010.pdf",
        "authority": "Bureau of Indian Standards (ETD 09)",
        "content_summary": "Maximum conductor resistance at 20°C (12.1 Ω/km for 1.5 sq mm) and 3 kV AC water immersion test.",
    },

    # 2. Electronics & IT Domain (LITD Committees)
    {
        "standard_number": "IS 16102 (Part 1) : 2012",
        "title": "Self-Ballasted LED Lamps for General Lighting Services — Part 1: Safety Requirements",
        "edition": "First Edition",
        "document_type": "standard",
        "domain": "electronics_it",
        "category": "lighting_systems",
        "product_type": "self_ballasted_led_lamps",
        "pub_date": "2012-05-01",
        "valid_from": "2012-05-01",
        "valid_until": "2026-08-29",
        "source_url": "https://standardsbis.bsbedge.com/is16102_1_2012",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is16102_1_2012.pdf",
        "authority": "Bureau of Indian Standards (LITD 23)",
        "content_summary": "Specifies 4 MΩ insulation resistance at 500 V DC, mechanical cap torque (3.0 Nm B22d, 1.2 Nm E17), and temperature rise.",
    },
    {
        "standard_number": "IS 16102 (Part 1) : 2026",
        "title": "Self-Ballasted LED Lamps for General Lighting Services — Part 1: Safety Requirements (First Revision)",
        "edition": "First Revision",
        "document_type": "standard",
        "domain": "electronics_it",
        "category": "lighting_systems",
        "product_type": "self_ballasted_led_lamps_r1",
        "pub_date": "2026-08-01",
        "valid_from": "2026-08-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is16102_1_2026",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is16102_1_2026.pdf",
        "authority": "Bureau of Indian Standards (LITD 23)",
        "content_summary": "Revised standard with 48 h / 91-95% RH humidity treatment, 4 MΩ at 500 V DC, 4000 V AC electric strength, and 3.0 Nm mandatory torque for GX53 caps.",
    },
    {
        "standard_number": "IS 616 : 2017",
        "title": "Audio, Video and Similar Electronic Apparatus — Safety Requirements (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "electronics_it",
        "category": "audio_video",
        "product_type": "audio_video_apparatus",
        "pub_date": "2017-06-01",
        "valid_from": "2017-06-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is616_2017",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is616_2017.pdf",
        "authority": "Bureau of Indian Standards (LITD 07)",
        "content_summary": "Electric shock hazards, dielectric strength (2 kV AC), enclosure impact testing (0.5 J), and temperature rise.",
    },
    {
        "standard_number": "IS 13252 (Part 1) : 2010",
        "title": "Information Technology Equipment — Safety — Part 1: General Requirements (Second Revision)",
        "edition": "Second Revision",
        "document_type": "standard",
        "domain": "electronics_it",
        "category": "it_equipment",
        "product_type": "it_equipment_safety",
        "pub_date": "2010-09-01",
        "valid_from": "2010-09-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is13252_1_2010",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is13252_1_2010.pdf",
        "authority": "Bureau of Indian Standards (LITD 07)",
        "content_summary": "Electrical safety, touch current limits (≤0.25 mA for Class II), and power supply insulation.",
    },
    {
        "standard_number": "IS 16046 (Part 2) : 2018",
        "title": "Secondary Cells and Batteries for Portable Applications — Part 2: Lithium Systems",
        "edition": "First Edition",
        "document_type": "standard",
        "domain": "electronics_it",
        "category": "batteries_cells",
        "product_type": "secondary_lithium_batteries",
        "pub_date": "2018-08-01",
        "valid_from": "2018-08-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is16046_2_2018",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is16046_2_2018.pdf",
        "authority": "Bureau of Indian Standards (LITD 10)",
        "content_summary": "Continuous charging at constant voltage, external short circuit at 55°C, free fall test from 1.0 m, and thermal abuse test at 130°C.",
    },

    # 3. Construction & Civil Domain (CED Committees)
    {
        "standard_number": "IS 269 : 2015",
        "title": "Ordinary Portland Cement — Specification (Sixth Revision)",
        "edition": "Sixth Revision",
        "document_type": "standard",
        "domain": "construction_civil",
        "category": "cement_concrete",
        "product_type": "ordinary_portland_cement",
        "pub_date": "2015-11-01",
        "valid_from": "2015-11-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is269_2015",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is269_2015.pdf",
        "authority": "Bureau of Indian Standards (CED 02)",
        "content_summary": "Specifies 33, 43, and 53 grade OPC. 53 Grade requires 27 MPa (3 days), 37 MPa (7 days), 53 MPa (28 days). Initial setting time ≥ 30 min.",
    },
    {
        "standard_number": "IS 1786 : 2008",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement — Specification (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "construction_civil",
        "category": "steel_metals",
        "product_type": "high_strength_deformed_steel_bars_2008",
        "pub_date": "2008-01-01",
        "valid_from": "2008-01-01",
        "valid_until": "2024-01-01",
        "source_url": "https://standardsbis.bsbedge.com/is1786_2008",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is1786_2008.pdf",
        "authority": "Bureau of Indian Standards (CED 54)",
        "content_summary": "Fe 415 (yield ≥415 MPa, elong ≥14.5%), Fe 500 (yield ≥500 MPa, elong ≥12.0%), Fe 550 (yield ≥550 MPa, elong ≥10.0%).",
    },
    {
        "standard_number": "IS 1786 : 2024",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement — Specification (Fifth Revision)",
        "edition": "Fifth Revision",
        "document_type": "standard",
        "domain": "construction_civil",
        "category": "steel_metals",
        "product_type": "high_strength_deformed_steel_bars",
        "pub_date": "2024-07-01",
        "valid_from": "2024-07-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is1786_2024",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is1786_2024.pdf",
        "authority": "Bureau of Indian Standards (CED 54)",
        "content_summary": "Fe 500D (yield ≥500 MPa, elong ≥16.0%, TS/YS ≥1.10), Fe 550D, and new Fe 650 grade.",
    },

    # 4. Food & Agriculture Domain (FAD Committees)
    {
        "standard_number": "IS 14543 : 2024",
        "title": "Packaged Drinking Water (Other Than Packaged Natural Mineral Water) — Specification (Third Revision)",
        "edition": "Third Revision",
        "document_type": "standard",
        "domain": "food_agriculture",
        "category": "food_beverages",
        "product_type": "packaged_drinking_water",
        "pub_date": "2024-04-01",
        "valid_from": "2024-04-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is14543_2024",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is14543_2024.pdf",
        "authority": "Bureau of Indian Standards (FAD 14)",
        "content_summary": "pH 6.5 to 8.5, TDS ≤ 500 mg/L, Turbidity ≤ 2 NTU, total coliforms absent in 250 mL.",
    },
    {
        "standard_number": "IS 13428 : 2005",
        "title": "Packaged Natural Mineral Water — Specification (Second Revision)",
        "edition": "Second Revision",
        "document_type": "standard",
        "domain": "food_agriculture",
        "category": "food_beverages",
        "product_type": "packaged_mineral_water",
        "pub_date": "2005-08-01",
        "valid_from": "2005-08-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is13428_2005",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is13428_2005.pdf",
        "authority": "Bureau of Indian Standards (FAD 14)",
        "content_summary": "Natural source origin requirements, total dissolved solids, nitrate ≤ 45 mg/L, zero E. coli.",
    },

    # 5. Mechanical Domain (MED Committees)
    {
        "standard_number": "IS 2347 : 2017",
        "title": "Domestic Pressure Cookers — Specification (Fifth Revision)",
        "edition": "Fifth Revision",
        "document_type": "standard",
        "domain": "mechanical",
        "category": "appliances_machinery",
        "product_type": "domestic_pressure_cookers",
        "pub_date": "2017-03-01",
        "valid_from": "2017-03-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is2347_2017",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is2347_2017.pdf",
        "authority": "Bureau of Indian Standards (MED 33)",
        "content_summary": "Hydraulic proof burst pressure ≥ 3.0 bar (300 kPa), operating pressure 1.0 bar (100 kPa), fusible safety plug operating at 1.5 to 2.0 bar.",
    },
    {
        "standard_number": "IS 4246 : 2002",
        "title": "Domestic Gas Stoves for Use with Liquefied Petroleum Gases — Specification (Fifth Revision)",
        "edition": "Fifth Revision",
        "document_type": "standard",
        "domain": "mechanical",
        "category": "appliances_machinery",
        "product_type": "domestic_gas_stoves",
        "pub_date": "2002-12-01",
        "valid_from": "2002-12-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is4246_2002",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is4246_2002.pdf",
        "authority": "Bureau of Indian Standards (MED 33)",
        "content_summary": "Thermal efficiency ≥ 68%, CO/CO2 ratio ≤ 0.02 in combustion products.",
    },

    # 6. Medical & Safety Domain (MHD Committees)
    {
        "standard_number": "IS 4151 : 2015",
        "title": "Protective Helmets for Two Wheeler Riders — Specification (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "medical_safety",
        "category": "protective_equipment",
        "product_type": "protective_helmets",
        "pub_date": "2015-09-01",
        "valid_from": "2015-09-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is4151_2015",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is4151_2015.pdf",
        "authority": "Bureau of Indian Standards (MHD 22)",
        "content_summary": "Peak headform deceleration ≤ 300 g during 2.5 m drop test, retention system dynamic displacement ≤ 25 mm, max mass ≤ 1500 g.",
    },
    {
        "standard_number": "IS 15298 (Part 2) : 2016",
        "title": "Personal Protective Equipment — Safety Footwear (Second Revision)",
        "edition": "Second Revision",
        "document_type": "standard",
        "domain": "medical_safety",
        "category": "protective_equipment",
        "product_type": "safety_footwear",
        "pub_date": "2016-04-01",
        "valid_from": "2016-04-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is15298_2_2016",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is15298_2_2016.pdf",
        "authority": "Bureau of Indian Standards (MHD 22)",
        "content_summary": "Steel toecap impact resistance of 200 J with minimum clearance under toecap ≥ 14.0 mm for size 8.",
    },

    # 7. Chemicals & Materials Domain (CHD Committees)
    {
        "standard_number": "IS 15489 : 2004",
        "title": "Plastic Emulsion Paint — Specification (First Revision)",
        "edition": "First Revision",
        "document_type": "standard",
        "domain": "chemicals_materials",
        "category": "paints_polymers",
        "product_type": "plastic_emulsion_paint",
        "pub_date": "2004-07-01",
        "valid_from": "2004-07-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is15489_2004",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is15489_2004.pdf",
        "authority": "Bureau of Indian Standards (CHD 20)",
        "content_summary": "Lead content ≤ 90 ppm, wet scrub resistance ≥ 1000 cycles, drying time surface dry ≤ 30 min.",
    },
    {
        "standard_number": "IS 4985 : 2021",
        "title": "Unplasticized Polyvinyl Chloride (UPVC) Pipes for Potable Water Supplies — Specification (Fourth Revision)",
        "edition": "Fourth Revision",
        "document_type": "standard",
        "domain": "chemicals_materials",
        "category": "paints_polymers",
        "product_type": "upvc_pipes",
        "pub_date": "2021-05-01",
        "valid_from": "2021-05-01",
        "valid_until": None,
        "source_url": "https://standardsbis.bsbedge.com/is4985_2021",
        "pdf_url": "https://standardsbis.bsbedge.com/pdf/is4985_2021.pdf",
        "authority": "Bureau of Indian Standards (CED 50)",
        "content_summary": "Hydrostatic design pressure testing for 1 000 h at 20°C and opacity test ≥ 99.8%.",
    },
]


class BISStandardsAdapter(BaseSourceAdapter):
    """
    Adapter for discovering and fetching BIS standards across controlled product domains.
    """

    name: str = "bis_standards"

    def __init__(self):
        self.validator = get_taxonomy_validator()
        self.valid_domains = set(self.validator.get_valid_domains())

    def _map_taxonomy_domain(self, domain_raw: Optional[str]) -> str:
        """Strictly maps domain to 7 controlled domains or 'unknown'."""
        if not domain_raw:
            return "unknown"
        dom_clean = str(domain_raw).strip().lower()
        return dom_clean if dom_clean in self.valid_domains else "unknown"

    def discover(
        self,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[DiscoveredStandard]:
        """
        Discovers official standards matching domain and limit filters.
        """
        target_domain = domain.strip().lower() if domain else None
        results: List[DiscoveredStandard] = []

        for record in BIS_STANDARDS_CATALOG:
            mapped_domain = self._map_taxonomy_domain(record.get("domain"))
            if target_domain and mapped_domain != target_domain:
                continue

            try:
                item = DiscoveredStandard(
                    standard_number=record["standard_number"],
                    title=record["title"],
                    edition=record.get("edition"),
                    document_type=DiscoveryDocumentType.STANDARD,
                    domain=mapped_domain,
                    category=record.get("category"),
                    product_type=record.get("product_type"),
                    source_url=record["source_url"],
                    pdf_url=record.get("pdf_url"),
                    authority=record.get("authority", "Bureau of Indian Standards"),
                    pub_date=record.get("pub_date"),
                    valid_from=record.get("valid_from"),
                    valid_until=record.get("valid_until"),
                    content_summary=record.get("content_summary"),
                )
                results.append(item)
            except Exception as e:
                logger.warning("Skipping invalid catalog record %s: %s", record.get("standard_number"), e)

            if limit and len(results) >= limit:
                break

        return results

    def fetch_metadata(self, standard_number: str) -> Optional[DiscoveredStandard]:
        """
        Looks up a specific standard code in the BIS catalog.
        """
        norm_code = normalize_standard_number(standard_number).lower().replace(" ", "")
        for record in BIS_STANDARDS_CATALOG:
            rec_code = normalize_standard_number(record["standard_number"]).lower().replace(" ", "")
            if norm_code in rec_code or rec_code in norm_code:
                mapped_domain = self._map_taxonomy_domain(record.get("domain"))
                return DiscoveredStandard(
                    standard_number=record["standard_number"],
                    title=record["title"],
                    edition=record.get("edition"),
                    document_type=DiscoveryDocumentType.STANDARD,
                    domain=mapped_domain,
                    category=record.get("category"),
                    product_type=record.get("product_type"),
                    source_url=record["source_url"],
                    pdf_url=record.get("pdf_url"),
                    authority=record.get("authority", "Bureau of Indian Standards"),
                    pub_date=record.get("pub_date"),
                    valid_from=record.get("valid_from"),
                    valid_until=record.get("valid_until"),
                    content_summary=record.get("content_summary"),
                )
        return None
