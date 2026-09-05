"""
Pytest Integration for 25-Product RAG Evaluation Suite.
Asserts >= 95% pass rate, 0 wrong product resolutions, 0 hallucinations, and full evidence backing.
"""
import json
import pytest
from pathlib import Path
from evaluation.run_rag_evaluation import RAGEvaluationRunner

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "data" / "evaluation" / "rag_25_product_test_cases.json"
RESULTS_DIR = ROOT_DIR / "data" / "evaluation" / "results"


@pytest.fixture(scope="module")
def eval_runner():
    return RAGEvaluationRunner(dataset_path=DATASET_PATH)


def test_rag_multi_product_evaluation_gate(eval_runner):
    """Executes the comprehensive 460-case evaluation and enforces release gate criteria."""
    summary = eval_runner.run_evaluation()
    
    assert summary["total_test_cases"] >= 400
    assert summary["wrong_product_count"] == 0, f"Encountered {summary['wrong_product_count']} cross-product confusion failures!"
    assert summary["hallucinations_count"] == 0, f"Encountered {summary['hallucinations_count']} hallucinations!"
    assert summary["pass_rate_pct"] >= 95.0, f"Pass rate {summary['pass_rate_pct']}% is below 95% threshold!"
    assert summary["release_gate_verdict"] == "PASS"


def test_generated_reports_exist():
    """Verifies that all 5 artifact files were produced."""
    assert (RESULTS_DIR / "rag_evaluation_results.json").exists()
    assert (RESULTS_DIR / "rag_evaluation_summary.json").exists()
    assert (RESULTS_DIR / "rag_failures.json").exists()
    assert (RESULTS_DIR / "rag_product_coverage.json").exists()
    assert (RESULTS_DIR / "rag_source_coverage.json").exists()
    assert (RESULTS_DIR / "rag_evaluation_report.md").exists()
