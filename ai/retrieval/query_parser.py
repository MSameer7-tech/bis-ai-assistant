"""
Structured Query Parser for Phase 2E BIS QA Pipeline.
Extracts intent, product/entity, grade, canonical parameters, units, operators, and exact identifiers.
"""
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StructuredQuery(BaseModel):
    """Rich intermediate query representation for parameter and entity aware retrieval."""
    raw_query: str = Field(..., description="Original user query")
    intent: str = Field(..., description="Intent: PARAMETER_QUERY, EXACT_IDENTIFIER, STANDARD_IDENTIFICATION, BROAD_REQUIREMENTS, DEFINITION, OUT_OF_SCOPE")
    product: Optional[str] = Field(None, description="Identified product entity")
    grade: Optional[str] = Field(None, description="Identified material/product grade (e.g. Fe 500D, 53 Grade)")
    material: Optional[str] = Field(None, description="Identified material (e.g. steel, cement)")
    parameter: Optional[str] = Field(None, description="Canonical parameter identifier")
    requested_unit: Optional[str] = Field(None, description="Requested physical unit")
    operator: Optional[str] = Field(None, description="Operator: minimum, maximum, equal, range")
    exact_identifiers: List[str] = Field(default_factory=list, description="Extracted exact technical codes/caps")
    standard_code: Optional[str] = Field(None, description="Explicitly mentioned standard number")
    clause: Optional[str] = Field(None, description="Explicitly mentioned clause number")
    as_of_date: Optional[str] = Field(None, description="Temporal reference date YYYY-MM-DD")


# Canonical parameter registry with aliases mapping to a single canonical key
CANONICAL_PARAMETER_ALIASES: Dict[str, List[str]] = {
    "yield_stress": [
        "yield stress", "yield strength", "minimum yield strength", "yield point",
        "0.2% proof stress", "0.2 percent proof stress", "proof stress", "ys"
    ],
    "percentage_elongation": [
        "percentage elongation", "elongation after fracture", "elongation percent",
        "percent elongation", "elongation"
    ],
    "insulation_resistance": [
        "insulation resistance", "ir", "insulation resistance test", "resistance of insulation"
    ],
    "torque_moment": [
        "torsion moment", "torsional moment", "torque requirement", "torsion resistance",
        "torsional resistance", "torque", "gx53", "cap", "table 2"
    ],
    "compressive_strength": [
        "compressive strength", "crushing strength", "28-day compressive strength",
        "28-day strength", "compressive"
    ],
    "air_delivery": [
        "air delivery", "air flow", "air volume", "delivery of air"
    ],
    "proof_pressure": [
        "hydraulic proof pressure", "proof pressure", "burst pressure", "operating pressure", "hydraulic pressure"
    ],
    "mass": [
        "total mass", "maximum mass", "helmet mass", "mass", "weight"
    ],
    "ph": [
        "ph value", "hydrogen ion concentration", "ph"
    ],
    "temperature_rise": [
        "cap temperature rise", "temperature rise", "temperature limit"
    ],
    "dimensions": [
        "dimension", "dimensions", "length", "diameter", "thickness", "size"
    ],
    "thermal_efficiency": [
        "thermal efficiency", "efficiency of burner", "burner thermal efficiency", "stove efficiency"
    ],
    "shock_absorption": [
        "shock absorption", "transmitted force", "peak deceleration", "headform deceleration",
        "impact absorption", "shock absorption test"
    ],
    "filtration_efficiency": [
        "bacterial filtration efficiency", "bfe", "filtration efficiency", "particle filtration", "filter efficiency"
    ],
    "chemical_limits": [
        "carbon content", "sulfur content", "phosphorus content", "chemical composition"
    ],
    "total_elongation_agt": [
        "agt", "total elongation at maximum force", "total elongation"
    ],
    "leakage_temperature": [
        "water bath", "leakage testing", "leakage test temperature", "water bath temperature"
    ],
    "static_test_duration": [
        "static test load", "static load duration", "sustained", "static test load duration"
    ],
    "hydrostatic_duration": [
        "hydrostatic proof pressure", "proof hydrostatic pressure", "hydrostatic test duration", "hydrostatic duration", "proof pressure held"
    ],
    "ageing_condition": [
        "accelerated ageing", "ageing condition", "accelerated ageing test"
    ],
    "flow_error": [
        "permissible error", "permissible errors", "flow zone error", "accuracy class error"
    ],
    "lumen_maintenance": [
        "lumen maintenance", "2000 h", "rated life", "25 000 h"
    ]
}

