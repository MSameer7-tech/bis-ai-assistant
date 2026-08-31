"""
Phase 4 Grounded RAG Engine Subpackage.
"""
from ai.rag.models import (
    RetrievedChunk,
    Citation,
    RAGContext,
    GuardrailResult,
    RAGAnswer
)
from ai.rag.retriever import RAGRetriever
from ai.rag.context_builder import ContextBuilder
from ai.rag.prompt import BIS_SYSTEM_PROMPT, build_user_prompt
from ai.rag.generator import (
    BaseLLMProvider,
    DeterministicGroundedGenerator,
    OllamaLLMProvider,
    get_llm_provider
)
from ai.rag.citation import CitationExtractor
from ai.rag.guardrails import ComplianceGuardrails
from ai.rag.answer import AnswerFormatter
from ai.rag.pipeline import RAGPipeline

__all__ = [
    "RetrievedChunk",
    "Citation",
    "RAGContext",
    "GuardrailResult",
    "RAGAnswer",
    "RAGRetriever",
    "ContextBuilder",
    "BIS_SYSTEM_PROMPT",
    "build_user_prompt",
    "BaseLLMProvider",
    "DeterministicGroundedGenerator",
    "OllamaLLMProvider",
    "get_llm_provider",
    "CitationExtractor",
    "ComplianceGuardrails",
    "AnswerFormatter",
    "RAGPipeline"
]
