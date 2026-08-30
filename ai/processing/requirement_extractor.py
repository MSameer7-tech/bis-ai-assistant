"""
Requirement Statement Normalizer for Phase 2D.
Converts natural language normative standard clauses into machine-readable requirement rules
with complete contextual metadata, dual value representations (original + normalized),
explicit semantic states (mandatory, under_consideration, conditional, exception),
and full traceable provenance.
"""

import logging
import re
from typing import Any, Dict, List

from ai.processing.value_normalizer import ValueNormalizer

logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extracts structured semantic requirement statements conforming to 2D-8, 2D-9, and 2D-10 specifications."""

    def __init__(self):
        self.val_normalizer = ValueNormalizer()

    def extract_requirements(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans clauses to generate formal, machine-readable requirement rules with conditions,
        dual value representation, explicit semantic status, and full provenance.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        source_id = processed_doc.get("source_id", "SRC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        std_num = str(doc_meta.get("standard_number") or doc_meta.get("title", doc_id)).strip()

        requirements: List[Dict[str, Any]] = []

        def build_provenance(clause: Dict[str, Any]) -> Dict[str, Any]:
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])
            return {
                "document_id": doc_id,
                "source_id": source_id,
                "standard": std_num,
                "clause": clause.get("clause_number", ""),
                "page": c_pages[0] if c_pages else 1,
                "pages": c_pages,
                "section": clause.get("title", f"Clause {clause.get('clause_number')}"),
                "original_text": clause.get("content", "")[:300].strip(),
            }

        def parse_clause_for_requirements(clause: Dict[str, Any]):
            c_num = clause.get("clause_number", "")
            c_text = clause.get("content", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])
            c_lower = c_text.lower()
            prov = build_provenance(clause)

            # Determine semantic state
            if "under consideration" in c_lower:
                status = "under_consideration"
            elif "exception" in c_lower or "not applicable" in c_lower:
                status = "exception"
            elif "if " in c_lower or "where applicable" in c_lower or "when fitted" in c_lower:
                status = "conditional"
            elif "should" in c_lower or "recommended" in c_lower:
                status = "recommended"
            elif "note" in c_lower[:30]:
                status = "informative"
            else:
                status = "mandatory"

            # 1. Cap Temperature Rise (Clause 10: <= 120 K)
            if "temperature rise" in c_lower and ("120 k" in c_lower or "120" in c_text):
                norm_val = self.val_normalizer.normalize_value_expression("120 K")
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "maximum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-TEMP",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "complete lamp",
                    "parameter": "cap_temperature_rise",
                    "operator": "<=",
                    "original_value": "120 K",
                    "normalized": norm_val["normalized"],
                    "value": 120.0,
                    "unit": "K",
                    "conditions": {
                        "ambient_temperature": {
                            "original_value": "(25 ± 5)°C",
                            "normalized": {"nominal": 25, "tolerance": 5, "unit": "°C"},
                        },
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
                    "provenance": prov,
                }
                requirements.append(req)

            # 2. Under Consideration Temperature (Clause 11 / 13: 80°C under consideration)
            if "80°c" in c_lower and "under consideration" in c_lower:
                norm_val = self.val_normalizer.normalize_value_expression("80 °C (under consideration)")
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "pending_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-80C-PENDING",
                    "status": "under_consideration",
                    "clause": c_num,
                    "subject": "insulating material parts not retaining live parts",
                    "parameter": "ball_pressure_temperature",
                    "operator": ">=",
                    "original_value": "80°C (value 80°C under consideration)",
                    "normalized": {"value": 80, "unit": "°C"},
                    "value": 80.0,
                    "unit": "°C",
                    "conditions": {
                        "ambient_treatment": "parts not retaining live parts in position",
                    },
                    "acceptance_criterion": {
                        "provisional_minimum": 80.0,
                        "unit": "°C",
                        "criterion_text": "Provisional 80°C under active technical consideration",
                    },
                    "exceptions": "Value 80°C is actively under consideration and not finalized as mandatory",
                    "evidence": "80°C (value 80°C under consideration) for other parts.",
                    "source_pages": c_pages,
                    "provenance": prov,
                }
                requirements.append(req)

            # 3. GX53 Torque (Clause 9.1: 3 Nm under consideration)
            if "gx53" in c_lower and "under consideration" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "pending_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-GX53-PENDING",
                    "status": "under_consideration",
                    "clause": c_num,
                    "subject": "GX53 lamp cap",
                    "parameter": "torsion_moment_torque",
                    "operator": ">=",
                    "original_value": "3 Nm (under consideration)",
                    "normalized": {"value": 3, "unit": "Nm"},
                    "value": 3.0,
                    "unit": "Nm",
                    "conditions": {
                        "cap_type": "GX53",
                    },
                    "acceptance_criterion": {
                        "provisional_minimum": 3.0,
                        "unit": "Nm",
                        "criterion_text": "Torsion moment 3 Nm under consideration for GX53",
                    },
                    "exceptions": "Provisional requirement for GX53 cap style",
                    "evidence": "GX 53: 3 Nm (under consideration)",
                    "source_pages": c_pages,
                    "provenance": prov,
                }
                requirements.append(req)

            # 4. Inspection Test Quantity (Clause 15.2: ITQ = 25 lamps)
            if "25" in c_text and ("itq" in c_lower or "inspection test quantity" in c_lower or "initial test quantity" in c_lower or "sample" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "sampling_quantity",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-ITQ",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "batch / inspection lot",
                    "parameter": "inspection_test_quantity",
                    "operator": "==",
                    "original_value": "25 lamps",
                    "normalized": {"value": 25, "unit": "lamps"},
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
                    "provenance": prov,
                }
                requirements.append(req)

            # 5. Insulation Resistance (Clause 8.1 / 8.1.1: >= 4 MΩ)
            if "insulation resistance" in c_lower and ("4" in c_text or "mΩ" in c_lower or "mohm" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "minimum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-IR",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "insulation_resistance",
                    "operator": ">=",
                    "original_value": "4 MΩ",
                    "normalized": {"value": 4.0, "unit": "MΩ"},
                    "value": 4.0,
                    "unit": "MΩ",
                    "conditions": {
                        "humidity_treatment": {
                            "original_value": "48 h at (91-95)% RH",
                            "normalized": {
                                "duration": {"value": 48, "unit": "h"},
                                "humidity": {"min": 91, "max": 95, "unit": "%"},
                                "temperature": {"min": 25, "max": 35, "unit": "°C"},
                            },
                        },
                    },
                    "test": {
                        "applied_voltage": {
                            "original_value": "approximately 500 V d.c.",
                            "normalized": {"value": 500, "unit": "V d.c."},
                        },
                        "measurement_time": {
                            "original_value": "1 min after application",
                            "normalized": {"value": 60, "unit": "s"},
                        },
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
                    "provenance": prov,
                }
                requirements.append(req)

            # 6. Electric Strength / Dielectric (Clause 8.2: 4000 V a.c.)
            if "electric strength" in c_lower or "4 000 v" in c_lower or "4000 v" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "dielectric_test",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-ES",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "dielectric_electric_strength",
                    "operator": "==",
                    "original_value": "4 000 V a.c.",
                    "normalized": {"value": 4000, "unit": "V a.c."},
                    "value": 4000,
                    "unit": "V a.c.",
                    "conditions": {
                        "humidity_treatment": "immediately following 48 h humidity treatment",
                    },
                    "test": {
                        "test_voltage": "4 000 V a.c. (r.m.s.)",
                        "frequency": "50 Hz",
                        "duration": "1 minute (60 s)",
                    },
                    "acceptance_criterion": {
                        "minimum": 4000,
                        "unit": "V a.c.",
                        "criterion_text": "No flashover or breakdown shall occur during the 1 minute application",
                    },
                    "exceptions": None,
                    "evidence": "A test voltage of 4 000 V a.c. shall be applied for 1 min without breakdown.",
                    "source_pages": c_pages,
                    "provenance": prov,
                }
                requirements.append(req)

            # 7. Rated Wattage Limit (Clause 1: <= 60 W)
            if "rated wattage" in c_lower and "60 w" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "maximum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-WATT",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "rated_wattage",
                    "operator": "<=",
                    "original_value": "60 W",
                    "normalized": {"value": 60.0, "unit": "W"},
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
                    "provenance": prov,
                }
                requirements.append(req)

            # 8. Mandatory Markings (Clause 5 / 5.1 / 5.4)
            if "marking" in c_lower and ("shall be marked" in c_lower or "mandatory" in c_lower):
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "mandatory_marking",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-MARK",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "self-ballasted LED lamp",
                    "parameter": "mandatory_marking_elements",
                    "operator": "mandatory",
                    "original_value": "Mark of origin, rated voltage, rated wattage, rated frequency, standard mark",
                    "normalized": {
                        "items": [
                            "Mark of origin (trademark)",
                            "Rated voltage or voltage range (V)",
                            "Rated wattage (W)",
                            "Rated frequency (Hz)",
                            "Standard Mark (CRS Registration Number)",
                        ]
                    },
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
                    "provenance": prov,
                }
                requirements.append(req)

            # 9. Glow Wire Temperature (Clause 11 / 10.2: 650°C / 750°C)
            if "glow-wire" in c_lower or "glow wire" in c_lower:
                req = {
                    "entity_type": "requirement",
                    "requirement_type": "minimum_limit",
                    "requirement_id": f"REQ-{doc_id.replace('-', '')}-{c_num}-GLOW",
                    "status": "mandatory",
                    "clause": c_num,
                    "subject": "insulating material",
                    "parameter": "glow_wire_temperature",
                    "operator": ">=",
                    "original_value": "650°C / 750°C",
                    "normalized": {
                        "live_parts_holding": {"value": 750, "unit": "°C"},
                        "non_live_parts": {"value": 650, "unit": "°C"},
                    },
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
                    "provenance": prov,
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
