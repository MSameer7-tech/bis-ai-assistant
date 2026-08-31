"""
Tests for Phase 4 Batch 6: pipeline.py and end-to-end question answering
"""
import pytest
from ai.rag.pipeline import RAGPipeline
from ai.rag.models import RAGAnswer


@pytest.fixture
def rag_pipeline():
    return RAGPipeline()


def test_rag_pipeline_insulation_resistance_query(rag_pipeline):
    query = "What is the minimum insulation resistance?"
    res: RAGAnswer = rag_pipeline.answer_question(query=query)

    assert isinstance(res, RAGAnswer)
    assert "4 MΩ" in res.answer
    assert "500 V" in res.answer
    assert len(res.citations) > 0
    assert any(c.verified for c in res.citations)
    assert res.confidence >= 0.8
    assert res.guardrail_result.passed is True


def test_rag_pipeline_gx53_provisional_query(rag_pipeline):
    query = "What is the torque requirement for GX53 cap?"
    res: RAGAnswer = rag_pipeline.answer_question(query=query, as_of_date="2018-01-01")

    assert "3.0 Nm" in res.answer
    assert "under consideration" in res.answer.lower() or "provisional" in res.answer.lower()
    assert res.guardrail_result.passed is True


def test_rag_pipeline_e17_torque_query(rag_pipeline):
    query = "What torque applies to E17 cap?"
    res: RAGAnswer = rag_pipeline.answer_question(query=query, as_of_date="2018-01-01")

    assert "1.5 Nm" in res.answer
    assert res.guardrail_result.passed is True


def test_rag_pipeline_temporal_query(rag_pipeline):
    query = "What is the torque requirement for GX53 cap?"
    # As of 2018 (should pull 2012 standard)
    res_2018: RAGAnswer = rag_pipeline.answer_question(query=query, as_of_date="2018-01-01")
    assert "IS 16102 (Part 1) : 2012" in res_2018.citations[0].standard_number
    assert res_2018.temporal_context == "2018-01-01"


def test_rag_pipeline_unknown_question_refusal(rag_pipeline):
    query = "What is the manufacturing cost and retail market price of an LED lamp?"
    res: RAGAnswer = rag_pipeline.answer_question(query=query)

    assert "could not find sufficient" in res.answer.lower()
    assert res.refusal_reason is not None or res.abstention_reason is not None
