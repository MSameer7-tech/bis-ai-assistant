"""
Standardized Citation & Structured Grounding Formatter (Phase 5 Sub-Phase 5F).
Assembles verified answers, executive verdicts, testing matrices, visual certification paths,
and cryptographic evidence ledgers.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from ai.intelligence.query_understanding import ParsedQuery
from ai.intelligence.chain_reasoner import CertificationChainResult
from ai.intelligence.timeline_engine import TimelineResult
from ai.acquisition.provenance.models import EvidenceRecord, EvidentiaryStrength
from ai.rag.citation import CitationBuilder


class FormattedGroundingPayload(BaseModel):
    """Auditor-ready standardized output package."""
    executive_verdict: str
    detailed_answer: str
    normative_table_md: Optional[str] = None
    certification_flow_ascii: str
    certification_flow_mermaid: str
    timeline_summary: Optional[str] = None
    evidence_ledger: List[Dict[str, Any]] = Field(default_factory=list)
    citations_markdown: str


class StandardizedCitationFormatter:
    """
    Constructs clean, standardized, audit-grade response structures.
    """
    def __init__(self):
        self.cit_builder = CitationBuilder()

    def format_response(
        self,
        parsed_query: ParsedQuery,
        chain_result: CertificationChainResult,
        timeline_result: Optional[TimelineResult],
        core_answer_text: str,
        evidence_records: List[EvidenceRecord],
        test_requirements: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[str]] = None
    ) -> FormattedGroundingPayload:
        """Assembles all intelligence layers into a structured output contract."""
        
        # 1. Executive Verdict
        mand_status_str = "MANDATORY" if chain_result.is_qco_mandatory else "VOLUNTARY"
        verdict_lines = [
            f"### 🏛️ BIS Executive Verdict: **{mand_status_str}**",
            f"- **Product / Commodity**: {chain_result.canonical_product}",
            f"- **Governing Indian Standard**: `{chain_result.standard_number}`",
            f"- **Certification Scheme**: `{chain_result.scheme_code}`",
            f"- **Statutory Mandate**: {'Mandatory under Quality Control Order (QCO)' if chain_result.is_qco_mandatory else 'Voluntary Indian Standard'}",
            f"- **Certification Chain Status**: **{chain_result.chain_status}** ({len(chain_result.nodes) - len(chain_result.missing_required_nodes)}/{len(chain_result.nodes)} nodes verified)"
        ]
        if warnings:
            for w in warnings:
                verdict_lines.append(f"> {w}")
        executive_verdict = "\n".join(verdict_lines)

        # 2. Normative Specifications Table
        normative_table_md = None
        if test_requirements:
            table_lines = [
                "### 🧪 Prescribed Compliance Tests & Normative Limits",
                "| Test Name / Parameter | Normative Requirement | Test Method | Applicable Clause |",
                "|---|---|---|---|"
            ]
            for tr in test_requirements:
                table_lines.append(
                    f"| **{tr.get('test_name', '')}** | {tr.get('requirement', '')} | `{tr.get('test_method', '')}` | {tr.get('clause_page', 'Standard Scope')} |"
                )
            normative_table_md = "\n".join(table_lines)

        # 3. Evidence Ledger & Citations Markdown
        ledger = []
        cit_md_lines = ["### 📜 Authoritative Regulatory Citations & Provenance Ledger"]
        for ev in evidence_records:
            ledger.append(ev.model_dump())
            strength_badge = "🟢 VERIFIED" if ev.evidentiary_strength == EvidentiaryStrength.EVIDENCE_VERIFIED else "🟡 PARTIAL"
            hash_snippet = f"`{ev.document_sha256[:16]}...`" if ev.document_sha256 else "Registry-Indexed"
            cit_md_lines.append(
                f"- **{ev.citation_title}** ({strength_badge})\n"
                f"  - Locator: `{ev.locator_value}` | Clause: `{ev.clause_number or 'Scope'}` | Page: `{ev.page_number or '1'}`\n"
                f"  - Document SHA-256: {hash_snippet} | Authority: `{ev.source_authority.value}`"
            )

        citations_markdown = "\n".join(cit_md_lines)

        # 4. Timeline Summary
        timeline_summary = None
        if timeline_result:
            timeline_summary = (
                f"**Active Standard Edition**: `{timeline_result.active_standard_edition}` "
                f"({timeline_result.active_standard_title}) as of target date `{timeline_result.target_date}`. "
                f"Total historical milestones indexed: {len(timeline_result.events)}."
            )

        return FormattedGroundingPayload(
            executive_verdict=executive_verdict,
            detailed_answer=core_answer_text,
            normative_table_md=normative_table_md,
            certification_flow_ascii=chain_result.ascii_diagram,
            certification_flow_mermaid=chain_result.mermaid_diagram,
            timeline_summary=timeline_summary,
            evidence_ledger=ledger,
            citations_markdown=citations_markdown
        )
