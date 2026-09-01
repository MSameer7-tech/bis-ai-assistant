"""
Phase 6F: Query Intent Classifier.
Categorizes user inquiries into 7 discrete intent routes to guide hybrid multi-channel retrieval:
1. STANDARD_LOOKUP
2. PRODUCT_STANDARD
3. TECHNICAL_VALUE
4. CERTIFICATION_QCO
5. LABORATORY
6. VERSION_COMPARISON
7. CLAUSE_LOOKUP
"""
import re
from enum import Enum
from typing import Dict, Any, Optional


class QueryIntent(str, Enum):
    STANDARD_LOOKUP = "STANDARD_LOOKUP"
    PRODUCT_STANDARD = "PRODUCT_STANDARD"
    TECHNICAL_VALUE = "TECHNICAL_VALUE"
    CERTIFICATION_QCO = "CERTIFICATION_QCO"
    LABORATORY = "LABORATORY"
    VERSION_COMPARISON = "VERSION_COMPARISON"
    CLAUSE_LOOKUP = "CLAUSE_LOOKUP"


class IntentClassifier:
    """
    Classifies user natural language query into specific retrieval routes.
    """

    @classmethod
    def classify(cls, query: str) -> str:
        return cls.classify_intent(query)["intent"]

    @staticmethod
    def classify_intent(query: str) -> Dict[str, Any]:
        q_lower = query.strip().lower()

        # 1. Version Comparison
        if any(w in q_lower for w in ["superseded", "supersedes", "previous edition", "earlier version", "changed between", "difference between", "difference in", "compare editions", "2008 and 2024", "2013 and 2024"]):
            return {
                "intent": QueryIntent.VERSION_COMPARISON.value,
                "confidence": 0.95,
                "primary_channel": "graph_and_metadata"
            }

        # 2. Laboratory / Testing facilities
        if any(w in q_lower for w in ["laboratory", "laboratories", "lab", "testing facility", "where to test", "test center", "nabl accredited", "testing capabilities"]):
            return {
                "intent": QueryIntent.LABORATORY.value,
                "confidence": 0.95,
                "primary_channel": "graph_first"
            }

        # 3. Certification / QCO / Mandatory ISI Mark
        if any(w in q_lower for w in ["qco", "quality control order", "mandatory", "compulsory", "certification scheme", "isi mark mandatory", "scheme of inspection", "product manual", "sit"]):
            return {
                "intent": QueryIntent.CERTIFICATION_QCO.value,
                "confidence": 0.95,
                "primary_channel": "graph_first"
            }

        # 4. Clause Lookup
        if re.search(r"\b(clause|subclause|section|annex|table)\s+([0-9A-Z\.]+)", q_lower):
            return {
                "intent": QueryIntent.CLAUSE_LOOKUP.value,
                "confidence": 0.95,
                "primary_channel": "metadata_and_vector"
            }

        # 5. Technical Value / Tolerances / Exact Parameters
        if any(w in q_lower for w in ["minimum", "maximum", "yield strength", "elongation", "tensile", "thickness", "diameter", "temperature", "pressure", "tolerance", "value of", "requirement for", "nominal mass"]):
            return {
                "intent": QueryIntent.TECHNICAL_VALUE.value,
                "confidence": 0.90,
                "primary_channel": "hybrid_vector_and_exact"
            }

        # 6. Standard Identification from Product
        if any(w in q_lower for w in ["which standard", "what standard", "applicable standard", "standard for", "standard covers", "is code for", "bis standard for"]):
            return {
                "intent": QueryIntent.PRODUCT_STANDARD.value,
                "confidence": 0.95,
                "primary_channel": "ontology_product_resolver"
            }

        # 7. Standard Lookup by IS Number
        if re.search(r"\bis\s*([0-9]{3,5})\b", q_lower):
            return {
                "intent": QueryIntent.STANDARD_LOOKUP.value,
                "confidence": 0.90,
                "primary_channel": "metadata_first"
            }

        # Default fallback
        return {
            "intent": QueryIntent.PRODUCT_STANDARD.value,
            "confidence": 0.70,
            "primary_channel": "hybrid_dense_and_ontology"
        }
