"""
Phase 4 Context Builder: Formats retrieved chunks into high-density, citation-tagged evidence blocks.
"""
from typing import List, Optional
from ai.rag.models import RetrievedChunk, RAGContext


class ContextBuilder:
    """
    Constructs structured, high-density LLM prompt context from validated RetrievedChunk instances.
    Enforces clear normative banners, especially for under_consideration requirements.
    """

    def __init__(self, max_tokens: int = 3500):
        self.max_tokens = max_tokens

    def build_context(self, chunks: List[RetrievedChunk]) -> RAGContext:
        """
        Formats retrieved chunks into numbered evidence blocks with provenance headers and normative banners.

        Args:
            chunks: Ordered list of retrieved chunks (from highest to lowest relevance)

        Returns:
            RAGContext containing formatted prompt text and structured evidence blocks
        """
        if not chunks:
            return RAGContext(
                evidence_blocks=[],
                formatted_prompt_context="No relevant BIS standard documents were retrieved for this query.",
                chunks=[],
                total_tokens_estimate=0
            )

        evidence_blocks: List[str] = []
        included_chunks: List[RetrievedChunk] = []
        running_token_estimate = 0

        for i, chunk in enumerate(chunks, 1):
            pages_str = ", ".join(str(p) for p in chunk.pages) if chunk.pages else "N/A"
            if chunk.chunk_type == "IDENTITY_EVIDENCE":
                normative_banner = "\nSTATUS: [IDENTITY METADATA ONLY - DO NOT USE AS NORMATIVE EVIDENCE]"
            elif chunk.chunk_type == "RELATIONSHIP_EVIDENCE":
                normative_banner = "\nSTATUS: [CATALOGUE RELATIONSHIP ONLY - DO NOT USE AS NORMATIVE EVIDENCE]"
            elif chunk.chunk_type == "PROCEDURAL_EVIDENCE":
                normative_banner = "\nSTATUS: [PROCEDURAL INSTRUCTION ONLY]"
            elif chunk.normative_force.lower() in ["under_consideration", "provisional"]:
                normative_banner = "\n⚠️ STATUS: [PROVISIONAL / UNDER CONSIDERATION - NOT A MANDATORY REQUIREMENT]"
            elif chunk.normative_force.lower() == "mandatory":
                normative_banner = "\nSTATUS: [MANDATORY NORMATIVE REQUIREMENT]"
            elif chunk.normative_force.lower() == "informative":
                normative_banner = "\nSTATUS: [INFORMATIVE / GENERAL GUIDANCE]"

            validity_str = ""
            if chunk.valid_from:
                validity_str += f" | Effective From: {chunk.valid_from}"
            if chunk.valid_until:
                validity_str += f" | Valid Until: {chunk.valid_until}"

            block = (
                f"--- [EVIDENCE-{i}] ---\n"
                f"Standard: {chunk.standard_number}\n"
                f"Clause: {chunk.clause_number}\n"
                f"Page(s): {pages_str}\n"
                f"Document ID: {chunk.document_id} (Version: {chunk.version_id or 'v001'})\n"
                f"Source ID: {chunk.source_id}\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"Normative Force: {chunk.normative_force.upper()}\n"
                f"Temporal Status: {chunk.temporal_status.upper()}{validity_str}"
                f"{normative_banner}\n\n"
                f"Source Content:\n"
                f"{chunk.text.strip()}\n"
                f"--- [END EVIDENCE-{i}] ---"
            )

            # Rough token estimate (~4 characters per token)
            block_tokens = len(block) // 4
            if running_token_estimate + block_tokens > self.max_tokens and included_chunks:
                break

            evidence_blocks.append(block)
            included_chunks.append(chunk)
            running_token_estimate += block_tokens

        formatted_context = "\n\n".join(evidence_blocks)

        return RAGContext(
            evidence_blocks=evidence_blocks,
            formatted_prompt_context=formatted_context,
            chunks=included_chunks,
            total_tokens_estimate=running_token_estimate
        )
