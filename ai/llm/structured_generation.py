"""
Structured Generation Coordinator (Phase 7A).
Formats isolated authoritative evidence blocks and coordinates structured LLM generation.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from ai.llm.provider import BaseLLMProvider, get_llm_provider
from ai.rag.models import RAGContext, RetrievedChunk

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

STRUCTURED_BIS_SYSTEM_PROMPT = """You are the Bureau of Indian Standards (BIS) Technical Assistant.
Your mission is to provide strictly grounded technical compliance answers about Indian Standards.

CRITICAL GROUNDING RULES:
1. Answer ONLY from the supplied Authoritative Evidence blocks.
2. DO NOT use pre-trained background knowledge to invent standard numbers, edition years, clauses, or numerical values.
3. Every factual claim MUST cite the exact Standard, Clause, and Page number provided in the evidence.
4. If the supplied evidence is insufficient or contradictory, explicitly state that verified evidence is not available.
5. If the query asks for out-of-scope information (market prices, corporate revenue, personal opinions, unstandardized products), refuse with a clear explanation.
"""


class StructuredGenerator:
    """
    Coordinates LLM generation using evidence isolation and structured prompt templates.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def build_evidence_messages(
        self,
        query: str,
        context: RAGContext,
        as_of_date: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Builds system and user message payload with numbered evidence blocks.
        """
        evidence_str = ""
        for i, chunk in enumerate(context.chunks, 1):
            pages_str = ", ".join(str(p) for p in chunk.pages) if chunk.pages else "N/A"
            evidence_str += (
                f"\n--- [Evidence {i}] ---\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"Standard: {chunk.standard_number}\n"
                f"Clause: {chunk.clause_number}\n"
                f"Pages: {pages_str}\n"
                f"Normative Force: {chunk.normative_force}\n"
                f"Content:\n{chunk.text}\n"
            )

        temporal_notice = f"Historical Applicability Date: {as_of_date}\n" if as_of_date else "Current Enforced Editions (2026)\n"

        user_content = (
            f"USER QUESTION:\n{query}\n\n"
            f"{temporal_notice}\n"
            f"AUTHORITATIVE EVIDENCE:\n"
            f"{evidence_str if evidence_str else 'No matching evidence found in the BIS knowledge base.'}\n\n"
            f"INSTRUCTIONS:\n"
            f"Provide a clear, authoritative markdown response directly answering the question based ONLY on the evidence above.\n"
            f"Include citations in the format: IS <number>:<year>, Clause <clause>, Page <page>."
        )

        return [
            {"role": "system", "content": STRUCTURED_BIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

    def generate(
        self,
        query: str,
        context: RAGContext,
        as_of_date: Optional[str] = None,
        response_schema: Optional[Type[T]] = None
    ) -> Dict[str, Any]:
        """
        Executes structured generation via the configured LLM provider.
        """
        messages = self.build_evidence_messages(query, context, as_of_date)
        return self.provider.generate(
            messages=messages,
            response_schema=response_schema,
            context=context,
            query=query
        )
