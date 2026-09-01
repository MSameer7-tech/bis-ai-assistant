import pytest
from ai.llm.model_config import LLMConfig
from ai.llm.provider import get_llm_provider, BaseLLMProvider
from ai.llm.deterministic_provider import DeterministicLLMProvider
from ai.llm.structured_generation import StructuredGenerator
from ai.rag.models import RAGContext, RetrievedChunk


def test_llm_config_defaults():
    cfg = LLMConfig.from_env()
    assert cfg.provider in ("deterministic", "mock", "offline")
    assert cfg.temperature == 0.0


def test_llm_provider_factory():
    provider = get_llm_provider()
    assert isinstance(provider, DeterministicLLMProvider)


def test_deterministic_provider_generation():
    provider = DeterministicLLMProvider()
    chunk = RetrievedChunk(
        chunk_id="CHK-001",
        document_id="DOC-034",
        source_id="SRC-001",
        standard_number="IS 1786 : 2024",
        clause_number="7.2.1",
        title="Yield Stress Requirements",
        pages=[18],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        score=0.95,
        text="The minimum yield strength for Fe 500D shall be 500 N/mm².",
        content_hash="abc123hash"
    )
    context = RAGContext(
        evidence_blocks=[chunk.text],
        formatted_prompt_context=chunk.text,
        chunks=[chunk]
    )
    res = provider.generate(
        messages=[{"role": "user", "content": "What is the yield strength for Fe 500D?"}],
        context=context,
        query="What is the yield strength for Fe 500D under IS 1786:2024?"
    )
    assert "text" in res
    assert "500" in res["text"] or "IS 1786" in res["text"]


def test_structured_generator_prompt_building():
    gen = StructuredGenerator()
    chunk = RetrievedChunk(
        chunk_id="CHK-002",
        document_id="DOC-001",
        source_id="SRC-001",
        standard_number="IS 374 : 2024",
        clause_number="8.1",
        title="Air Delivery Requirements",
        pages=[5],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        score=0.92,
        text="Electric ceiling fans shall have a minimum air delivery of 210 m³/min.",
        content_hash="hash374"
    )
    context = RAGContext(
        evidence_blocks=[chunk.text],
        formatted_prompt_context=chunk.text,
        chunks=[chunk]
    )
    messages = gen.build_evidence_messages("What is the air delivery for ceiling fans?", context)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "IS 374 : 2024" in messages[1]["content"]
    assert "Clause: 8.1" in messages[1]["content"]
