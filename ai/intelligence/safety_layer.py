"""
Regulatory Safety, Multi-Conflict & Abstention Layer (Phase 5 Sub-Phase 5G).
Enforces zero-hallucination guardrails, unsupported material traps, cross-domain parameter traps,
and contradictory gazette notification conflict detection.
"""
import re
import logging
from enum import Enum
from typing import List, Dict, Optional, Set, Any, Tuple
from pydantic import BaseModel, Field

from ai.intelligence.query_understanding import ParsedQuery, QueryIntent
from ai.intelligence.hybrid_retriever import HybridRetrievalResult
from ai.rag.evidence_gate import GateDecision

logger = logging.getLogger(__name__)


class SafetyVerdict(str, Enum):
    ALLOW = "ALLOW"
    BLOCK_OUT_OF_SCOPE = "BLOCK_OUT_OF_SCOPE"
    BLOCK_CROSS_DOMAIN_TRAP = "BLOCK_CROSS_DOMAIN_TRAP"
    WARN_CONFLICT = "WARN_CONFLICT"
    WARN_STALE_HISTORICAL = "WARN_STALE_HISTORICAL"
    ABSTAIN_INSUFFICIENT_EVIDENCE = "ABSTAIN_INSUFFICIENT_EVIDENCE"


class SafetyCheckResult(BaseModel):
    """Detailed outcome of passing a query and evidence through the regulatory safety layer."""
    is_safe_to_generate: bool
    verdict: SafetyVerdict
    refusal_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    conflict_details: Optional[str] = None
    guidance_message: Optional[str] = None


class RegulatorySafetyLayer:
    """
    Multi-stage regulatory safety gate preventing hallucination, cross-domain leakage,
    and ungrounded legal claims.
    """
    UNSUPPORTED_MATERIALS = {
        "titanium", "titanium alloy", "ti-6al-4v", "inconel", "inconel 718", "inconel 625",
        "kevlar", "aramid", "carbon fiber", "carbon fibre", "cfrp", "graphene", "zirconium",
        "nitinol", "beryllium copper", "uhmwpe", "aerogel", "gallium nitride", "tungsten carbide",
        "teleportation", "anti-gravity", "dark matter", "starship", "warp drive", "space elevator",
        "holographic quantum", "lightsaber", "plasma blaster", "vibranium", "adamantium",
        "laser cannon", "cold fusion", "quantum computer", "quantum processor", "binary search",
        "capital of", "recipe", "world cup", "airspeed velocity", "gdp"
    }

    CROSS_DOMAIN_INCOMPATIBILITIES = [
        # (Parameter keyword, Incompatible subject)
        ("air delivery", ["steel", "rebar", "cement", "water", "helmet", "stove", "pipe"]),
        ("service value", ["steel", "rebar", "cement", "water", "helmet", "stove"]),
        ("proof stress", ["water", "fan", "helmet", "lamp", "soap", "bulb", "food"]),
        ("yield strength", ["water", "fan", "lamp", "bulb", "oil", "food"]),
        ("ph", ["steel", "rebar", "fan", "helmet", "switch", "socket", "conduit", "cement", "concrete"]),
        ("compressive strength", ["fan", "lamp", "water", "bulb", "wire"]),
        ("coliform", ["steel", "fan", "cement", "helmet", "gas stove", "cable"]),
        ("thermal efficiency", ["steel", "cement", "water", "helmet", "fan", "wire"])
    ]

    def evaluate_safety(
        self,
        parsed_query: ParsedQuery,
        retrieval_result: HybridRetrievalResult
    ) -> SafetyCheckResult:
        """
        Executes comprehensive regulatory safety checks on query and retrieved context.
        """
        q_lower = parsed_query.clean_query.lower()
        warnings: List[str] = []

        # 1. Unsupported Material & Out-of-Scope Topic Gate
        for mat in self.UNSUPPORTED_MATERIALS:
            if re.search(r"\b" + re.escape(mat) + r"(?:s|es)?\b", q_lower) and not parsed_query.standard_code:
                return SafetyCheckResult(
                    is_safe_to_generate=False,
                    verdict=SafetyVerdict.BLOCK_OUT_OF_SCOPE,
                    refusal_message=f"Topic / Material '{mat.title()}' is not covered under the active Indian Standards (BIS) product certification catalog.",
                    guidance_message="Refer to specialized international, academic, or domain-specific specifications for non-BIS governed topics."
                )

        # 1b. General Out-of-Scope / No Product Match Gate
        if not parsed_query.canonical_product and not parsed_query.standard_code and not parsed_query.extracted_entities:
            # Check if retrieval found any high-confidence Indian Standard evidence
            if not retrieval_result.ranked_chunks or (retrieval_result.ranked_chunks and getattr(retrieval_result.ranked_chunks[0], "relevance_score", 1.0) < 0.40):
                return SafetyCheckResult(
                    is_safe_to_generate=False,
                    verdict=SafetyVerdict.BLOCK_OUT_OF_SCOPE,
                    refusal_message="I could not find a verified Indian Standard (IS) or regulated commodity matching your query in the BIS registry.",
                    guidance_message="Please verify if the product or standard is listed under active BIS Quality Control Orders (QCO) or Scheme-I/II."
                )

        # 2. Cross-Domain Parameter Trap Gate
        for param_term, bad_subjects in self.CROSS_DOMAIN_INCOMPATIBILITIES:
            if re.search(r"\b" + re.escape(param_term) + r"\b", q_lower):
                for subj in bad_subjects:
                    if re.search(r"\b" + re.escape(subj) + r"\b", q_lower):
                        return SafetyCheckResult(
                            is_safe_to_generate=False,
                            verdict=SafetyVerdict.BLOCK_CROSS_DOMAIN_TRAP,
                            refusal_message=f"Cross-Domain Inconsistency: The parameter '{param_term}' is technically inapplicable to '{subj}'.",
                            guidance_message=f"'{param_term}' applies to relevant governed commodities. Check the specific product standard."
                        )

        # 3. Evidence Gate Primary Decision Check
        if retrieval_result.primary_decision == GateDecision.REFUSE_UNVERIFIED_CLAIM:
            return SafetyCheckResult(
                is_safe_to_generate=False,
                verdict=SafetyVerdict.ABSTAIN_INSUFFICIENT_EVIDENCE,
                refusal_message="I could not find authoritative primary regulatory evidence in the BIS registry to answer this query definitively.",
                guidance_message="Please verify if the standard number or commodity is currently listed under mandatory QCO or Scheme-I/II."
            )

        # 4. Conflicting Evidence Check
        if retrieval_result.primary_decision == GateDecision.SURFACE_CONFLICT:
            warnings.append("⚠️ Contradictory regulatory gazette notifications detected across revisions. Reviewing both provisions.")
            return SafetyCheckResult(
                is_safe_to_generate=True,
                verdict=SafetyVerdict.WARN_CONFLICT,
                warnings=warnings,
                conflict_details="Multiple gazette amendments specify conflicting compliance dates or transition windows."
            )

        # 5. Stale / Historical Check
        if retrieval_result.primary_decision == GateDecision.HISTORICAL_CONTEXT_ONLY:
            warnings.append("ℹ️ This standard edition is superseded. Generating response in historical context with current edition references.")
            return SafetyCheckResult(
                is_safe_to_generate=True,
                verdict=SafetyVerdict.WARN_STALE_HISTORICAL,
                warnings=warnings
            )

        return SafetyCheckResult(
            is_safe_to_generate=True,
            verdict=SafetyVerdict.ALLOW,
            warnings=warnings
        )
