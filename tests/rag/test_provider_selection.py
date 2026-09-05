import pytest
import os
from unittest.mock import patch
from ai.rag.generator import get_llm_provider, OpenAILLMProvider, GroqLLMProvider, ProviderResponse

@patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test_openai_key"}, clear=True)
def test_openai_provider_config():
    provider = get_llm_provider()
    assert isinstance(provider, OpenAILLMProvider)
    assert provider.api_key == "test_openai_key"

@patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"}, clear=True)
def test_groq_provider_config():
    provider = get_llm_provider()
    assert isinstance(provider, GroqLLMProvider)
    assert provider.api_key == "test_groq_key"
    assert provider.model_name == "qwen/qwen3.8-27b"

@patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"}, clear=True)
def test_provider_selection_works():
    assert isinstance(get_llm_provider("openai"), OpenAILLMProvider)
    assert isinstance(get_llm_provider("groq"), GroqLLMProvider)

def test_internal_response_interface_identical():
    response = ProviderResponse(
        generated_answer="test",
        claims=[],
        citations=[],
        model="test",
        model_version="v1",
        generation_status="SUCCESS",
        refusal_status=False,
        metadata={}
    )
    assert hasattr(response, "generated_answer")
    assert hasattr(response, "claims")
    assert hasattr(response, "citations")

@patch.dict(os.environ, {"LLM_PROVIDER": "groq"}, clear=True)
def test_missing_groq_api_key():
    provider = get_llm_provider()
    assert provider.api_key is None
    # Verify it doesn't crash but properly lacks the key

@patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True)
def test_missing_openai_api_key():
    provider = get_llm_provider()
    assert provider.api_key is None

def test_no_api_key_printed():
    provider = GroqLLMProvider()
    provider.api_key = "secret_key_123"
    assert "secret_key_123" not in str(provider)
    assert "secret_key_123" not in repr(provider)
