"""
Deterministic Knowledge Entity Extractor for Indian Standards and Regulations.
Extracts 7 core entity families:
A. Standards (IS / IEC standards)
B. Products (Self-ballasted LED lamp, Lamp cap, Controlgear)
C. Technical Parameters (Insulation resistance, Cap temperature rise, Bending moment, Torque, etc.)
D. Values & Units (60 W, 250 V, 4 MΩ, 120 K, 48 h, 91-95%, 25 lamps)
E. Components & Lamp Caps (B15d, B22d, E11, E12, E14, E17, E26, E27, GU10, GX53)
F. Tests (Insulation resistance test, Electric strength test, Torsion test, Ball-pressure test, Glow-wire test, etc.)
G. Authorities (Bureau of Indian Standards, MeitY, IEC)
"""

import logging
import re
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

# Regex Patterns
STANDARD_REF_PATTERN = re.compile(
    r"\b((?:IS(?:/IEC)?|IEC)\s+[0-9]{3,6}(?:\s*\([^\)\n]+\))?(?:\s*:\s*[0-9]{4})?)\b",
    re.IGNORECASE,
)

LAMP_CAP_PATTERN = re.compile(
    r"\b(B15d?|B22d?|E10|E11|E12|E14|E17|E26d?|E27|GU10|GZ10|GX53)\b",
    re.IGNORECASE,
)

VOLTAGE_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*(?:V|kV)\s*(?:a\.?c\.?|d\.?c\.?|r\.?m\.?s\.?)?)\b",
    re.IGNORECASE,
)

WATTAGE_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*W\b)",
    re.IGNORECASE,
)

RESISTANCE_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*(?:MΩ|kΩ|Ω|Mohm|ohm))\b",
    re.IGNORECASE,
)

TORQUE_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*Nm\b)",
    re.IGNORECASE,
)

TEMP_KELVIN_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*K\b)",
)

TEMP_CELSIUS_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*°C\b)",
    re.IGNORECASE,
)

HUMIDITY_PATTERN = re.compile(
    r"([0-9]{1,2}(?:\s*[\-–to]\s*[0-9]{1,2})?\s*%\s*(?:RH|relative humidity)?)",
    re.IGNORECASE,
)

SAMPLING_PATTERN = re.compile(
    r"\b(ITQ|initial test quantity|inspection test quantity|batch size|sample size)\s*(?:=|is|of)?\s*([0-9]+(?:\s*lamps?)?)\b",
    re.IGNORECASE,
)

TEST_NAME_PATTERNS = [
    ("insulation_resistance_test", re.compile(r"\binsulation resistance\b", re.IGNORECASE)),
    ("electric_strength_test", re.compile(r"\belectric strength\b|\bdielectric\b", re.IGNORECASE)),
    ("torsion_test", re.compile(r"\btorsion test\b|\btorque test\b|\bmechanical strength\b", re.IGNORECASE)),
    ("ball_pressure_test", re.compile(r"\bball[- ]pressure test\b", re.IGNORECASE)),
    ("glow_wire_test", re.compile(r"\bglow[- ]wire test\b", re.IGNORECASE)),
    ("cap_temperature_rise_test", re.compile(r"\bcap temperature rise\b", re.IGNORECASE)),
    ("fault_condition_test", re.compile(r"\bfault conditions?\b", re.IGNORECASE)),
    ("marking_durability_test", re.compile(r"\brubbing.*hexane\b|\bmarking durability\b", re.IGNORECASE)),
]


