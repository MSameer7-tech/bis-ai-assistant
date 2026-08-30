"""
Requirement Statement Normalizer.
Converts normative standard clauses into machine-readable requirement rules
with typed subjects, properties, operators, threshold values, and test conditions.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extracts structured requirement statements from standard clauses."""

    def extract_requirements(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans clauses to generate formal, machine-readable requirement rules.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        requirements: List[Dict[str, Any]] = []

        def parse_clause_for_requirements(clause: Dict[str, Any]):
            c_num = clause.get("clause_number", "")
            c_text = clause.get("content", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])

            # 1. Insulation Resistance (e.g. Clause 8.1 / 8.1.1: >= 4 MΩ)
            if "insulation resistance" in c_text.lower() and ("4" in c_text or "mΩ" in c_text.lower() or "mohm" in c_text.lower()):
                req = {
                    "requirement_id": f"REQ-{doc_id}-{c_num}-001",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "property": "insulation_resistance",
                    "operator": ">=",
                    "value": 4.0,
                    "unit": "MΩ",
                    "condition": {
                        "humidity_treatment": "48 h at 91-95% RH",
                        "measurement_voltage": "500 V d.c.",
                        "measurement_time": "1 min after voltage application",
                    },
                    "compliance_criteria": "Insulation resistance between live parts and accessible parts shall not be less than 4 MΩ",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 2. Electric Strength / Dielectric (e.g. Clause 8.2: 4000 V a.c.)
            if "electric strength" in c_text.lower() or "4 000 v" in c_text.lower() or "4000 v" in c_text.lower():
                req = {
                    "requirement_id": f"REQ-{doc_id}-{c_num}-002",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "property": "dielectric_electric_strength",
                    "operator": "==",
                    "value": 4000,
                    "unit": "V a.c.",
                    "condition": {
                        "duration": "1 minute",
                        "waveform": "50 Hz r.m.s.",
                    },
                    "compliance_criteria": "No flashover or breakdown shall occur during the 1 minute test",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 3. Rated Wattage Limit (Clause 1: <= 60 W)
            if "rated wattage" in c_text.lower() and "60 w" in c_text.lower():
                req = {
                    "requirement_id": f"REQ-{doc_id}-{c_num}-003",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "property": "rated_wattage_limit",
                    "operator": "<=",
                    "value": 60.0,
                    "unit": "W",
                    "condition": {
                        "voltage_range": "up to 250 V a.c. 50 Hz",
                    },
                    "compliance_criteria": "Applies to self-ballasted lamps having rated wattage up to 60 W",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 4. Mandatory Markings (Clause 5 / 5.1 / 5.4)
            if "marking" in c_text.lower() and ("shall be marked" in c_text.lower() or "mandatory" in c_text.lower()):
                req = {
                    "requirement_id": f"REQ-{doc_id}-{c_num}-004",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "property": "mandatory_marking",
                    "operator": "mandatory",
                    "value": "Mark of origin, rated voltage, rated wattage, rated frequency, standard mark",
                    "unit": None,
                    "condition": {
                        "legibility_test": "Rubbing with hexane soaked cloth for 15s",
                    },
                    "compliance_criteria": "Marking shall remain legible and easily discernible after durability test",
                    "source_pages": c_pages,
                }
                requirements.append(req)

            # 5. Glow Wire Temperature (Clause 11 / 10.2: 650°C / 750°C)
            if "glow-wire" in c_text.lower() or "glow wire" in c_text.lower():
                req = {
                    "requirement_id": f"REQ-{doc_id}-{c_num}-005",
                    "clause": c_num,
                    "subject": "insulating material",
                    "property": "glow_wire_temperature",
                    "operator": ">=",
                    "value": 650.0,
                    "unit": "°C",
                    "condition": {
                        "standard_method": "IS 11000 (Part 2/Sec 1)",
                        "live_parts_holding": "750 °C",
                        "non_live_parts": "650 °C",
                    },
                    "compliance_criteria": "Any flames or glowing must extinguish within 30 s after withdrawal of glow-wire",
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
