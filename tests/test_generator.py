"""
Tests for Phase 4 Batch 3: generator.py
"""
import pytest
from ai.rag.models import RetrievedChunk
from ai.rag.context_builder import ContextBuilder
from ai.rag.prompt import BIS_SYSTEM_PROMPT, build_user_prompt
from ai.rag.generator import DeterministicGroundedGenerator, get_llm_provider


@pytest.fixture
def sample_context():
    chunk = RetrievedChunk(
        chunk_id="DOC-001-v001::8.1.1::REQ-001",
        document_id="DOC-001",
        version_id="DOC-001-v001",
        source_id="SRC-001",
        standard_number="IS 16102 (Part 1) : 2012",
        clause_number="8.1.1",
        pages=[9],
        chunk_type="requirement",
        normative_force="mandatory",
        temporal_status="current",
        valid_from="2012-08-01",
        score=0.032,
        text="The insulation resistance shall not be less than 4 MΩ when tested at 500 V DC.",
        content_hash="abc123hash",
        provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
    )
    return ContextBuilder().build_context([chunk])


def test_deterministic_generator_answers_grounded_question(sample_context):
    gen = DeterministicGroundedGenerator()
    query = "What is the minimum insulation resistance?"
    prompt = build_user_prompt(query, sample_context)
    ans = gen.generate_answer(BIS_SYSTEM_PROMPT, prompt, sample_context, query)

    assert "4 MΩ" in ans
    assert "IS 16102 (Part 1) : 2012" in ans
    assert "Clause 8.1.1" in ans
    assert "Page(s) 9" in ans


def test_deterministic_generator_refuses_unknown_question(sample_context):
    gen = DeterministicGroundedGenerator()
    query = "What is the manufacturing cost of a lamp?"
    prompt = build_user_prompt(query, sample_context)
    ans = gen.generate_answer(BIS_SYSTEM_PROMPT, prompt, sample_context, query)

    assert "I could not find sufficient information in the retrieved BIS documents" in ans


def test_deterministic_generator_adversarial_modes(sample_context):
    num_gen = DeterministicGroundedGenerator(adversarial_mode="numerical_mismatch")
    ans_num = num_gen.generate_answer("", "", sample_context, "insulation")
    assert "5 MΩ" in ans_num

    cit_gen = DeterministicGroundedGenerator(adversarial_mode="invalid_citation")
    ans_cit = cit_gen.generate_answer("", "", sample_context, "insulation")
    assert "IS 99999 : 2099" in ans_cit
