"""
Citation Extractor, Citation Builder, and Citation-Aware Grounding Formatter (Phase 4 Batch F).
Extracts, validates, and builds deep regulatory citations for RAG answers.
"""
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ai.acquisition.provenance.models import EvidenceRecord, EvidentiaryStrength
from ai.rag.models import RetrievedChunk, Citation
from ai.rag.evidence_gate import EvidenceGate, EvidenceEvaluationResult, GateDecision


class CitationExtractor:
    """Extracts and verifies citations from generated LLM answers against retrieved chunks."""

    # Pattern: - IS 16102 (Part 1) : 2012, Clause 8.1.1, Page(s) 9 (Document ID: DOC-001)
    CITATION_PATTERN = re.compile(
        r"-\s*([A-Z0-9\s\(\)/:\-]+?),\s*(?:Clause\s+([A-Za-z0-9\.\-_]+))?,\s*(?:Page\(s\)\s+([0-9,\s]+))?(?:\s*\(Document ID:\s*([A-Za-z0-9\-_]+)\))?",
        re.IGNORECASE
    )

    def extract_citations(
        self,
        answer_text: str,
        retrieved_chunks: Optional[List[RetrievedChunk]] = None,
        structured_citations: Optional[List[Dict[str, Any]]] = None
    ) -> List[Citation]:
        chunks = retrieved_chunks or []
        citations: List[Citation] = []
        
        # If structured citations are provided (Phase 7), use them
        if structured_citations:
            for sc in structured_citations:
                std_clean = sc.get("standard_number", "").strip()
                clause_clean = sc.get("clause", "").strip()
                doc_clean = sc.get("document_id", "").strip()
                quote = sc.get("quote", "").strip()
                
                matched_chunk, verified = self._verify_citation(std_clean, clause_clean, doc_clean, quote, chunks)
                citations.append(Citation(
                    standard_number=std_clean,
                    clause=clause_clean or (matched_chunk.clause_number if matched_chunk else "General"),
                    pages=matched_chunk.pages if matched_chunk else [],
                    source_id=matched_chunk.source_id if matched_chunk else "UNKNOWN",
                    chunk_id=matched_chunk.chunk_id if matched_chunk else "UNMATCHED",
                    quote_snippet=quote,
                    verified=verified
                ))
            return citations

        # Fallback to regex extraction for unstructured legacy generator
        matches = self.CITATION_PATTERN.findall(answer_text)
        for match in matches:
            std_raw, clause_raw, pages_raw, doc_id_raw = match
            std_clean = std_raw.strip()
            clause_clean = clause_raw.strip() if clause_raw else ""
            doc_clean = doc_id_raw.strip() if doc_id_raw else ""
            
            matched_chunk, verified = self._verify_citation(std_clean, clause_clean, doc_clean, "", chunks)
            
            citations.append(Citation(
                standard_number=std_clean,
                clause=clause_clean or (matched_chunk.clause_number if matched_chunk else "General"),
                pages=matched_chunk.pages if matched_chunk else [],
                source_id=matched_chunk.source_id if matched_chunk else "UNKNOWN",
                chunk_id=matched_chunk.chunk_id if matched_chunk else "UNMATCHED",
                quote_snippet=None,
                verified=verified
            ))
        return citations

    def _verify_citation(self, std: str, clause: str, doc_id: str, quote: str, chunks: List[RetrievedChunk]) -> tuple[Optional[RetrievedChunk], bool]:
        """Strict Phase 7 Verification combining metadata matching and token overlap."""
        for chunk in chunks:
            std_match = (
                std.upper() in chunk.standard_number.upper() or
                chunk.standard_number.upper() in std.upper() or
                (doc_id and chunk.document_id and doc_id.upper() == chunk.document_id.upper())
            )
            clause_match = True
            if clause and chunk.clause_number:
                clause_match = (clause.lower() == chunk.clause_number.lower())
                
            if std_match and clause_match:
                if not quote:
                    return chunk, True
                
                # Token overlap / textual support verification
                quote_tokens = set(re.findall(r"\w+", quote.lower()))
                chunk_tokens = set(re.findall(r"\w+", chunk.text.lower()))
                
                if not quote_tokens:
                    return chunk, True
                    
                overlap = len(quote_tokens.intersection(chunk_tokens))
                # 80% token overlap required to prevent plausible fakes
                if overlap / len(quote_tokens) >= 0.8:
                    return chunk, True
                
        return None, False


class CitationBuilder:
    """
    Builds clean, legally grounded citation blocks for user-facing answers.
    """
    def __init__(self, evidence_gate: Optional[EvidenceGate] = None):
        self.gate = evidence_gate or EvidenceGate()

    def format_citation_block(self, evidence: EvidenceRecord) -> str:
        """
        Formats a structured citation box for grounding display.
        """
        lines = [
            f"**Authority**: {evidence.source_authority.value}",
            f"**Citation**: {evidence.citation_title}",
            f"**Locator**: {evidence.locator_value}"
        ]
        if evidence.clause_number:
            lines.append(f"**Clause**: {evidence.clause_number}")
        if evidence.page_number:
            lines.append(f"**Page**: {evidence.page_number}")
        if evidence.document_sha256:
            lines.append(f"**Document SHA-256**: `{evidence.document_sha256[:16]}...`")
        if evidence.provenance_url:
            lines.append(f"**Source URL**: [{evidence.provenance_url}]({evidence.provenance_url})")
        if evidence.evidentiary_strength == EvidentiaryStrength.STALE_EVIDENCE:
            lines.append("⚠️ **Status**: *Historical Record (Superseded)*")
        else:
            lines.append(f"**Evidentiary Status**: `{evidence.evidentiary_strength.value}`")

        return "\n".join(lines)

    def format_inline_citation(self, evidence: EvidenceRecord) -> str:
        """Generates inline markdown citation e.g. [IS 1786:2008, Cl 8.1, Pg 4]."""
        return f"[{evidence.format_citation()}]"
