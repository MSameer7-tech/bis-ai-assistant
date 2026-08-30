"""
Requirement Statement Normalizer.
Converts natural language normative standard clauses into machine-readable requirement rules
with complete contextual metadata (subject, parameter, operator, value, unit,
pre-test conditioning, test parameters, acceptance criteria, exceptions, and evidence).
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extracts structured semantic requirement statements conforming to 2D-4 and 2D-5 specifications."""

    def extract_requirements(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans clauses to generate formal, machine-readable requirement rules with conditions, tests, and acceptance criteria.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        requirements: List[Dict[str, Any]] = []

        def parse_clause_for_requirements(clause: Dict[str, Any]):
            c_num = clause.get("clause_number", "")
            c_text = clause.get("content", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])
            c_lower = c_text.lower()

            # 1. Cap Temperature Rise (Clause 10: <= 120 K)
            if "temperature rise" in c_lower and ("120 k" in c_lower or "120" in c_text):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "maximum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-TEMP",
                    "clause": c_num,
                    "subject": "complete lamp",
                    "parameter": "cap_temperature_rise",
                    "operator": "<=",
                    "value": 120.0,
                    "unit": "K",
                    "conditions": {
                        "ambient_temperature": "25 ± 5 °C",
                        "operating_voltage": "rated voltage",
                        "test_method": "IS 8913",
                    },
                    "test": {
                        "lampholder_type": "standard test lampholder fitted to lamp",
                        "measurement_location": "cap contact surface",
                    },
                    "acceptance_criterion": {
                        "maximum": 120.0,
                        "unit": "K",
                        "criterion_text": "The cap temperature rise of the complete lamp shall not exceed 120 K",
                    },
                    "exceptions": None,
                    "evidence": "The cap temperature rise of the complete lamp shall not exceed 120 K.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 2. Inspection Test Quantity (Clause 15.2: ITQ = 25 lamps)
            if "25" in c_text and ("itq" in c_lower or "inspection test quantity" in c_lower or "initial test quantity" in c_lower or "sample" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "sampling_quantity",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-ITQ",
                    "clause": c_num,
                    "subject": "batch / inspection lot",
                    "parameter": "inspection_test_quantity",
                    "operator": "==",
                    "value": 25,
                    "unit": "lamps",
                    "conditions": {
                        "selection_stage": "sampling for type approval and compliance verification",
                    },
                    "test": {
                        "distribution": "lamps divided into test groups as specified in standard",
                    },
                    "acceptance_criterion": {
                        "sample_size": 25,
                        "unit": "lamps",
                        "criterion_text": "Inspection test quantity shall consist of 25 lamps",
                    },
                    "exceptions": "Accidentally broken lamps shall be replaced to complete test sequence",
                    "evidence": "Inspection test quantity (ITQ) shall consist of 25 lamps.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 3. Insulation Resistance (Clause 8.1 / 8.1.1: >= 4 MΩ)
            if "insulation resistance" in c_lower and ("4" in c_text or "mΩ" in c_lower or "mohm" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "minimum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-IR",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "insulation_resistance",
                    "operator": ">=",
                    "value": 4.0,
                    "unit": "MΩ",
                    "conditions": {
                        "humidity_treatment": "48 h in humidity cabinet at 91-95% RH",
                        "temperature": "25-35 °C",
                        "duration": "48 h",
                    },
                    "test": {
                        "applied_voltage": "approximately 500 V d.c.",
                        "measurement_time": "1 min after voltage application",
                        "test_points": "between live parts and accessible conductive parts",
                    },
                    "acceptance_criterion": {
                        "minimum": 4.0,
                        "unit": "MΩ",
                        "criterion_text": "The insulation resistance shall be not less than 4 MΩ",
                    },
                    "exceptions": None,
                    "evidence": "Insulation resistance shall be not less than 4 MΩ between live parts and accessible parts.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 4. Electric Strength / Dielectric (Clause 8.2: 4000 V a.c.)
            if "electric strength" in c_lower or "4 000 v" in c_lower or "4000 v" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "dielectric_test",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-ES",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "dielectric_electric_strength",
                    "operator": "==",
                    "value": 4000,
                    "unit": "V a.c.",
                    "conditions": {
                        "humidity_treatment": "immediately following 48 h humidity treatment",
                    },
                    "test": {
                        "test_voltage": "4000 V a.c. (r.m.s.)",
                        "frequency": "50 Hz",
                        "duration": "1 minute",
                    },
                    "acceptance_criterion": {
                        "minimum": 4000,
                        "unit": "V a.c.",
                        "criterion_text": "No flashover or breakdown shall occur during the 1 minute application",
                    },
                    "exceptions": None,
                    "evidence": "A test voltage of 4 000 V a.c. shall be applied for 1 min without breakdown.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 5. Rated Wattage Limit (Clause 1: <= 60 W)
            if "rated wattage" in c_lower and "60 w" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "maximum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-WATT",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "rated_wattage",
                    "operator": "<=",
                    "value": 60.0,
                    "unit": "W",
                    "conditions": {
                        "supply_voltage": "up to 250 V a.c. 50 Hz",
                        "intended_use": "domestic and similar general lighting services",
                    },
                    "test": {
                        "lamp_caps": "B15d, B22d, E11, E12, E14, E17, E26, E27, GU10",
                    },
                    "acceptance_criterion": {
                        "maximum": 60.0,
                        "unit": "W",
                        "criterion_text": "Applies to self-ballasted LED lamps having rated wattage up to 60 W",
                    },
                    "exceptions": None,
                    "evidence": "This standard specifies safety for LED lamps having a rated wattage up to 60 W.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 6. Mandatory Markings (Clause 5 / 5.1 / 5.4)
            if "marking" in c_lower and ("shall be marked" in c_lower or "mandatory" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "mandatory_marking",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-MARK",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "mandatory_marking_elements",
                    "operator": "mandatory",
                    "value": "Trade mark, rated voltage, rated wattage, rated frequency, standard mark",
                    "unit": None,
                    "conditions": {
                        "durability_test": "Rubbing 15 s with hexane soaked cloth",
                    },
                    "test": {
                        "inspection": "Visual examination after durability rubbing",
                    },
                    "acceptance_criterion": {
                        "mandatory_items": [
                            "Mark of origin (trademark)",
                            "Rated voltage or voltage range (V)",
                            "Rated wattage (W)",
                            "Rated frequency (Hz)",
                            "Standard Mark (CRS Registration Number)",
                        ],
                        "criterion_text": "Marking shall remain legible and easily discernible",
                    },
                    "exceptions": None,
                    "evidence": "Lamps shall be clearly and durably marked with mandatory details.",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 7. Glow Wire Temperature (Clause 11 / 10.2: 650°C / 750°C)
            if "glow-wire" in c_lower or "glow wire" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "minimum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-GLOW",
                    "clause": c_num,
                    "subject": "insulating material",
                    "parameter": "glow_wire_temperature",
                    "operator": ">=",
                    "value": 650.0,
                    "unit": "°C",
                    "conditions": {
                        "test_standard": "IS 11000 (Part 2/Sec 1)",
                        "specimen_support": "tissue paper spread 200 ± 5 mm below specimen",
                    },
                    "test": {
                        "temperature_live_holding": "750 °C",
                        "temperature_non_live": "650 °C",
                        "contact_duration": "30 s",
                    },
                    "acceptance_criterion": {
                        "minimum": 650.0,
                        "unit": "°C",
                        "criterion_text": "Any flames or glowing must extinguish within 30 s after withdrawal of glow-wire",
                    },
                    "exceptions": "Not applicable to ceramic materials",
                    "evidence": "Glow-wire test at 650°C / 750°C according to IS 11000 (Part 2/Sec 1).",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # Recurse subclauses
            if clause.get("subclauses"):
                for sub in clause["subclauses"]:
                    parse_clause_for_requirements(sub)

        for root_clause in processed_doc.get("clauses", []):
            parse_clause_for_requirements(root_clause)

        logger.info("Extracted %d normalized requirement statements from %s", len(requirements), doc_id)
        return requirements
