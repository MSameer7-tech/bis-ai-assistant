"""
Deterministic Knowledge Entity Extractor for Indian Standards and Regulations.
Extracts products, standards, parameters, values, test methods, thresholds,
lamp caps, referenced standards, and compliance rules with strict provenance.
"""

import logging
import re
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

# Entity regex patterns
STANDARD_REF_PATTERN = re.compile(
    r"\b(IS(?:/IEC)?\s+[0-9]{3,6}(?:\s*\([^\)\n]+\))?(?:\s*:\s*[0-9]{4})?)\b",
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

TEMPERATURE_PATTERN = re.compile(
    r"(\b[0-9]+(?:\.[0-9]+)?\s*°C\b)",
    re.IGNORECASE,
)

SAMPLING_PATTERN = re.compile(
    r"\b(ITQ|initial test quantity|batch size|sample size)\s*(?:=|is|of)?\s*([0-9]+(?:\s*lamps?)?)\b",
    re.IGNORECASE,
)


class EntityExtractor:
    """Extracts typed domain entities from normalized clause and page content."""

    def extract_entities_from_document(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts typed entities across all pages and clauses in the document.
        Maintains source_clause and source_pages provenance on every entity.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        entities: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def add_entity(entity_type: str, name: str, value: Any, clause_num: str, pages: List[int], extra: Dict[str, Any] = None):
            dedup_key = f"{entity_type}:{name}:{clause_num}"
            if dedup_key in seen_keys:
                return
            seen_keys.add(dedup_key)

            record = {
                "entity_id": f"ENT-{doc_id}-{len(entities) + 1:04d}",
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

        # 1. Document Level Entities
        doc_meta = processed_doc.get("document_metadata", {})
        if doc_meta.get("standard_number"):
            add_entity("standard", doc_meta["standard_number"], doc_meta["title"], "0", [1])
        if "Self-Ballasted LED" in doc_meta.get("title", ""):
            add_entity("product", "Self-Ballasted LED Lamp", "Self-Ballasted LED Lamps for General Lighting Services", "1", [1])

        # 2. Iterate through flat clauses
        def traverse_clauses(clause_list: List[Dict[str, Any]]):
            for c in clause_list:
                c_num = c.get("clause_number", "0")
                c_pages = c.get("page_refs", [c.get("page_start", 1)])
                c_text = c.get("content", "")

                # Referenced Standards
                for ref_match in STANDARD_REF_PATTERN.finditer(c_text):
                    ref_std = ref_match.group(1).strip()
                    if ref_std != doc_meta.get("standard_number"):
                        add_entity("referenced_standard", ref_std, ref_std, c_num, c_pages)

                # Lamp Caps
                for cap_match in LAMP_CAP_PATTERN.finditer(c_text):
                    cap_name = cap_match.group(1).upper()
                    add_entity("lamp_cap", cap_name, cap_name, c_num, c_pages)

                # Voltages
                for v_match in VOLTAGE_PATTERN.finditer(c_text):
                    v_val = v_match.group(1).strip()
                    add_entity("parameter", "voltage", v_val, c_num, c_pages, {"unit": "V"})

                # Wattages
                for w_match in WATTAGE_PATTERN.finditer(c_text):
                    w_val = w_match.group(1).strip()
                    add_entity("parameter", "wattage", w_val, c_num, c_pages, {"unit": "W"})

                # Resistance / Thresholds
                for r_match in RESISTANCE_PATTERN.finditer(c_text):
                    r_val = r_match.group(1).strip()
                    add_entity("threshold", "insulation_resistance", r_val, c_num, c_pages)

                # Torques
                for t_match in TORQUE_PATTERN.finditer(c_text):
                    t_val = t_match.group(1).strip()
                    add_entity("threshold", "mechanical_torque", t_val, c_num, c_pages, {"unit": "Nm"})

                # Temperatures
                for temp_match in TEMPERATURE_PATTERN.finditer(c_text):
                    temp_val = temp_match.group(1).strip()
                    add_entity("parameter", "temperature", temp_val, c_num, c_pages, {"unit": "°C"})

                # Sampling rules
                for samp_match in SAMPLING_PATTERN.finditer(c_text):
                    samp_rule = samp_match.group(0).strip()
                    add_entity("sampling_rule", samp_match.group(1).upper(), samp_rule, c_num, c_pages)

                # Recursively process subclauses
                if c.get("subclauses"):
                    traverse_clauses(c["subclauses"])

        traverse_clauses(processed_doc.get("clauses", []))

        # 3. Annex Entities
        for annex in processed_doc.get("annexes", []):
            add_entity("annex", annex["annex_id"], annex.get("title"), annex["annex_id"], annex.get("page_refs", [annex.get("page_start", 1)]))

        logger.info("Extracted %d typed entities from %s", len(entities), doc_id)
        return entities
