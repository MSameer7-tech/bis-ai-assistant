"""
Phase 4 Answer Formatter: Generates clean, presentation-ready markdown and structured outputs.
"""
from typing import Dict, Any, Optional
from ai.rag.models import RAGAnswer


class AnswerFormatter:
    """
    Formats RAGAnswer objects into clean markdown with provenance badges,
    technical parameters tables, and confidence indicators.
    """

    def format_terminal_output(self, rag_answer: RAGAnswer) -> str:
        """Formats the RAGAnswer for terminal CLI display."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"🔍 BIS ASSISTANT QUERY: \"{rag_answer.query}\"")
        if rag_answer.temporal_context:
            lines.append(f"📅 Temporal Gate: {rag_answer.temporal_context}")
        lines.append("=" * 80)
        lines.append("")

        lines.append(rag_answer.answer.strip())
        lines.append("")

        # Verified Citations section
        lines.append("-" * 80)
        lines.append("📚 VERIFIED BIS PROVENANCE CITATIONS:")
        if rag_answer.citations:
            for idx, cit in enumerate(rag_answer.citations, 1):
                status_icon = "✅ [VERIFIED]" if cit.verified else "⚠️ [UNVERIFIED]"
                pages_str = ", ".join(str(p) for p in cit.pages) if cit.pages else "N/A"
                lines.append(f"  {idx}. {status_icon} {cit.standard_number}")
                lines.append(f"     Clause/Table: {cit.clause} | Page(s): {pages_str} | Source ID: {cit.source_id}")
                lines.append(f"     Chunk ID: {cit.chunk_id}")
        else:
            lines.append("  (No direct citations found)")

        lines.append("")
        confidence_pct = int(rag_answer.confidence * 100)
        confidence_icon = "🟢" if rag_answer.confidence >= 0.8 else ("🟡" if rag_answer.confidence >= 0.5 else "🔴")
        lines.append(f"🛡️ Grounding Confidence: {confidence_icon} {confidence_pct}%")

        if rag_answer.guardrail_result and rag_answer.guardrail_result.violations:
            lines.append("⚠️ GUARDRAIL WARNINGS:")
            for v in rag_answer.guardrail_result.violations:
                lines.append(f"  - {v}")

        lines.append("=" * 80)
        return "\n".join(lines)
