"""
Ollama Local Model Provider for on-premise execution (Llama 3, Mistral, Qwen).
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


class OllamaLLMProvider(BaseLLMProvider):
    """
    HTTP client for local Ollama instances.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        self.endpoint = (self.config.base_url or "http://localhost:11434").rstrip("/") + "/api/chat"

    def generate(
        self,
        messages: List[Dict[str, str]],
        response_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }

        if response_schema and self.config.enforce_json_schema:
            try:
                payload["format"] = response_schema.model_json_schema()
            except Exception:
                payload["format"] = "json"

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                return {
                    "text": content,
                    "provider": "ollama",
                    "model": self.config.model_name
                }
        except Exception as e:
            logger.error(f"Ollama API request failed: {e}")
            return {"text": "", "error": str(e)}
