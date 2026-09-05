"""
Evidence-Gated Regulatory Answer Generator & Intelligence Orchestrator (Phase 5 Sub-Phase 5C).
Orchestrates Query Understanding, Hybrid Retrieval, Chain Reasoning, Timeline Analysis,
Safety Evaluation, Numerical Verification, and Standardized Grounding Formatting.
"""
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from ai.intelligence.query_understanding import QueryUnderstandingEngine, ParsedQuery, QueryIntent
from ai.intelligence.hybrid_retriever import UnifiedHybridRetriever, HybridRetrievalResult
from ai.intelligence.chain_reasoner import CertificationChainReasoner, CertificationChainResult
from ai.intelligence.timeline_engine import RegulatoryTimelineEngine, TimelineResult
from ai.intelligence.safety_layer import RegulatorySafetyLayer, SafetyCheckResult, SafetyVerdict
from ai.intelligence.citation_formatter import StandardizedCitationFormatter, FormattedGroundingPayload
from ai.acquisition.tests.registry import TestRegistry
from ai.acquisition.provenance.registry import EvidenceRegistry
from ai.acquisition.provenance.models import EvidenceRecord, EvidentiaryStrength
from ai.rag.evidence_gate import GateDecision

logger = logging.getLogger(__name__)


class ProductionIntelligenceAnswer(BaseModel):
    """Unified master response payload for the BIS AI Assistant."""
    status: str  # VERIFIED, REFUSAL, PARTIAL_EVIDENCE, HISTORICAL_CONTEXT, CONFLICT
    query: str
    parsed_query: ParsedQuery
    verdict: Dict[str, Any]
    answer_markdown: str
    certification_chain: Optional[CertificationChainResult] = None
    timeline: Optional[TimelineResult] = None
    test_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    confidence: float = 0.95


