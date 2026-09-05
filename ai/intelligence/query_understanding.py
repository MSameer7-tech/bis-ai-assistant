"""
Multi-Intent & Canonical Entity Query Understanding Engine (Phase 5 Sub-Phase 5A).
Converts natural language user queries into rich, structured regulatory intent payloads.
"""
import re
from enum import Enum
from typing import List, Dict, Optional, Set, Any, Tuple
from pydantic import BaseModel, Field

from ai.acquisition.products.registry import ProductRegistry
from ai.acquisition.standards.registry import StandardsRegistry
from ai.acquisition.qco.registry import QCORegistry
from ai.acquisition.schemes.registry import SchemeRegistry
from ai.acquisition.hallmarking.registry import HallmarkRegistry
from ai.acquisition.consumer.registry import ConsumerRegistry
from ai.coverage.product_resolver import ProductResolver


class QueryIntent(str, Enum):
    """Canonical regulatory query intents under BIS ecosystem."""
    MANDATORY_STATUS = "MANDATORY_STATUS"            # "Is BIS certification mandatory?"
    CERTIFICATION_SCHEME = "CERTIFICATION_SCHEME"    # "Which scheme covers this (Scheme-I, Scheme-II)?"
    TESTING_REQUIREMENTS = "TESTING_REQUIREMENTS"    # "What tests are prescribed?"
    LABORATORY_LOOKUP = "LABORATORY_LOOKUP"          # "Which labs test this product?"
    SIT_SCHEDULE = "SIT_SCHEDULE"                    # "What is the Scheme of Inspection and Testing / sampling?"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"                # "What are the grouping / marking requirements in product manual?"
    LICENCE_CRS_STATUS = "LICENCE_CRS_STATUS"        # "Verify CM/L number or CRS R-number"
    HALLMARKING_PURITY = "HALLMARKING_PURITY"        # "Gold/Silver purity, AHC recognition, HUID validation"
    CONSUMER_COMPLAINT = "CONSUMER_COMPLAINT"        # "File complaint, 30-day SLA, Section 31 compensation"
    AMENDMENT_HISTORY = "AMENDMENT_HISTORY"          # "What amendments/revisions apply?"
    TECHNICAL_VALUE = "TECHNICAL_VALUE"              # "What is the minimum yield strength / efficiency?"
    GENERAL_KYS = "GENERAL_KYS"                      # "What is IS 374? / Overview of standard"


class ParsedQuery(BaseModel):
    """Structured representation of a parsed user query."""
    raw_query: str
    clean_query: str
    canonical_product: Optional[str] = None
    standard_code: Optional[str] = None
    intents: List[QueryIntent] = Field(default_factory=list)
    primary_intent: QueryIntent = QueryIntent.GENERAL_KYS
    temporal_target: Optional[str] = "current"
    as_of_date: Optional[str] = None
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    jurisdiction: str = "DOMESTIC_INDIA"
    scheme_hint: Optional[str] = None
    is_multi_hop: bool = False
    confidence: float = 0.9


