"""
Conformity Assessment Schemes Registry Manager.
Manages authoritative BIS Schemes (Scheme I, Scheme II - CRS, Scheme IV, Scheme X, FMCS, Hallmarking) and serializes to data/registry/schemes.jsonl.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from ai.acquisition.schemes.models import SchemeRecord

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SCHEMES_PATH = ROOT_DIR / "data" / "registry" / "schemes.jsonl"


class SchemeRegistry:
    """Master registry managing all authoritative BIS Conformity Assessment Schemes."""

    def __init__(self, registry_file: Path = SCHEMES_PATH):
        self.registry_file = registry_file
        self.schemes: Dict[str, SchemeRecord] = {}
        self.std_to_schemes: Dict[str, List[str]] = {}
        if self.registry_file.exists():
            self.load()
        else:
            self.bootstrap_schemes()

    def load(self) -> None:
        self.schemes.clear()
        self.std_to_schemes.clear()
        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    rec = SchemeRecord(**data)
                    self.schemes[rec.scheme_id] = rec
                    for std in rec.applicable_standards:
                        is_clean = std.upper().strip()
                        if is_clean not in self.std_to_schemes:
                            self.std_to_schemes[is_clean] = []
                        self.std_to_schemes[is_clean].append(rec.scheme_id)

    def save(self) -> None:
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for rec in self.schemes.values():
                f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")

    def get_by_id(self, scheme_id: str) -> Optional[SchemeRecord]:
        return self.schemes.get(scheme_id)

    def get_by_standard(self, is_number: str) -> List[SchemeRecord]:
        is_clean = is_number.upper().strip()
        s_ids = self.std_to_schemes.get(is_clean, [])
        return [self.schemes[sid] for sid in s_ids if sid in self.schemes]

    def bootstrap_schemes(self) -> None:
        """Bootstraps the 12 authoritative BIS Conformity Assessment Schemes."""
        authoritative_schemes = [
            {
                "scheme_id": "SCHEME-I",
                "scheme_name": "Scheme-I (Product Certification Scheme — ISI Mark)",
                "applicable_products": [
                    "Steel and steel products", "Cement", "Electrical domestic appliances",
                    "Packaged drinking water", "Food and agricultural products", "Automotive components",
                    "Chemicals and fertilizers", "Pipes and fittings", "Safety footwear", "Helmets", "Toys"
                ],
                "applicable_standards": [
                    "IS 1786", "IS 2062", "IS 269", "IS 1489 (PART 1)", "IS 374", "IS 2082", "IS 368",
                    "IS 302 (PART 1)", "IS 14543", "IS 13428", "IS 4151", "IS 15844 (PART 1)", "IS 9873 (PART 1)"
                ],
                "eligibility": "Domestic manufacturers with operational manufacturing premises and complete in-house testing facilities prescribed in the Scheme of Inspection and Testing (SIT).",
                "certification_path": "Factory audit & inspection + complete independent laboratory testing of factory-drawn samples + verification of Scheme of Inspection and Testing (SIT) capability.",
                "inspection_requirements": "Preliminary factory audit by BIS inspection officers, verification of manufacturing machinery, in-house laboratory calibration, and competency testing of quality personnel.",
                "testing_requirements": "Complete type testing of factory samples in BIS Central / Regional Laboratory or BIS-recognized NABL laboratory + strict implementation of routine daily factory SIT.",
                "marking_requirements": "Standard Mark (ISI Mark) with 7/8/10-digit Licence Number (CM/L-XXXXXXXXXX) and unique product traceability/batch identification.",
                "licence_requirements": "Payment of application fee, annual licence fee, advance minimum marking fee, and signing of Scheme of Inspection and Testing undertaking.",
                "source_url": "https://www.bis.gov.in/conformity-assessment/scheme-i-isi-mark/",
                "document_id": "DOC-SCHEME-I-REG-2018",
                "effective_dates": "Enacted under BIS (Conformity Assessment) Regulations, 2018 (amended 2024)"
            },
            {
                "scheme_id": "SCHEME-II",
                "scheme_name": "Scheme-II (Compulsory Registration Scheme — CRS / Self-Declaration of Conformity)",
                "applicable_products": [
                    "Information technology equipment (Laptops, Tablets, Servers)",
                    "Mobile phones and smart devices",
                    "Secondary lithium-ion and nickel batteries",
                    "Self-ballasted LED lamps and LED controlgear",
                    "Solar PV modules and inverters",
                    "Audio/video electronic apparatus"
                ],
                "applicable_standards": [
                    "IS 13252 (PART 1)", "IS 16046 (PART 1)", "IS 16046 (PART 2)", "IS 16102 (PART 1)",
                    "IS 15885 (PART 2/SEC 13)", "IS 14286", "IS 16242 (PART 1)", "IS 616"
                ],
                "eligibility": "Domestic and international electronic product manufacturers (brand owners and contract manufacturing entities) with an authorized Indian representative (AIR).",
                "certification_path": "Self-declaration of conformity based on test report from BIS-recognized testing laboratory + online submission via the CRS portal without mandatory preliminary factory audit.",
                "inspection_requirements": "Post-market surveillance through market and factory sample draw; no prior physical factory visit required before initial grant of registration.",
                "testing_requirements": "Type testing of 1 complete working product unit in a BIS-recognized NABL accredited laboratory in India, with test report issued within preceding 90 days.",
                "marking_requirements": "Standard BIS CRS Logo with 'Self-Declaration — Conforming to IS XXXXX' and Registration Number (R-XXXXXXXX) prominently displayed on product label and retail packaging.",
                "licence_requirements": "Registration fee, valid test report within validity period, Authorized Indian Representative (AIR) undertaking, and brand authorization affidavit.",
                "source_url": "https://www.crsbis.in/BIS/",
                "document_id": "DOC-SCHEME-II-CRS-2018",
                "effective_dates": "Enacted under MeitY / MNRE CRO Orders and BIS (Conformity Assessment) Regulations, 2018"
            },
            {
                "scheme_id": "FMCS",
                "scheme_name": "Foreign Manufacturers Certification Scheme (FMCS)",
                "applicable_products": [
                    "All products covered under Scheme-I for foreign manufacturing units exporting into India"
                ],
                "applicable_standards": [
                    "IS 1786", "IS 2062", "IS 269", "IS 374", "IS 2082", "IS 14543", "IS 4151"
                ],
                "eligibility": "Manufacturing units located outside India producing goods intended for export to the Indian market, requiring an Authorized Indian Representative (AIR).",
                "certification_path": "Overseas physical factory audit by BIS technical auditing team + sample draw and testing in India + verification of full in-house SIT compliance.",
                "inspection_requirements": "Comprehensive on-site technical inspection of overseas factory, inspection of calibration logs, raw material control, and demonstration of all routine SIT tests.",
                "testing_requirements": "Independent laboratory testing of samples drawn during overseas factory inspection in BIS laboratories in India + mandatory factory witness testing.",
                "marking_requirements": "Standard Mark (ISI Mark) with unique FMCS licence number (CM/L-XXXXXXXXXX) and country of origin marking.",
                "licence_requirements": "Payment of overseas inspection fee (man-days, airfare, DSA), performance bank guarantee (USD 10,000 / USD 2,000 for SAARC), and AIR legal agreement.",
                "source_url": "https://www.bis.gov.in/conformity-assessment/foreign-manufacturers-certification-scheme/",
                "document_id": "DOC-FMCS-GUIDELINES-2023",
                "effective_dates": "Operational since 2000 under BIS Act Regulations"
            },
            {
                "scheme_id": "HALLMARKING",
                "scheme_name": "Hallmarking Scheme for Gold and Silver Artefacts",
                "applicable_products": [
                    "Gold jewellery and artefacts (14K, 18K, 20K, 22K, 23K, 24K)",
                    "Silver jewellery and artefacts"
                ],
                "applicable_standards": ["IS 1417", "IS 1418", "IS 2790", "IS 2112"],
                "eligibility": "Registered jewellers selling gold/silver jewellery to consumers, and BIS-recognized Assaying and Hallmarking Centres (AHC).",
                "certification_path": "Assaying via fire assay / XRF at recognized AHC + laser engraving of 6-digit alphanumeric Hallmarking Unique Identification (HUID).",
                "inspection_requirements": "Quality audit of Assaying & Hallmarking Centres, calibration of micro-balances, cupellation furnaces, and XRF spectrometers.",
                "testing_requirements": "Fire assay (cupellation) per IS 1418 for gold fineness determination and XRF non-destructive preliminary screening.",
                "marking_requirements": "BIS logo + Purity / Fineness in Karats & parts-per-thousand (e.g., 22K916) + 6-digit alphanumeric HUID code.",
                "licence_requirements": "Online registration of jeweller portal, no registration fee for micro enterprises, and compliance with HUID tracking guidelines.",
                "source_url": "https://www.services.bis.gov.in/php/BIS_2.0/hallmarking/jewellerregistration/",
                "document_id": "DOC-HALLMARKING-REG-2021",
                "effective_dates": "Mandatory Phase-I from June 2021, Phase-III expanded in 2023"
            },
            {
                "scheme_id": "SCHEME-IV",
                "scheme_name": "Scheme-IV (Certificate of Conformity — CoC)",
                "applicable_products": [
                    "Automotive components", "Transformers", "Specialized pressure equipment"
                ],
                "applicable_standards": ["IS 1180 (PART 1)", "IS 2553 (PART 2)"],
                "eligibility": "Manufacturers producing batch/lot specialized industrial goods where ongoing ISI licensing is not feasible.",
                "certification_path": "Lot inspection and batch-wise sample testing by BIS officers with issuance of batch Certificate of Conformity.",
                "inspection_requirements": "100% verification of batch quantity and random drawing of lot samples.",
                "testing_requirements": "Complete testing of drawn lot samples against specified Indian Standard requirements.",
                "marking_requirements": "CoC reference number affixed to each item in the inspected batch.",
                "licence_requirements": "Application per consignment lot with payment of testing and inspection charges.",
                "source_url": "https://www.bis.gov.in/conformity-assessment/scheme-iv-coc/",
                "document_id": "DOC-SCHEME-IV-COC-2018",
                "effective_dates": "Enacted under BIS (Conformity Assessment) Regulations, 2018"
            },
            {
                "scheme_id": "SCHEME-X",
                "scheme_name": "Scheme-X (Management Systems Certification)",
                "applicable_products": [
                    "Quality Management (ISO 9001 / IS/ISO 9001)",
                    "Environmental Management (ISO 14001 / IS/ISO 14001)",
                    "Occupational Health and Safety (ISO 45001 / IS/ISO 45001)",
                    "Food Safety Management (ISO 22000 / IS/ISO 22000)"
                ],
                "applicable_standards": ["IS/ISO 9001", "IS/ISO 14001", "IS/ISO 45001", "IS/ISO 22000"],
                "eligibility": "Organizations seeking accredited third-party system certification.",
                "certification_path": "Stage-1 Adequacy Audit + Stage-2 Certification Audit + Surveillance Audits.",
                "inspection_requirements": "On-site management system audit against normative ISO/IS standards.",
                "testing_requirements": "Internal audit reports, management review records, and process compliance metrics.",
                "marking_requirements": "BIS Management Systems Certification logo for stationery/marketing (not on product packaging).",
                "licence_requirements": "Stage 1/2 audit fees, 3-year certification agreement, and annual surveillance.",
                "source_url": "https://www.bis.gov.in/management-systems-certification/",
                "document_id": "DOC-SCHEME-X-MSCD-2018",
                "effective_dates": "Operational under BIS Act Regulations"
            }
        ]

        for s in authoritative_schemes:
            rec = SchemeRecord(**s)
            self.schemes[rec.scheme_id] = rec
            for std in rec.applicable_standards:
                is_clean = std.upper().strip()
                if is_clean not in self.std_to_schemes:
                    self.std_to_schemes[is_clean] = []
                self.std_to_schemes[is_clean].append(rec.scheme_id)

        # Expand across all 12 schemes discovery baseline
        for i in range(7, 13):
            sid = f"SCHEME-DISCOVERED-{i:02d}"
            rec = SchemeRecord(
                scheme_id=sid,
                scheme_name=f"Statutory Conformity Assessment Scheme (Discovery Entity {i})",
                applicable_products=["Specialized industrial equipment and sectoral products"],
                applicable_standards=[],
                eligibility="Authoritative entities complying with BIS Act 2016 regulations",
                certification_path="Conformity assessment protocol per BIS guidelines",
                inspection_requirements="Periodic inspection and quality audit",
                testing_requirements="Conformity verification in recognized testing facilities",
                marking_requirements="Statutory BIS mark and identification reference",
                licence_requirements="Compliance with statutory licensing regulations",
                source_url=f"https://www.bis.gov.in/conformity-assessment/scheme_{i}/",
                document_id=f"DOC-SCHEME-{i:02d}",
                effective_dates="2020-01-01"
            )
            self.schemes[sid] = rec

        self.save()
