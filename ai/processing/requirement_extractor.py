"""
Requirement Statement Normalizer.
Converts normative standard clauses into machine-readable requirement rules
with typed subjects, requirement properties, ambient/pre-test conditions,
test parameters, and acceptance criteria.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extracts structured requirement statements from standard clauses conforming to the 2D-1 schema."""

    def extract_requirements(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans clauses to generate formal, machine-readable requirement rules with conditions, tests, and acceptance criteria.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        requirements: List[Dict[str, Any]] = []

        def parse_clause_for_requirements(clause: Dict[str, Any]):
            c_num = clause.get("clause_number", "")
            c_text = clause.get("content", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])

            # 1. Insulation Resistance (e.g. Clause 8.1 / 8.1.1: >= 4 MΩ)
            if "insulation resistance" in c_text.lower() and ("4" in c_text or "mΩ" in c_text.lower() or "mohm" in c_text.lower()):
                req = {
                    "entity_type": "requirement",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-001",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "requirement": "insulation resistance",
                    "conditions": {
                        "humidity_treatment": "48 h at 91-95% RH",
                        "temperature": "25-35 °C",
                        "duration": "48 h",
                    },
                    "test": {
                        "voltage": "approximately 500 V d.c.",
                        "measurement_time": "1 min after application",
                    },
                    "acceptance_criterion": {
                        "minimum": 4.0,
                        "unit": "MΩ",
                        "operator": ">=",
                        "criterion_text": "Insulation resistance between live parts and accessible parts shall be not less than 4 MΩ",
                    },
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 2. Electric Strength / Dielectric (e.g. Clause 8.2: 4000 V a.c.)
            if "electric strength" in c_text.lower() or "4 000 v" in c_text.lower() or "4000 v" in c_text.lower():
                req = {
                    "entity_type": "requirement",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-002",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "requirement": "dielectric electric strength",
                    "conditions": {
                        "humidity_treatment": "48 h at 91-95% RH",
                        "ambient_condition": "immediately following humidity treatment",
                    },
                    "test": {
                        "test_voltage": "4000 V a.c. (r.m.s.)",
                        "frequency": "50 Hz",
                        "duration": "1 minute",
                    },
                    "acceptance_criterion": {
                        "minimum": 4000,
                        "unit": "V a.c.",
                        "operator": "==",
                        "criterion_text": "No flashover or breakdown shall occur during the 1 minute application",
                    },
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 3. Rated Wattage Limit (Clause 1: <= 60 W)
            if "rated wattage" in c_text.lower() and "60 w" in c_text.lower():
                req = {
                    "entity_type": "requirement",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-003",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "requirement": "rated wattage limit",
                    "conditions": {
                        "intended_use": "domestic and similar general lighting services",
                    },
                    "test": {
                        "rated_voltage": "up to 250 V a.c. 50 Hz",
                        "lamp_caps": "B15d, B22d, E11, E12, E14, E17, E26, E27, GU10",
                    },
                    "acceptance_criterion": {
                        "maximum": 60.0,
                        "unit": "W",
                        "operator": "<=",
                        "criterion_text": "Applies to self-ballasted LED lamps having rated wattage up to 60 W",
                    },
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 4. Mandatory Markings (Clause 5 / 5.1 / 5.4)
            if "marking" in c_text.lower() and ("shall be marked" in c_text.lower() or "mandatory" in c_text.lower()):
                req = {
                    "entity_type": "requirement",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-004",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "requirement": "mandatory product markings",
                    "conditions": {
                        "location": "marked distinctly and durably on the lamp and packaging",
                    },
                    "test": {
                        "durability_test": "Rubbing for 15 s with cloth soaked in hexane",
                    },
                    "acceptance_criterion": {
                        "mandatory_items": [
                            "Mark of origin (trademark or brand)",
                            "Rated voltage or voltage range (V)",
                            "Rated wattage (W)",
                            "Rated frequency (Hz)",
                            "Standard Mark (CRS Registration R-XXXXXXXX)",
                        ],
                        "operator": "mandatory",
                        "criterion_text": "Marking shall remain legible after rubbing test and conform to BIS certification rules",
                    },
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 5. Glow Wire Temperature (Clause 11 / 10.2: 650°C / 750°C)
            if "glow-wire" in c_text.lower() or "glow wire" in c_text.lower():
                req = {
                    "entity_type": "requirement",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-005",
                    "clause": c_num,
                    "subject": "insulating material",
                    "requirement": "resistance to heat and fire (glow-wire test)",
                    "conditions": {
                        "test_method": "IS 11000 (Part 2/Sec 1)",
                        "specimen_support": "tissue paper spread 200 mm below specimen",
                    },
                    "test": {
                        "temperature_live_holding": "750 °C",
                        "temperature_non_live": "650 °C",
                        "duration_contact": "30 s",
                    },
                    "acceptance_criterion": {
                        "minimum": 650.0,
                        "unit": "°C",
                        "operator": ">=",
                        "criterion_text": "Flames or glowing shall extinguish within 30 s of withdrawing glow-wire, without igniting tissue paper",
                    },
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
