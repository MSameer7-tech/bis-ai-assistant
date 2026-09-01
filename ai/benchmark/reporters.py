"""
Master Benchmark Reporters & Release Gate Auditing (Phase 4H).
Renders terminal tables, structured JSON, and GitHub markdown reports.
"""
import os
import json
from ai.benchmark.models import MasterBenchmarkReport


class BenchmarkReporter:
    """Renders comprehensive benchmark reports across terminal, JSON, and Markdown."""

    @classmethod
    def print_terminal_report(cls, report: MasterBenchmarkReport):
        """Prints a clean, formatted executive summary table to terminal stdout."""
        print("\n" + "=" * 80)
        print("🏛️  BUREAU OF INDIAN STANDARDS — MASTER BENCHMARK EVALUATION")
        print("=" * 80)

        # Corpus Stats
        c = report.corpus_stats
        print(f"Corpus Scope: {c.get('total_documents', 110)} Documents | {c.get('total_products', 179)} Products | {c.get('total_chunks', 1961)} Chunks | {c.get('total_standards', 107)} Standards")
        print(f"Total Test Cases Executed: {report.total_cases:,}")
        print("-" * 80)

        # Category Breakdown
        print(f"{'CATEGORY':<28} | {'CASES':<7} | {'PASSED':<7} | {'ACCURACY':<10} | {'SAFETY RATE':<11} | {'LATENCY'}")
        print("-" * 80)
        for cat_name, m in sorted(report.categories.items()):
            safety_str = f"{m.safety_rate*100:.1f}%" if "safety" in cat_name or "ambiguity" in cat_name else "N/A"
            print(f"{cat_name:<28} | {m.total_cases:<7} | {m.passed_cases:<7} | {m.accuracy*100:>8.2f}% | {safety_str:>11} | {m.avg_latency_ms:.1f} ms")

        print("-" * 80)

        # Query Type Breakdown
        print(f"{'QUERY TYPE':<28} | {'CASES':<7} | {'PASSED':<7} | {'ACCURACY':<10} | {'CRITICAL':<8} | {'HIGH':<6}")
        print("-" * 80)
        for qt_name, m in sorted(report.query_types.items()):
            print(f"{qt_name:<28} | {m.total_cases:<7} | {m.passed_cases:<7} | {m.accuracy*100:>8.2f}% | {m.critical_failures:<8} | {m.high_failures:<6}")

        print("-" * 80)

        # Failure Severities
        print("📊 SEVERITY SUMMARY:")
        print(f"  🔴 CRITICAL FAILURES: {report.critical_failures} (Threshold: 0)")
        print(f"  🟠 HIGH FAILURES:     {report.high_failures}")
        print(f"  🟡 MEDIUM FAILURES:   {report.medium_failures}")
        print(f"  ⚪ LOW FAILURES:      {report.low_failures}")
        print("-" * 80)

        # Release Gate Verdict
        gate_status = "✅ PASSED" if report.release_gate_passed else "❌ FAILED"
        print(f"🎯 MASTER RELEASE GATE VERDICT: {gate_status}")
        print(f"   - Overall Accuracy:   {report.overall_accuracy*100:.2f}% (Passed: {report.passed_cases}/{report.total_cases})")
        print(f"   - Critical Failures:  {report.critical_failures} == 0 -> {'MET' if report.critical_failures == 0 else 'VIOLATED'}")
        print("=" * 80 + "\n")

    @classmethod
    def save_json_report(cls, report: MasterBenchmarkReport, file_path: str):
        """Saves full structured benchmark results to JSON file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

    @classmethod
    def save_markdown_report(cls, report: MasterBenchmarkReport, file_path: str):
        """Saves executive markdown summary for documentation and walkthroughs."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        lines = [
            "# BIS AI Assistant Master Benchmark Report",
            f"**Execution Timestamp**: `{report.timestamp}`",
            "",
            "## Corpus Scope",
            f"- **Documents**: `{report.corpus_stats.get('total_documents', 110)}`",
            f"- **Unique Products**: `{report.corpus_stats.get('total_products', 179)}`",
            f"- **Unique Standards**: `{report.corpus_stats.get('total_standards', 107)}`",
            f"- **Total Chunks**: `{report.corpus_stats.get('total_chunks', 1961)}`",
            "",
            "## Category Performance Breakdown",
            "",
            "| Category | Total Cases | Passed | Accuracy | Safety Rate | Avg Latency |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |"
        ]

        for cat_name, m in sorted(report.categories.items()):
            safety_str = f"{m.safety_rate*100:.1f}%" if "safety" in cat_name or "ambiguity" in cat_name else "N/A"
            lines.append(f"| `{cat_name}` | {m.total_cases} | {m.passed_cases} | **{m.accuracy*100:.2f}%** | {safety_str} | {m.avg_latency_ms:.1f} ms |")

        lines.extend([
            "",
            "## Severity & Safety Invariants",
            f"- 🔴 **Critical Failures**: `{report.critical_failures}` (Target: 0)",
            f"- 🟠 **High Failures**: `{report.high_failures}`",
            f"- 🟡 **Medium Failures**: `{report.medium_failures}`",
            f"- ⚪ **Low Failures**: `{report.low_failures}`",
            "",
            f"## Release Gate Status: **{'✅ PASSED' if report.release_gate_passed else '❌ FAILED'}**",
            f"- **Overall Accuracy**: `{report.overall_accuracy*100:.2f}%` ({report.passed_cases}/{report.total_cases})"
        ])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