class QueryUnderstandingEngine:
    """
    Parses and disambiguates natural language queries into machine-actionable regulatory payloads.
    """
    def __init__(self):
        self.ps_resolver = ProductResolver()
        self.prod_reg = ProductRegistry()
        self.std_reg = StandardsRegistry()
        self.qco_reg = QCORegistry()
        self.scheme_reg = SchemeRegistry()
        self.hallmark_reg = HallmarkRegistry()
        self.consumer_reg = ConsumerRegistry()

        # Regular expressions for entity resolution
        self.is_code_pattern = re.compile(
            r"\bIS\s*[:\-]?\s*(\d{2,5})(?:\s*(?:\(|Part\s*)(\d+)(?:\)|\/Sec\s*\d+)?)?(?:\s*:\s*(\d{4}))?(?!\s*-\s*digit)\b",
            re.IGNORECASE
        )
        self.cml_pattern = re.compile(r"\b(?:CM\s*/\s*L\s*[-–:]?\s*|CML\s*[-–:]?\s*)(\d{7,10})\b", re.IGNORECASE)
        self.r_num_pattern = re.compile(r"\b(?:R\s*[-–:]?\s*)(\d{8})\b", re.IGNORECASE)
        self.huid_pattern = re.compile(r"\b([A-Z0-9]{6})\b", re.IGNORECASE)

        # Keyword mapping for intents
        self.intent_keywords = {
            QueryIntent.MANDATORY_STATUS: [
                "mandatory", "compulsory", "required", "need bis", "need certification",
                "qco", "quality control order", "legal requirement", "statutory mandate",
                "can i sell without", "is it compulsory"
            ],
            QueryIntent.CERTIFICATION_SCHEME: [
                "scheme", "scheme-i", "scheme-ii", "scheme-iv", "isi mark", "crs",
                "compulsory registration", "tatkal", "simplified procedure", "normal procedure",
                "hallmark scheme", "certification path"
            ],
            QueryIntent.TESTING_REQUIREMENTS: [
                "test", "testing", "prescribed tests", "routine test", "type test",
                "acceptance test", "mechanical test", "chemical test", "tensile",
                "air delivery", "compressive strength", "thermal efficiency", "burst pressure"
            ],
            QueryIntent.LABORATORY_LOOKUP: [
                "laboratory", "lab", "testing facility", "accredited lab", "where to test",
                "bis recognized lab", "central laboratory", "regional lab", "testing centre"
            ],
            QueryIntent.SIT_SCHEDULE: [
                "sit", "scheme of inspection", "sampling frequency", "inspection schedule",
                "sample size", "control unit", "how often to test", "batch testing"
            ],
            QueryIntent.PRODUCT_MANUAL: [
                "product manual", "guidelines for conformity", "grouping guidelines",
                "raw material requirement", "marking requirements", "scope of licence"
            ],
            QueryIntent.LICENCE_CRS_STATUS: [
                "licence", "license", "cml", "cm/l", "r-number", "registration number",
                "check licence", "verify licence", "active licence", "licensee"
            ],
            QueryIntent.HALLMARKING_PURITY: [
                "hallmark", "hallmarking", "huid", "ahc", "purity", "22k", "24k", "18k",
                "14k", "916", "750", "585", "gold jewellery", "silver jewellery", "assaying"
            ],
            QueryIntent.CONSUMER_COMPLAINT: [
                "complaint", "grievance", "fake isi", "misuse", "section 31", "compensation",
                "bis care", "file complaint", "sla", "substandard", "penalty"
            ],
            QueryIntent.AMENDMENT_HISTORY: [
                "amendment", "amendments", "revision", "reaffirmed", "superseded",
                "withdrawn", "changes in", "latest edition", "history of standard"
            ],
            QueryIntent.TECHNICAL_VALUE: [
                "what is the value", "minimum", "maximum", "tolerance", "limit",
                "efficiency", "strength", "thickness", "dimension", "specification for"
            ]
        }

        # Parameter vocabulary
        self.parameter_keywords = {
            "air_delivery": ["air delivery", "m3/min", "service value", "cfm"],
            "insulation_resistance": ["insulation resistance", "megohms", "m ohm", "insulation"],
            "proof_stress": ["yield strength", "proof stress", "0.2% proof", "tensile stress", "n/mm2"],
            "tensile_strength": ["tensile strength", "ultimate tensile", "ts/ys"],
            "elongation": ["elongation", "percentage elongation"],
            "compressive_strength": ["compressive strength", "cube strength", "28 day strength", "mpa"],
            "setting_time": ["initial setting time", "final setting time", "setting time"],
            "thermal_efficiency": ["thermal efficiency", "efficiency %", "gas consumption"],
            "operating_pressure": ["operating pressure", "burst pressure", "proof pressure", "safety valve"],
            "impact_absorption": ["impact absorption", "peak acceleration", "headform", "300g"],
            "huid": ["huid", "hallmark unique id", "6 digit huid"],
            "purity_ppt": ["fineness", "parts per thousand", "karat", "karats", "22 karat", "24 karat"]
        }

    def parse_query(self, query: str, as_of_date: Optional[str] = None) -> ParsedQuery:
        """Parses raw text query into a rich ParsedQuery payload."""
        clean_q = query.strip()
        q_lower = clean_q.lower()

        extracted_entities: Dict[str, Any] = {}
        intents: List[QueryIntent] = []

        # 1. Standard Code Extraction
        standard_code = None
        is_match = self.is_code_pattern.search(clean_q)
        if is_match:
            main_num = is_match.group(1)
            part_num = is_match.group(2)
            year_num = is_match.group(3)
            if part_num:
                standard_code = f"IS {main_num} (Part {part_num})"
            else:
                standard_code = f"IS {main_num}"
            if year_num:
                extracted_entities["explicit_year"] = year_num
                extracted_entities["full_standard_code"] = f"{standard_code} : {year_num}"
            extracted_entities["standard_number"] = standard_code

        # 2. Authoritative Problem Statement (PS) Product Resolution
        canonical_product = None
        ps_match = self.ps_resolver.resolve_from_query(clean_q)
        if ps_match:
            canonical_product = ps_match.product.canonical_name
            if not standard_code:
                standard_code = ps_match.product.canonical_standard
            extracted_entities["ps_id"] = ps_match.product.id
            extracted_entities["matched_product_term"] = ps_match.matched_term
            extracted_entities["canonical_product"] = ps_match.product.canonical_name
            extracted_entities["scheme_id"] = ps_match.product.scheme
            extracted_entities["mandatory_certification"] = ps_match.product.mandatory_certification
            extracted_entities["category"] = ps_match.product.category
            extracted_entities["match_confidence"] = ps_match.match_confidence

        # If not matched in alias dictionary, search sorted products registry
        if not canonical_product:
            STOPWORDS_TERMS = {"follow", "order", "general", "safety", "standard", "table", "part", "unit", "system"}
            sorted_prods = sorted(
                self.prod_reg.products.values(),
                key=lambda x: len(x.term or ""),
                reverse=True
            )
            for p in sorted_prods:
                term_clean = p.term.lower().strip()
                if len(term_clean) < 3 or term_clean in STOPWORDS_TERMS:
                    continue
                cname = p.normalized_name or p.canonical_name or p.term
                if re.search(r"\b" + re.escape(term_clean) + r"\b", q_lower):
                    canonical_product = cname
                    if not standard_code and p.standard_number:
                        standard_code = p.standard_number.split(":")[0].strip()
                    extracted_entities["matched_product_term"] = term_clean
                    extracted_entities["canonical_product"] = cname
                    if p.scheme_id:
                        extracted_entities["scheme_id"] = p.scheme_id
                    if p.mandatory_certification:
                        extracted_entities["mandatory_certification"] = True
                    break

        # 3. Licence CM/L, CRS R-Number & HUID Extraction
        cml_match = self.cml_pattern.search(clean_q)
        if cml_match:
            cml_val = cml_match.group(1)
            extracted_entities["cml_number"] = cml_val
            intents.append(QueryIntent.LICENCE_CRS_STATUS)

        r_match = self.r_num_pattern.search(clean_q)
        if r_match:
            r_val = r_match.group(1)
            extracted_entities["r_number"] = f"R-{r_val}"
            intents.append(QueryIntent.LICENCE_CRS_STATUS)

        # 4. Technical Parameter Extraction
        for param_key, keywords in self.parameter_keywords.items():
            if any(kw in q_lower for kw in keywords):
                extracted_entities["parameter"] = param_key
                intents.append(QueryIntent.TECHNICAL_VALUE)
                break

        # 5. Multi-Intent Classification
        for intent_enum, kw_list in self.intent_keywords.items():
            if any(kw in q_lower for kw in kw_list):
                if intent_enum not in intents:
                    intents.append(intent_enum)

        # Default to GENERAL_KYS if no specific intent identified
        if not intents:
            intents.append(QueryIntent.GENERAL_KYS)

        # Primary intent prioritization
        primary_intent = intents[0]
        if QueryIntent.MANDATORY_STATUS in intents:
            primary_intent = QueryIntent.MANDATORY_STATUS
        elif QueryIntent.TECHNICAL_VALUE in intents:
            primary_intent = QueryIntent.TECHNICAL_VALUE
        elif QueryIntent.CERTIFICATION_SCHEME in intents:
            primary_intent = QueryIntent.CERTIFICATION_SCHEME
        elif QueryIntent.TESTING_REQUIREMENTS in intents:
            primary_intent = QueryIntent.TESTING_REQUIREMENTS

        # 6. Temporal Target Extraction
        temporal_target = "current"
        resolved_date = as_of_date
        year_match = re.search(r"\b(19\d\d|20[0-2]\d)\b", clean_q)
        if year_match and not extracted_entities.get("explicit_year"):
            y_val = year_match.group(1)
            temporal_target = f"historical_{y_val}"
            resolved_date = f"{y_val}-01-01"
            extracted_entities["query_year"] = y_val

        # 7. Jurisdiction & Scheme Hint Resolution
        jurisdiction = "DOMESTIC_INDIA"
        if any(w in q_lower for w in ["foreign", "overseas", "import", "fmcs", "outside india"]):
            jurisdiction = "FOREIGN_FMCS"
        elif any(w in q_lower for w in ["eco mark", "ecomark", "environment friendly"]):
            jurisdiction = "DOMESTIC_ECO_MARK"

        scheme_hint = None
        if "crs" in q_lower or "compulsory registration" in q_lower or (standard_code and any(s in standard_code for s in ["16046", "16102", "13252", "616"])):
            scheme_hint = "SCHEME-II"
        elif "hallmark" in q_lower or "huid" in q_lower or "gold" in q_lower or "silver" in q_lower:
            scheme_hint = "SCHEME-IV"
        elif "fmcs" in q_lower or jurisdiction == "FOREIGN_FMCS":
            scheme_hint = "SCHEME-I (FMCS)"
        else:
            scheme_hint = "SCHEME-I"

        is_multi_hop = len(intents) >= 2 or ("and" in q_lower and len(intents) > 1)

        return ParsedQuery(
            raw_query=query,
            clean_query=clean_q,
            canonical_product=canonical_product,
            standard_code=standard_code,
            intents=intents,
            primary_intent=primary_intent,
            temporal_target=temporal_target,
            as_of_date=resolved_date,
            extracted_entities=extracted_entities,
            jurisdiction=jurisdiction,
            scheme_hint=scheme_hint,
            is_multi_hop=is_multi_hop,
            confidence=0.95 if (canonical_product or standard_code) else 0.85
        )
