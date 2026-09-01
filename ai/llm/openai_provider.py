"""
OpenAI / OpenRouter API Provider with Structured Output enforcement.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Type, TypeVar
import urllib.request
import urllib.error
from pydantic import BaseModel
from ai.llm.provider import BaseLLMProvider
from ai.llm.model_config import LLMConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAILLMProvider(BaseLLMProvider):
    """
    HTTP client for OpenAI / OpenAI-compatible APIs (OpenRouter, Groq, DeepSeek, Together).
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self.endpoint = (self.config.base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"

    def generate(
        self,
        messages: List[Dict[str, str]],
        response_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.config.api_key:
            logger.warning("No API key configured for OpenAI provider, falling back to empty response.")
            return {"text": "", "error": "MISSING_API_KEY"}

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if response_schema and self.config.enforce_json_schema:
            try:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_schema.__name__,
                        "strict": True,
                        "schema": response_schema.model_json_schema()
                    }
                }
            except Exception as e:
                logger.warning(f"Could not attach json_schema response_format: {e}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("choices", [{}])[0].get("message", {})
                content = choice.get("content", "")
                return {
                    "text": content,
                    "provider": "openai",
                    "model": self.config.model_name,
                    "usage": data.get("usage", {})
                }
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            return {"text": "", "error": str(e)}
