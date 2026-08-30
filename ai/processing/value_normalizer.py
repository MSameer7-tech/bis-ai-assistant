"""
Value and Unit Normalizer for Phase 2D.
Parses natural language numeric expressions, ranges, and tolerances into canonical
representations while preserving the exact original expression string.
"""

import re
from typing import Any, Dict, Optional

# Regex Patterns for Value Parsing
TOLERANCE_TEMP_REGEX = re.compile(
    r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*[\±\+\/\-]\s*([0-9]+(?:\.[0-9]+)?)\s*\)\s*°?C",
    re.IGNORECASE,
)

RANGE_REGEX = re.compile(
    r"(?:between\s+)?([0-9]+(?:\.[0-9]+)?)\s*(?:and|to|[\-–])\s*([0-9]+(?:\.[0-9]+)?)\s*(%|°C|V|W|MΩ|kΩ|Ω|Nm|K|h|min|s|percent|hours?|minutes?|seconds?)(?:$|\s|\b)",
    re.IGNORECASE,
)

NUMERIC_UNIT_REGEX = re.compile(
    r"([0-9]+(?:\s+[0-9]+)*(?:\.[0-9]+)?)\s*(MΩ|kΩ|Ω|Mohm|ohm|V|kV|W|kW|Nm|K|°C|Hz|kHz|percent|%|h|hours?|min|minutes?|s|seconds?|kg|g|mm|cm|m)(?:$|\s|\b)",
    re.IGNORECASE,
)


class ValueNormalizer:
    """Normalizes raw technical text into canonical values and structured units."""

    def normalize_value_expression(self, text: str) -> Dict[str, Any]:
        """
        Normalizes a technical value string while preserving 'original_value'.
        Handles tolerances like (25 ± 5)°C, ranges like 91-95%, and spaced numbers like 1 000 V.
        """
        clean_text = text.strip()

        # 1. Tolerance temperature e.g. (25 ± 5)°C
        tol_match = TOLERANCE_TEMP_REGEX.search(clean_text)
        if tol_match:
            nom = float(tol_match.group(1))
            tol = float(tol_match.group(2))
            return {
                "original_value": clean_text,
                "normalized": {
                    "nominal": int(nom) if nom.is_integer() else nom,
                    "tolerance": int(tol) if tol.is_integer() else tol,
                    "unit": "°C",
                },
                "status": "mandatory",
            }

        # 2. Range e.g. 91 to 95 % or 91-95 %
        range_match = RANGE_REGEX.search(clean_text)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            raw_unit = range_match.group(3).strip()
            unit_norm = "%" if raw_unit.lower() in ("percent", "%") else raw_unit
            return {
                "original_value": clean_text,
                "normalized": {
                    "min": int(min_val) if min_val.is_integer() else min_val,
                    "max": int(max_val) if max_val.is_integer() else max_val,
                    "unit": unit_norm,
                },
                "status": "mandatory",
            }

        # 3. Numeric with unit e.g. 1 000 V, 48 h, 1 min
        num_match = NUMERIC_UNIT_REGEX.search(clean_text)
        if num_match:
            raw_num_str = num_match.group(1).replace(" ", "")
            raw_unit = num_match.group(2).strip()

            val = float(raw_num_str) if "." in raw_num_str else int(raw_num_str)

            # Canonical Unit Mapping
            unit_map = {
                "percent": "%",
                "mohm": "MΩ",
                "ohm": "Ω",
                "hours": "h",
                "hour": "h",
                "minutes": "min",
                "minute": "min",
                "seconds": "s",
                "second": "s",
            }
            canonical_unit = unit_map.get(raw_unit.lower(), raw_unit)

            status = "under_consideration" if "under consideration" in clean_text.lower() else "mandatory"

            return {
                "original_value": clean_text,
                "normalized": {
                    "value": val,
                    "unit": canonical_unit,
                },
                "status": status,
            }

        status = "under_consideration" if "under consideration" in clean_text.lower() else "mandatory"
        return {
            "original_value": clean_text,
            "normalized": {
                "raw": clean_text,
            },
            "status": status,
        }


def normalize_value(text: str) -> Dict[str, Any]:
    """Convenience helper to normalize a value expression."""
    normalizer = ValueNormalizer()
    return normalizer.normalize_value_expression(text)