class ProductionIntelligenceEngine:
    """
    Master production intelligence engine coordinating all Phase 5 reasoning pipelines.
    """
    def __init__(self):
        self.query_parser = QueryUnderstandingEngine()
        self.hybrid_retriever = UnifiedHybridRetriever()
        self.chain_reasoner = CertificationChainReasoner()
        self.timeline_engine = RegulatoryTimelineEngine()
        self.safety_layer = RegulatorySafetyLayer()
        self.citation_formatter = StandardizedCitationFormatter()
        self.test_reg = TestRegistry()
        self.evidence_reg = EvidenceRegistry()

    def process_query(
        self,
        query: str,
        as_of_date: Optional[str] = None,
        top_k: int = 5
    ) -> ProductionIntelligenceAnswer:
        """
        Executes the full 7-stage production intelligence workflow:
        1. Query Understanding (5A)
        2. Hybrid Retrieval & Subgraph Traversal (5B)
        3. Regulatory Safety & Multi-Conflict Evaluation (5G)
        4. Deterministic Certification Chain Resolution (5D)
        5. Regulatory Timeline & Temporal Analysis (5E)
        6. Normative Requirements Extraction
        7. Evidence-Gated Answer Assembly & Grounding Formatting (5F)
        """
        # Stage 1: Query Understanding
        parsed_query: ParsedQuery = self.query_parser.parse_query(query, as_of_date=as_of_date)

        # Stage 2: Hybrid Retrieval & Subgraph Traversal
        retrieval_result: HybridRetrievalResult = self.hybrid_retriever.retrieve(
            parsed_query,
            top_k=top_k,
            as_of_date=as_of_date
        )

        # Stage 3: Regulatory Safety & Conflict Evaluation
        safety_check: SafetyCheckResult = self.safety_layer.evaluate_safety(
            parsed_query,
            retrieval_result
        )

        if not safety_check.is_safe_to_generate:
            # Deterministic Safe Abstention / Refusal
            refusal_text = f"### ⚠️ Regulatory Safety Notice\n\n{safety_check.refusal_message}\n\n**Guidance**: {safety_check.guidance_message or 'Check the official BIS portal.'}"
            return ProductionIntelligenceAnswer(
                status="REFUSAL",
                query=query,
                parsed_query=parsed_query,
                verdict={"verdict": "REFUSAL", "reason": safety_check.verdict.value},
                answer_markdown=refusal_text,
                certification_chain=None,
                timeline=None,
                test_requirements=[],
                evidence_records=[],
                citations=[],
                warnings=safety_check.warnings,
                confidence=0.9
            )

        # Stage 4: Certification Chain Resolution
        target_entity = parsed_query.canonical_product or parsed_query.standard_code or parsed_query.clean_query
        chain_result: CertificationChainResult = self.chain_reasoner.resolve_chain(
            target_entity,
            as_of_date=as_of_date
        )

        # Stage 5: Regulatory Timeline Analysis
        std_for_timeline = chain_result.standard_number if chain_result.standard_number != "UNKNOWN_STANDARD" else (parsed_query.standard_code or "IS 374")
        timeline_result: TimelineResult = self.timeline_engine.resolve_timeline(
            std_for_timeline,
            as_of_date=as_of_date
        )

        # Stage 6: Normative Test Requirements Resolution
        test_requirements = []
        raw_tests = self.test_reg.get_by_standard(std_for_timeline)
        for t in raw_tests:
            test_requirements.append({
                "test_name": t.test_name,
                "requirement": t.requirement,
                "test_method": t.test_method,
                "clause_page": t.source_clause_page or "Clause 1"
            })

        # Stage 7: Evidence Records Aggregation
        evidence_records: List[EvidenceRecord] = []
        std_evs = self.evidence_reg.get_by_entity(std_for_timeline)
        evidence_records.extend(std_evs)

        # Also pull from graph nodes evidence
        for gn in retrieval_result.graph_nodes[:10]:
            if gn.evidence_id:
                ev_rec = self.evidence_reg.get_by_id(gn.evidence_id)
                if ev_rec and ev_rec not in evidence_records:
                    evidence_records.append(ev_rec)

        # Stage 8: Generate Detailed Context Answer
        core_answer_lines = []
        if chain_result.is_qco_mandatory:
            core_answer_lines.append(
                f"**Yes**, BIS certification is **mandatory** for **{chain_result.canonical_product}** under Indian Standard **{chain_result.standard_number}**."
            )
            core_answer_lines.append(
                f"Compliance is governed under Conformity Assessment **{chain_result.scheme_code}** pursuant to Central Government statutory Quality Control Orders."
            )
        else:
            core_answer_lines.append(
                f"BIS certification for **{chain_result.canonical_product}** under **{chain_result.standard_number}** is currently **voluntary** under the general ISI mark scheme."
            )

        if test_requirements:
            core_answer_lines.append(
                f"\n**Prescribed Testing Overview**: Manufacturers must establish in-house testing facilities and comply with {len(test_requirements)} key normative test parameters including: "
                f"{', '.join([t['test_name'] for t in test_requirements[:4]])}."
            )

        # Add temporal advisory if applicable
        if timeline_result.temporal_warning:
            core_answer_lines.append(f"\n{timeline_result.temporal_warning}")

        core_answer_text = "\n".join(core_answer_lines)

        # Stage 9: Assembly with Standardized Citation Formatter
        all_warnings = list(safety_check.warnings)
        if timeline_result.temporal_warning and timeline_result.temporal_warning not in all_warnings:
            all_warnings.append(timeline_result.temporal_warning)

        grounding_payload: FormattedGroundingPayload = self.citation_formatter.format_response(
            parsed_query=parsed_query,
            chain_result=chain_result,
            timeline_result=timeline_result,
            core_answer_text=core_answer_text,
            evidence_records=evidence_records,
            test_requirements=test_requirements,
            warnings=all_warnings
        )

        # Combine into complete final markdown
        final_md_blocks = [
            grounding_payload.executive_verdict,
            "---",
            "### 📋 Regulatory Guidance & Explanation",
            grounding_payload.detailed_answer,
            "---",
            f"### 🔗 Visual Certification Pathway (`{chain_result.scheme_code}`)",
            f"```\n{grounding_payload.certification_flow_ascii}\n```",
        ]
        if grounding_payload.normative_table_md:
            final_md_blocks.extend(["---", grounding_payload.normative_table_md])
        
        final_md_blocks.extend(["---", grounding_payload.citations_markdown])
        full_answer_markdown = "\n\n".join(final_md_blocks)

        status = "VERIFIED"
        if any(w.startswith("⚠️") for w in all_warnings):
            status = "HISTORICAL_CONTEXT"
        elif any(w.startswith("ℹ️") for w in all_warnings):
            status = "PARTIAL_EVIDENCE"

        verdict_dict = {
            "product": chain_result.canonical_product,
            "standard": chain_result.standard_number,
            "scheme": chain_result.scheme_code,
            "is_mandatory": chain_result.is_qco_mandatory,
            "chain_status": chain_result.chain_status,
            "policy_category": chain_result.policy_category
        }

        return ProductionIntelligenceAnswer(
            status=status,
            query=query,
            parsed_query=parsed_query,
            verdict=verdict_dict,
            answer_markdown=full_answer_markdown,
            certification_chain=chain_result,
            timeline=timeline_result,
            test_requirements=test_requirements,
            evidence_records=[e.model_dump() for e in evidence_records],
            citations=[e.citation_title for e in evidence_records],
            warnings=all_warnings,
            confidence=0.98 if chain_result.chain_status == "COMPLETE" else 0.88
        )
