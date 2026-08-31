"""
Unit and regression tests for standard identification and domain retrieval.
Verifies that natural language questions such as 'Which BIS standard applies to X?'
correctly retrieve the exact standard and return grounded scope answers.
"""
import pytest
from ai.rag.pipeline import RAGPipeline

@pytest.fixture(scope="module")
def rag_pipeline():
    return RAGPipeline()

def test_ceiling_fan_standard_identification(rag_pipeline):
    query = "Which BIS standard applies to electric ceiling fans?"
    answer = rag_pipeline.answer_question(query)
    
    assert answer.guardrail_result.passed is True
    assert any("IS 374" in c.standard_number for c in answer.citations)
    assert "IS 374" in answer.answer
    assert "Electric Ceiling Fans" in answer.answer
    assert answer.guardrail_result.grounding_confidence >= 0.9

def test_ordinary_portland_cement_standard_identification(rag_pipeline):
    query = "Which BIS standard specifies ordinary Portland cement?"
    answer = rag_pipeline.answer_question(query)
    
    assert answer.guardrail_result.passed is True
    assert any("IS 269" in c.standard_number for c in answer.citations)
    assert "IS 269" in answer.answer
    assert "Ordinary Portland Cement" in answer.answer
    assert answer.guardrail_result.grounding_confidence >= 0.9

def test_protective_helmets_standard_identification(rag_pipeline):
    query = "Which BIS standard covers protective helmets for motorcycle riders?"
    answer = rag_pipeline.answer_question(query)
    
    assert answer.guardrail_result.passed is True
    assert any("IS 4151" in c.standard_number for c in answer.citations)
    assert "IS 4151" in answer.answer
    assert "Protective Helmets" in answer.answer
    assert answer.guardrail_result.grounding_confidence >= 0.9

def test_secondary_lithium_batteries_standard_identification(rag_pipeline):
    query = "Which BIS standard covers secondary lithium batteries?"
    answer = rag_pipeline.answer_question(query)
    
    assert answer.guardrail_result.passed is True
    assert any("IS 16046" in c.standard_number for c in answer.citations)
    assert "IS 16046 (Part 2)" in answer.answer
    assert answer.guardrail_result.grounding_confidence >= 0.9

def test_deformed_steel_bars_standard_identification(rag_pipeline):
    query = "Which BIS standard specifies high strength deformed steel bars for concrete reinforcement?"
    answer = rag_pipeline.answer_question(query)
    
    assert answer.guardrail_result.passed is True
    assert any("IS 1786" in c.standard_number for c in answer.citations)
    assert "IS 1786" in answer.answer
    assert answer.guardrail_result.grounding_confidence >= 0.9
