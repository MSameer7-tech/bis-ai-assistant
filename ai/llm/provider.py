"""
LLM Provider Abstraction Layer for BIS Grounded Generation.
Decouples RAG evidence retrieval from generation backend.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from ai.llm.model_config import LLMConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract contract for all LLM backends.
    Requires structured message handling and JSON Schema enforcement.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        response_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates structured or text response from provided conversation messages.

        Args:
            messages: List of message dicts [{"role": "system"|"user"|"assistant", "content": "..."}]
            response_schema: Optional Pydantic model enforcing structured output schema.

        Returns:
            Dict containing parsed structured output or raw text.
        """
        pass


def get_llm_provider(config: Optional[LLMConfig] = None) -> BaseLLMProvider:
    """
    Factory creating the configured LLM provider instance.
    """
    cfg = config or LLMConfig.from_env()
    provider_type = cfg.provider.lower()

    if provider_type in ("deterministic", "mock", "offline"):
        from ai.llm.deterministic_provider import DeterministicLLMProvider
        return DeterministicLLMProvider(cfg)
    elif provider_type in ("openai", "openrouter", "deepseek"):
        from ai.llm.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider(cfg)
    elif provider_type in ("ollama", "local"):
        from ai.llm.ollama_provider import OllamaLLMProvider
        return OllamaLLMProvider(cfg)
    else:
        logger.warning(f"Unknown LLM provider '{provider_type}', falling back to DeterministicLLMProvider.")
        from ai.llm.deterministic_provider import DeterministicLLMProvider
        return DeterministicLLMProvider(cfg)
