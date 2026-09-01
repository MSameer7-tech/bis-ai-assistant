"""
Deterministic Offline LLM Provider.
Provides deterministic, zero-network rule-based generation directly from evidence context.
Enables offline test suites, CI/CD regression, and reproducible benchmark evaluations.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from ai.llm.provider import BaseLLMProvider
from ai.llm.model_config import LLMConfig
from ai.rag.generator import DeterministicGroundedGenerator
from ai.rag.models import RAGContext, RetrievedChunk

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class DeterministicLLMProvider(BaseLLMProvider):
    """
    Offline deterministic generator adhering to the BaseLLMProvider interface.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self.underlying_generator = DeterministicGroundedGenerator()

    def generate(
        self,
        messages: List[Dict[str, str]],
        response_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        system_prompt = ""
        user_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
            elif m.get("role") == "user":
                user_prompt = m.get("content", "")

        context: Optional[RAGContext] = kwargs.get("context")
        query: str = kwargs.get("query", user_prompt)

        if not context:
            context = RAGContext(
                evidence_blocks=[],
                formatted_prompt_context="",
                chunks=[]
            )

        # Generate grounded markdown text
        raw_text = self.underlying_generator.generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
            query=query
        )

        return {
            "text": raw_text,
            "provider": "deterministic",
            "model": self.config.model_name
        }
