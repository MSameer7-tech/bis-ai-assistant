"""
Evidence Gate Module for RAG Grounding & Answer Safety (Phase 4 Batch F).
Enforces evidentiary rules between knowledge retrieval and answer generation to prevent hallucinated regulatory claims.
"""
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field

from ai.acquisition.provenance.models import EvidenceRecord, EvidentiaryStrength
from ai.acquisition.provenance.registry import EvidenceRegistry


class GateDecision(str, Enum):
    """Actionable decision returned by the Evidence Gate."""
    ALLOW_NORMATIVE_CLAIM = "ALLOW_NORMATIVE_CLAIM"      # Safe to state normative limits with exact citation
    ALLOW_LIMITED_CLAIM = "ALLOW_LIMITED_CLAIM"          # State general requirement, cite standard/order ID
    DO_NOT_QUOTE_VERBATIM = "DO_NOT_QUOTE_VERBATIM"      # Reference exists but text extraction incomplete
    REFUSE_UNVERIFIED_CLAIM = "REFUSE_UNVERIFIED_CLAIM"  # Abstain on ungrounded technical values
    SURFACE_CONFLICT = "SURFACE_CONFLICT"                # Explicitly highlight contradictory sources
    HISTORICAL_CONTEXT_ONLY = "HISTORICAL_CONTEXT_ONLY"  # Answer as historical fact with supersession warning


class EvidenceEvaluationResult(BaseModel):
    """Outcome of passing a retrieved item or claim through the Evidence Gate."""
    decision: GateDecision
    evidentiary_strength: EvidentiaryStrength
    citation_string: str
    can_state_normative_value: bool
    can_quote_verbatim: bool
    requires_supersession_warning: bool
    warning_or_disclaimer: Optional[str] = None
    evidence_record: Optional[EvidenceRecord] = None


class EvidenceGate:
    """
    Evaluates evidence records against regulatory safety rules before final answer generation.
    """
    def __init__(self, evidence_registry: Optional[EvidenceRegistry] = None):
        self.registry = evidence_registry or EvidenceRegistry()

    def evaluate_evidence(self, evidence: EvidenceRecord) -> EvidenceEvaluationResult:
        """Evaluates an EvidenceRecord and returns gate decision with safety flags."""
        strength = evidence.evidentiary_strength

        if strength == EvidentiaryStrength.EVIDENCE_VERIFIED:
            return EvidenceEvaluationResult(
                decision=GateDecision.ALLOW_NORMATIVE_CLAIM,
                evidentiary_strength=strength,
                citation_string=evidence.format_citation(),
                can_state_normative_value=True,
                can_quote_verbatim=bool(evidence.verbatim_quote),
                requires_supersession_warning=False,
                evidence_record=evidence
            )

        elif strength == EvidentiaryStrength.EVIDENCE_PARTIAL:
            return EvidenceEvaluationResult(
                decision=GateDecision.ALLOW_LIMITED_CLAIM,
                evidentiary_strength=strength,
                citation_string=evidence.format_citation(),
                can_state_normative_value=True,
                can_quote_verbatim=False,
                requires_supersession_warning=False,
                warning_or_disclaimer="[Reference based on official BIS directory index; clause-level verification pending]",
                evidence_record=evidence
            )

        elif strength == EvidentiaryStrength.SOURCE_FOUND_NOT_EXTRACTED:
            return EvidenceEvaluationResult(
                decision=GateDecision.DO_NOT_QUOTE_VERBATIM,
                evidentiary_strength=strength,
                citation_string=evidence.format_citation(),
                can_state_normative_value=False,
                can_quote_verbatim=False,
                requires_supersession_warning=False,
                warning_or_disclaimer="[Primary source document located but deep extraction in progress]",
                evidence_record=evidence
            )

        elif strength == EvidentiaryStrength.SOURCE_NOT_FOUND:
            return EvidenceEvaluationResult(
                decision=GateDecision.REFUSE_UNVERIFIED_CLAIM,
                evidentiary_strength=strength,
                citation_string="UNVERIFIED SOURCE",
                can_state_normative_value=False,
                can_quote_verbatim=False,
                requires_supersession_warning=False,
                warning_or_disclaimer="[Primary normative source document unavailable in authoritative registry; claim refused]",
                evidence_record=evidence
            )

        elif strength == EvidentiaryStrength.CONFLICTING_EVIDENCE:
            return EvidenceEvaluationResult(
                decision=GateDecision.SURFACE_CONFLICT,
                evidentiary_strength=strength,
                citation_string=evidence.format_citation(),
                can_state_normative_value=False,
                can_quote_verbatim=True,
                requires_supersession_warning=False,
                warning_or_disclaimer="[CRITICAL: Conflicting normative gazette / amendment provisions detected; review required]",
                evidence_record=evidence
            )

        elif strength == EvidentiaryStrength.STALE_EVIDENCE:
            return EvidenceEvaluationResult(
                decision=GateDecision.HISTORICAL_CONTEXT_ONLY,
                evidentiary_strength=strength,
                citation_string=evidence.format_citation(),
                can_state_normative_value=False,
                can_quote_verbatim=True,
                requires_supersession_warning=True,
                warning_or_disclaimer="[HISTORICAL ONLY: This standard/order is superseded and must not be used for current compliance]",
                evidence_record=evidence
            )

        # Default fallback
        return EvidenceEvaluationResult(
            decision=GateDecision.REFUSE_UNVERIFIED_CLAIM,
            evidentiary_strength=EvidentiaryStrength.SOURCE_NOT_FOUND,
            citation_string="UNKNOWN SOURCE",
            can_state_normative_value=False,
            can_quote_verbatim=False,
            requires_supersession_warning=False,
            warning_or_disclaimer="[Unknown evidentiary state; refused for regulatory safety]",
            evidence_record=None
        )

    def evaluate_entity(self, entity_id: str) -> List[EvidenceEvaluationResult]:
        """Evaluates all evidence records bound to an entity."""
        records = self.registry.get_by_entity(entity_id)
        if not records:
            # Check prefix match for multi-part standards (e.g. IS 16102 matching IS 16102 (PART 1))
            clean_e = entity_id.upper().strip()
            for eid, rec in self.registry.evidence_records.items():
                if rec.entity_id and clean_e in rec.entity_id.upper():
                    records.append(rec)

        if not records:
            # Check if entity is a registered standard in catalog
            from ai.acquisition.standards.registry import StandardsRegistry
            std_reg = StandardsRegistry()
            matched_stds = std_reg.get_by_is(entity_id)
            if matched_stds:
                return [EvidenceEvaluationResult(
                    decision=GateDecision.ALLOW_LIMITED_CLAIM,
                    evidentiary_strength=EvidentiaryStrength.EVIDENCE_PARTIAL,
                    citation_string=f"Indian Standard {matched_stds[0].is_number} (Catalog-Indexed)",
                    can_state_normative_value=False,
                    can_quote_verbatim=False,
                    requires_supersession_warning=False,
                    warning_or_disclaimer="[Catalog reference verified; clause-level PDF extraction in repair queue]"
                )]

            return [EvidenceEvaluationResult(
                decision=GateDecision.REFUSE_UNVERIFIED_CLAIM,
                evidentiary_strength=EvidentiaryStrength.SOURCE_NOT_FOUND,
                citation_string=f"Entity {entity_id} (Unindexed)",
                can_state_normative_value=False,
                can_quote_verbatim=False,
                requires_supersession_warning=False,
                warning_or_disclaimer=f"[No authoritative evidence record bound to entity '{entity_id}']"
            )]
        return [self.evaluate_evidence(r) for r in records]
