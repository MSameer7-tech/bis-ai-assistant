"""
LLM Configuration and Provider Settings.
Supports OpenAI, Ollama, Anthropic, Gemini, and Deterministic CI test providers.
"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration model for LLM providers."""
    provider: str = Field(default="deterministic", description="Provider type: deterministic, openai, ollama, custom")
    model_name: str = Field(default="bis-grounded-deterministic", description="Model identifier (e.g. gpt-4o, llama3:8b)")
    api_key: Optional[str] = Field(default=None, description="API Key for cloud providers")
    base_url: Optional[str] = Field(default=None, description="Base API endpoint URL (e.g. http://localhost:11434/v1)")
    temperature: float = Field(default=0.0, description="Sampling temperature (strictly 0.0 for deterministic factual grounding)")
    max_tokens: int = Field(default=2048, description="Maximum token generation limit")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    enforce_json_schema: bool = Field(default=True, description="Whether to enforce strict JSON Schema outputs")

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Loads configuration from environment variables."""
        provider = os.getenv("BIS_LLM_PROVIDER", "deterministic").lower()
        model_name = os.getenv("BIS_LLM_MODEL", "bis-grounded-deterministic")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("BIS_LLM_API_KEY")
        base_url = os.getenv("BIS_LLM_BASE_URL")

        return cls(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=float(os.getenv("BIS_LLM_TEMPERATURE", "0.0")),
            max_tokens=int(os.getenv("BIS_LLM_MAX_TOKENS", "2048")),
            timeout=float(os.getenv("BIS_LLM_TIMEOUT", "30.0")),
            enforce_json_schema=os.getenv("BIS_LLM_ENFORCE_JSON", "true").lower() == "true"
        )