class EntityExtractor:
    """Extracts typed domain entities across 7 families from normalized clauses and metadata."""

    def extract_entities_from_document(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts typed entities across all pages and clauses in the document.
        Maintains source_clause and source_pages provenance on every entity.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        entities: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def add_entity(entity_type: str, name: str, value: Any, clause_num: str, pages: List[int], extra: Dict[str, Any] = None):
            dedup_key = f"{entity_type}:{str(name).strip().upper()}:{clause_num}"
            if dedup_key in seen_keys:
                return
            seen_keys.add(dedup_key)

            record = {
                "entity_id": f"ENT-{doc_id.replace('-', '')}-{len(entities) + 1:04d}",
                "entity_type": entity_type,
                "name": name,
                "value": value,
                "document_id": doc_id,
                "source_clause": clause_num,
                "source_pages": sorted(list(set(pages))),
            }
            if extra:
                record.update(extra)
            entities.append(record)

        # 1. Family A: Primary Standard & Family G: Authorities
        if doc_meta.get("standard_number"):
            add_entity("standard", doc_meta["standard_number"], doc_meta.get("title"), "0", [1])
        add_entity("authority", "Bureau of Indian Standards (BIS)", "National Standards Body of India", "0", [1])
        add_entity("authority", "Ministry of Electronics and Information Technology (MeitY)", "Statutory Order Authority", "0", [1])

        # 2. Family B: Products
        title_str = doc_meta.get("title", "")
        if "Self-Ballasted" in title_str or "16102" in str(doc_meta.get("standard_number", "")):
            add_entity("product", "Self-Ballasted LED Lamp", "Self-Ballasted LED Lamps for General Lighting Services", "1", [1])
            add_entity("component", "Lamp Cap", "Standard Lamp Fitment Cap", "6", [9])
        if "Controlgear" in title_str or "15885" in str(doc_meta.get("standard_number", "")):
            add_entity("product", "LED Controlgear", "d.c. or a.c. Supplied Electronic Controlgear for LED Modules", "1", [1])

        # 3. Iterate through flat clauses to populate Families A, C, D, E, F
        def traverse_clauses(clause_list: List[Dict[str, Any]]):
            for c in clause_list:
                c_num = c.get("clause_number", "0")
                c_pages = c.get("page_refs", [c.get("page_start", 1)])
                c_text = c.get("content", "")

                # Family A: Referenced Standards
                for ref_match in STANDARD_REF_PATTERN.finditer(c_text):
                    ref_std = ref_match.group(1).strip()
                    if ref_std.upper() != str(doc_meta.get("standard_number", "")).upper():
                        add_entity("referenced_standard", ref_std, ref_std, c_num, c_pages)

                # Family E: Components / Lamp Caps
                for cap_match in LAMP_CAP_PATTERN.finditer(c_text):
                    cap_name = cap_match.group(1).upper()
                    add_entity("lamp_cap", cap_name, cap_name, c_num, c_pages)

                # Family F: Tests
                for test_type, test_pat in TEST_NAME_PATTERNS:
                    if test_pat.search(c_text):
                        test_display_name = test_type.replace("_", " ").title()
                        add_entity("test", test_display_name, test_display_name, c_num, c_pages)

                # Family C & D: Technical Parameters & Values
                for v_match in VOLTAGE_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "voltage", v_match.group(1).strip(), c_num, c_pages, {"unit": "V"})

                for w_match in WATTAGE_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "wattage", w_match.group(1).strip(), c_num, c_pages, {"unit": "W"})

                for r_match in RESISTANCE_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "insulation_resistance", r_match.group(1).strip(), c_num, c_pages, {"unit": "MΩ"})

                for t_match in TORQUE_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "torque", t_match.group(1).strip(), c_num, c_pages, {"unit": "Nm"})

                for k_match in TEMP_KELVIN_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "temperature_rise", k_match.group(1).strip(), c_num, c_pages, {"unit": "K"})

                for c_temp_match in TEMP_CELSIUS_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "temperature", c_temp_match.group(1).strip(), c_num, c_pages, {"unit": "°C"})

                for h_match in HUMIDITY_PATTERN.finditer(c_text):
                    add_entity("value_and_unit", "humidity", h_match.group(1).strip(), c_num, c_pages, {"unit": "% RH"})

                for samp_match in SAMPLING_PATTERN.finditer(c_text):
                    add_entity("sampling_rule", samp_match.group(1).upper(), samp_match.group(0).strip(), c_num, c_pages)

                if c.get("subclauses"):
                    traverse_clauses(c["subclauses"])

        traverse_clauses(processed_doc.get("clauses", []))

        # Annex entities
        for annex in processed_doc.get("annexes", []):
            add_entity("annex", annex["annex_id"], annex.get("title"), annex["annex_id"], annex.get("page_refs", [annex.get("page_start", 1)]))

        logger.info("Extracted %d typed entities across 7 families for %s", len(entities), doc_id)
        return entities