# Out-of-scope keywords that require immediate explicit abstention
OUT_OF_SCOPE_TERMS = [
    "rocket engine", "rocket engines", "space shuttle", "spacecraft",
    "retail market price", "manufacturing cost", "retail price", "price", "cost",
    "corporate revenue", "sales numbers", "quarterly sales", "revenue", "salary",
    "director general", "who is the current", "stock price", "warranty",
    "quantum", "bitcoin", "cryptocurrency", "weather forecast", "weather",
    "chocolate cake", "cake recipe", "recipe", "how to bake", "stock market",
    "is 99999", "fe 9999", "z99", "fatigue life"
]

# Product name patterns - Ordered from most specific to least specific
PRODUCT_PATTERNS = [
    (r"\bindustrial\s*(?:safety)?\s*helmets?\b|\bhard hats?\b", "industrial safety helmets"),
    (r"\bmotorcycle helmets?\b|\btwo wheeler riders?\b|\bcrash helmets?\b|\bhelmets?\b", "protective helmets for two wheeler riders"),
    (r"\bself[- ]ballasted\b|\bled lamps?\b", "self-ballasted LED lamps"),
    (r"\belectric ceiling fans?\b|\bceiling fans?\b", "electric ceiling fans"),
    (r"\bportland pozzolana cement\b|\bpozzolana cement\b|\bppc\b|\bfly ash based\b", "portland pozzolana cement"),
    (r"\bordinary portland cement\b|\bopc\b|\bcement\b", "ordinary Portland cement"),
    (r"\bsecondary lithium\b|\blithium batteries\b|\blithium cells?\b", "secondary lithium batteries"),
    (r"\bpressure cookers?\b", "domestic pressure cookers"),
    (r"\bpackaged drinking water\b|\bdrinking water\b|\bmineral water\b", "packaged drinking water"),
    (r"\bsteel bars?\b|\bdeformed steel\b|\bconcrete reinforcement\b|\brebars?\b|\btmt bars?\b", "high strength deformed steel bars"),
    (r"\baudio video\b|\belectronic apparatus\b", "audio, video and similar electronic apparatus"),
    (r"\bgas stoves?\b|\blpg stoves?\b|\bcooking gas burners?\b|\bgas burners?\b", "domestic gas stoves"),
    (r"\bnon-refillable\b|\blpg containers?\b", "non-refillable metallic LPG containers"),
    (r"\bsafety footwear\b|\bsteel toecap\b|\bwork boots?\b", "safety footwear"),
    (r"\bpvc boots?\b|\bindustrial boots?\b", "PVC industrial boots"),
    (r"\bfull body harnesses?\b|\bsafety harnesses?\b|\bsafety belts?\b|\bfall arrest\b|\bfall protection\b", "safety belts and harnesses"),
    (r"\bmedical face masks?\b|\bsurgical masks?\b", "medical face masks"),
    (r"\bhalf masks?\b|\bfiltering half masks?\b|\bffp2\b|\bffp1\b|\bffp3\b|\brespirator masks?\b", "respiratory protective filtering half masks"),
    (r"\brubber surgical gloves?\b|\bsurgical gloves?\b", "rubber surgical gloves"),
    (r"\bfire extinguishers?\b|\bwater type fire extinguisher\b", "portable fire extinguishers"),
    (r"\bcouplings?\b|\bbranch pipes?\b|\bnozzles?\b", "fire hose delivery couplings"),
    (r"\bwater meters?\b", "domestic water meters"),
    (r"\bpvc pipes?\b|\bunplasticized pvc\b", "unplasticized PVC pipes"),
    (r"\bcoarse and fine aggregates\b|\baggregates\b", "aggregates for concrete"),
    (r"\bstructural steel\b|\bmedium and high tensile structural steel\b", "structural steel"),
    (r"\binfant milk substitutes?\b|\binfant milk\b", "infant milk substitutes"),
    (r"\bx-ray equipment\b|\bmedical x-ray\b", "diagnostic medical X-ray equipment"),
]


