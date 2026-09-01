"""
Master Benchmark Runner (Phase 4G).
Executes benchmark datasets across RAGPipeline with multi-metric evaluation and latency tracking.
"""
import os
import time
import json
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional
from ai.benchmark.models import (
    BenchmarkCase, CaseEvaluationResult, CategoryMetrics, MasterBenchmarkReport, FailureSeverity
)
from ai.benchmark.evaluator import BenchmarkEvaluator
from ai.rag.pipeline import RAGPipeline


class BenchmarkRunner:
    """Executes corpus-grounded benchmark cases and produces aggregated reports."""

    def __init__(self, pipeline: Optional[RAGPipeline] = None):
        self.pipeline = pipeline or RAGPipeline()

    @staticmethod
    def load_cases_from_file(file_path: str) -> List[BenchmarkCase]:
        """Loads benchmark cases from a single JSON or JSONL file."""
        cases: List[BenchmarkCase] = []
        if not os.path.exists(file_path):
            return cases

        if file_path.endswith(".jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        cases.append(BenchmarkCase.model_validate_json(line_str))
        elif file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        cases.append(BenchmarkCase.model_validate(item))
                elif isinstance(data, dict) and "cases" in data:
                    for item in data["cases"]:
                        cases.append(BenchmarkCase.model_validate(item))
        return cases

    @staticmethod
    def load_cases_from_directory(dir_path: str) -> List[BenchmarkCase]:
        """Recursively loads all benchmark cases from JSON and JSONL files in directory."""
        cases: List[BenchmarkCase] = []
        for ext in ["*.jsonl", "*.json"]:
            for f_path in glob.glob(os.path.join(dir_path, "**", ext), recursive=True):
                cases.extend(BenchmarkRunner.load_cases_from_file(f_path))
        return cases

    def run_cases(
        self,
        cases: List[BenchmarkCase],
        max_cases: Optional[int] = None,
        category_filter: Optional[str] = None,
        quiet: bool = False,
        corpus_stats: Optional[Dict[str, Any]] = None
    ) -> MasterBenchmarkReport:
        """Runs the benchmark against the provided cases."""
        if category_filter:
            cases = [c for c in cases if category_filter.lower() in c.category.lower()]

        if max_cases and len(cases) > max_cases:
            cases = cases[:max_cases]

        total = len(cases)
        results: List[CaseEvaluationResult] = []

        cat_groups: Dict[str, List[CaseEvaluationResult]] = {}
        qt_groups: Dict[str, List[CaseEvaluationResult]] = {}

        if not quiet:
            print(f"🚀 Launching Master Benchmark over {total} test cases...")

        for idx, case in enumerate(cases, 1):
            t0 = time.perf_counter()
            try:
                if hasattr(self.pipeline, "answer_question"):
                    answer = self.pipeline.answer_question(case.query)
                elif hasattr(self.pipeline, "query"):
                    answer = self.pipeline.query(case.query)
                else:
                    raise AttributeError("Pipeline has neither answer_question nor query method")
            except Exception as e:
                # Execution exception
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                res = CaseEvaluationResult(
                    test_id=case.id,
                    category=case.category,
                    query=case.query,
                    query_type=case.query_type,
                    passed=False,
                    failure_severity=FailureSeverity.CRITICAL,
                    expected={"status": case.expected_status},
                    actual={"status": "ERROR"},
                    elapsed_ms=elapsed_ms,
                    error_message=f"Pipeline exception: {str(e)}"
                )
                results.append(res)
                continue

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            res = BenchmarkEvaluator.evaluate_case(case, answer, elapsed_ms)
            results.append(res)

            # Grouping
            cat_groups.setdefault(case.category, []).append(res)
            qt_groups.setdefault(case.query_type, []).append(res)

            if not quiet and (idx % 50 == 0 or idx == total or not res.passed):
                status_symbol = "✅" if res.passed else f"❌ [{res.failure_severity.value if res.failure_severity else 'FAIL'}]"
                print(f"[{idx:>4}/{total}] {status_symbol} {case.id:<22} ({elapsed_ms:>5.1f}ms): {case.query[:50]}...")

        # Aggregate Metrics
        categories_metrics = {
            cat: self._compute_metrics(cat, res_list) for cat, res_list in cat_groups.items()
        }
        query_types_metrics = {
            qt: self._compute_metrics(qt, res_list) for qt, res_list in qt_groups.items()
        }

        total_passed = sum(1 for r in results if r.passed)
        critical_fails = sum(1 for r in results if r.failure_severity == FailureSeverity.CRITICAL)
        high_fails = sum(1 for r in results if r.failure_severity == FailureSeverity.HIGH)
        medium_fails = sum(1 for r in results if r.failure_severity == FailureSeverity.MEDIUM)
        low_fails = sum(1 for r in results if r.failure_severity == FailureSeverity.LOW)

        overall_acc = (total_passed / total) if total > 0 else 0.0
        gate_passed = (critical_failures := critical_fails) == 0 and overall_acc >= 0.95

        return MasterBenchmarkReport(
            timestamp=datetime.now().isoformat(),
            corpus_stats=corpus_stats or {},
            total_cases=total,
            passed_cases=total_passed,
            failed_cases=total - total_passed,
            overall_accuracy=overall_acc,
            critical_failures=critical_fails,
            high_failures=high_fails,
            medium_failures=medium_fails,
            low_failures=low_fails,
            categories=categories_metrics,
            query_types=query_types_metrics,
            results=results,
            release_gate_passed=gate_passed
        )

    @staticmethod
    def _compute_metrics(name: str, res_list: List[CaseEvaluationResult]) -> CategoryMetrics:
        tot = len(res_list)
        pas = sum(1 for r in res_list if r.passed)
        crit = sum(1 for r in res_list if r.failure_severity == FailureSeverity.CRITICAL)
        high = sum(1 for r in res_list if r.failure_severity == FailureSeverity.HIGH)
        med = sum(1 for r in res_list if r.failure_severity == FailureSeverity.MEDIUM)
        low = sum(1 for r in res_list if r.failure_severity == FailureSeverity.LOW)
        avg_lat = sum(r.elapsed_ms for r in res_list) / tot if tot > 0 else 0.0

        # Safety rate: percentage of negative/safety/ambiguity cases that correctly abstained
        safety_cases = [r for r in res_list if r.expected.get("status") in ("ABSTAINED", "CLARIFICATION_REQUIRED")]
        safety_rate = (sum(1 for r in safety_cases if r.passed) / len(safety_cases)) if safety_cases else 1.0

        top1_acc = (sum(1 for r in res_list if r.checks.get("standard_top1", True) and r.passed) / tot) if tot > 0 else 0.0
        top3_acc = (sum(1 for r in res_list if r.checks.get("standard_retrieved", True) and r.passed) / tot) if tot > 0 else 0.0

        return CategoryMetrics(
            name=name,
            total_cases=tot,
            passed_cases=pas,
            failed_cases=tot - pas,
            accuracy=(pas / tot) if tot > 0 else 0.0,
            top1_accuracy=top1_acc,
            top3_accuracy=top3_acc,
            safety_rate=safety_rate,
            critical_failures=crit,
            high_failures=high,
            medium_failures=med,
            low_failures=low,
            avg_latency_ms=avg_lat
        )
