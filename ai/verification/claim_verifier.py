"""
Atomic Claim Extraction & Evidence Entailment Verifier (Phase 7D).
Decomposes generated answers into atomic claims and verifies grounding against retrieved chunks.
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING
from ai.rag.schema import AtomicClaim, EvidenceRef

if TYPE_CHECKING:
    from ai.rag.models import RetrievedChunk

logger = logging.getLogger(__name__)


class ClaimVerifier:
    """
    Extracts atomic claims from answer text and matches each to its supporting evidence chunk.
    """

    @classmethod
    def decompose_claims(cls, answer_text: str) -> List[str]:
        """
        Splits markdown answer text into atomic sentences/propositions.
        """
        # Split by section and lines
        lines = answer_text.strip().split("\n")
        claims = []

        for line in lines:
            line_str = line.strip()
            # Ignore headers, divider lines, and citation footnotes
            if not line_str or line_str.startswith(("#", "---", "=")):
                continue
            if line_str.startswith("- IS") or line_str.startswith("* IS"):
                continue

            # Strip list markdown prefixes
            clean_line = re.sub(r"^[-*•]\s+", "", line_str)
            clean_line = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_line)

            # Split sentences
            sentences = re.split(r"(?<=[.!?])\s+", clean_line)
            for s in sentences:
                s_clean = s.strip()
                s_lower = s_clean.lower()
                # Explicitly reject provider error strings from becoming claims
                if "generation failed" in s_lower or "error code" in s_lower or "api_key" in s_lower or "model_decommissioned" in s_lower or "missing credentials" in s_lower or "provider error" in s_lower:
                    continue
                if len(s_clean) > 12 and not s_lower.startswith(("citations", "technical details", "direct answer", "source:")):
                    claims.append(s_clean)

        return claims

    @classmethod
    def verify_claims(
        cls,
        answer_text: str,
        evidence_chunks: List[RetrievedChunk]
    ) -> List[AtomicClaim]:
        """
        Decomposes answer text into atomic claims and links each to supporting evidence.
        """
        raw_claims = cls.decompose_claims(answer_text)
        atomic_claims: List[AtomicClaim] = []

        # Decision Logic & Thresholds:
        # A claim is verified ONLY IF it achieves an entailment score >= 0.60
        # Score is built from:
        # - Token overlap ratio
        # - Numerical overlap (+0.40)
        # - Standard code mention (+0.35)
        # - Clause mention (+0.35)
        VERIFICATION_THRESHOLD = 0.60

        for i, claim_text in enumerate(raw_claims, 1):
            claim_id = f"CLM-{i:03d}"
            c_tokens = set(re.findall(r"\w+", claim_text.lower()))
            c_sig_tokens = {t for t in c_tokens if len(t) > 2 and t not in {"the", "for", "and", "under", "with", "from", "are", "shall"}}

            matched_evidence: List[EvidenceRef] = []
            best_entailment = 0.0

            for chunk in evidence_chunks:
                chunk_text = chunk.text
                chunk_tokens = set(re.findall(r"\w+", chunk_text.lower()))
                
                # Check token overlap
                overlap = len(c_sig_tokens & chunk_tokens)
                overlap_ratio = (overlap / len(c_sig_tokens)) if c_sig_tokens else 0.0

                # Check numerical value presence
                claim_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", claim_text))
                # Normalize float ints (500.0 -> 500)
                norm_claim_nums = {n.rstrip('.0') if '.' in n else n for n in claim_nums}
                chunk_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", chunk_text))
                norm_chunk_nums = {n.rstrip('.0') if '.' in n else n for n in chunk_nums}
                num_overlap = norm_claim_nums & norm_chunk_nums

                # Check if standard code or clause matches
                std_clean = re.sub(r"[\s:]+", "", chunk.standard_number.lower())
                std_in_claim = std_clean in re.sub(r"[\s:]+", "", claim_text.lower())
                clause_in_claim = chunk.clause_number in claim_text or f"clause {chunk.clause_number}".lower() in claim_text.lower()

                # Compute entailment score
                score = overlap_ratio
                if std_in_claim:
                    score += 0.35
                if clause_in_claim:
                    score += 0.35
                if num_overlap:
                    score += 0.40
                score = min(1.0, score)

                # Only associate evidence if it contributes meaningfully to entailment
                if score >= 0.40:
                    if score > best_entailment:
                        best_entailment = score

                    matched_evidence.append(EvidenceRef(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        standard_number=chunk.standard_number,
                        clause=chunk.clause_number,
                        page=chunk.pages[0] if chunk.pages else None,
                        quote=chunk_text[:150] + "..." if len(chunk_text) > 150 else chunk_text
                    ))

            is_verified = (best_entailment >= VERIFICATION_THRESHOLD)

            atomic_claims.append(AtomicClaim(
                claim_id=claim_id,
                text=claim_text,
                evidence=matched_evidence[:2], # Top 2 supporting evidence refs
                verified=is_verified,
                entailment_score=round(best_entailment if best_entailment > 0 else (0.85 if is_verified else 0.0), 2)
            ))

        return atomic_claims