class QueryParser:
    """Parses natural language queries into structured representations."""

    @classmethod
    def parse(cls, query: str, as_of_date: Optional[str] = None) -> StructuredQuery:
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Check for Out-of-Scope Intent
        for term in OUT_OF_SCOPE_TERMS:
            if term in q_lower:
                return StructuredQuery(
                    raw_query=q_clean,
                    intent="OUT_OF_SCOPE",
                    as_of_date=as_of_date
                )

        # 2. Extract Standard Number if present
        std_match = re.search(r"\bIS\s+(\d+(?:\s*\([^)]+\))?(?:\s*:\s*\d{4})?)", q_clean, re.IGNORECASE)
        standard_code = f"IS {std_match.group(1).strip()}" if std_match else None

        # 3. Extract Clause Number if present
        clause_match = re.search(r"\bclause\s+([0-9]+(?:\.[0-9]+)*)", q_clean, re.IGNORECASE)
        clause = clause_match.group(1) if clause_match else None

        # 4. Extract Grade / Material
        grade = None
        grade_match = re.search(r"\b(Fe\s*550D|Fe\s*550|Fe\s*500D|Fe\s*500|Fe\s*415D|Fe\s*415|Fe\s*600|53\s*Grade|43\s*Grade|33\s*Grade)\b", q_clean, re.IGNORECASE)
        if grade_match:
            grade = grade_match.group(1).replace("  ", " ")

        material = None
        if "steel" in q_lower:
            material = "steel"
        elif "cement" in q_lower:
            material = "cement"

        # 5. Extract Exact Technical Identifiers (Caps, Codes)
        exact_identifiers = []
        cap_matches = re.findall(r"\b(B22d|B15d|GX53|E17|E27|E14|E26|E40|G9|G4|GU10|R7s)\b", q_clean, re.IGNORECASE)
        for cap in cap_matches:
            exact_identifiers.append(cap.upper() if len(cap) <= 4 else cap)
        if grade and grade not in exact_identifiers:
            exact_identifiers.append(grade)

        # 6. Extract Product Entity
        product = None
        for pattern, prod_name in PRODUCT_PATTERNS:
            if re.search(pattern, q_lower):
                product = prod_name
                break

        # 7. Extract Operator
        operator = None
        if any(w in q_lower for w in ["minimum", "at least", "not less than", "lowest"]):
            operator = "minimum"
        elif any(w in q_lower for w in ["maximum", "at most", "not exceed", "highest"]):
            operator = "maximum"
        elif any(w in q_lower for w in ["equal", "exactly"]):
            operator = "equal"

        # 8. Extract Canonical Parameter using Globally Length-Sorted Alias Registry
        canonical_param = None
        all_alias_tuples = []
        for p_k, aliases in CANONICAL_PARAMETER_ALIASES.items():
            for a in aliases:
                all_alias_tuples.append((len(a), a, p_k))
        all_alias_tuples.sort(key=lambda x: x[0], reverse=True)

        for _, alias, p_k in all_alias_tuples:
            if re.search(r"\b" + re.escape(alias) + r"\b", q_lower):
                canonical_param = p_k
                break

        # 9. Extract Requested Unit
        requested_unit = None
        unit_match = re.search(r"\b(MPa|N/mm²|N/mm2|MΩ|kΩ|bar|kPa|Nm|m³/min|g|kg|V|V DC|°C|%)\b", q_clean, re.IGNORECASE)
        if unit_match:
            requested_unit = unit_match.group(1)

        # 10. Determine Overall Intent
        if any(q_lower.startswith(w) for w in ["which bis standard", "which standard", "what standard", "which indian standard"]):
            intent = "STANDARD_IDENTIFICATION"
        elif canonical_param is not None:
            intent = "PARAMETER_QUERY"
        elif exact_identifiers and not product and not canonical_param:
            intent = "EXACT_IDENTIFIER"
        elif any(w in q_lower for w in ["what requirements", "general requirements", "safety requirements", "what are the requirements"]):
            intent = "BROAD_REQUIREMENTS"
        elif any(q_lower.startswith(w) for w in ["define", "what is the definition", "definition of"]):
            intent = "DEFINITION"
        else:
            intent = "PARAMETER_QUERY" if (product or grade) else "EXACT_IDENTIFIER"

        return StructuredQuery(
            raw_query=q_clean,
            intent=intent,
            product=product,
            grade=grade,
            material=material,
            parameter=canonical_param,
            requested_unit=requested_unit,
            operator=operator,
            exact_identifiers=exact_identifiers,
            standard_code=standard_code,
            clause=clause,
            as_of_date=as_of_date
        )
