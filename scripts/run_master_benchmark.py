"""
CLI Runner for BIS AI Assistant Master Benchmark (Phase 4).
Usage:
  PYTHONPATH=. .venv/bin/python scripts/run_master_benchmark.py --smoke
  PYTHONPATH=. .venv/bin/python scripts/run_master_benchmark.py --dataset tests/benchmarks/safety
  PYTHONPATH=. .venv/bin/python scripts/run_master_benchmark.py --category construction
  PYTHONPATH=. .venv/bin/python scripts/run_master_benchmark.py --full
"""
import os
import sys
import argparse
from ai.benchmark.runner import BenchmarkRunner
from ai.benchmark.reporters import BenchmarkReporter
from ai.benchmark.catalog import CorpusCatalogBuilder


def main():
    parser = argparse.ArgumentParser(description="BIS AI Assistant Master Benchmark Runner")
    parser.add_argument("--dataset", "-d", type=str, default="tests/benchmarks",
                        help="Path to dataset directory or JSONL file (default: tests/benchmarks)")
    parser.add_argument("--category", "-c", type=str, default=None,
                        help="Filter cases by category name (e.g. safety, construction, technical)")
    parser.add_argument("--smoke", action="store_true",
                        help="Run fast smoke benchmark tier (~150 cases)")
    parser.add_argument("--max-cases", "-n", type=int, default=None,
                        help="Maximum test cases to execute")
    parser.add_argument("--report", "-r", type=str, default="data/evaluation/master_benchmark_report.json",
                        help="Path to save detailed JSON evaluation report")
    parser.add_argument("--markdown", "-m", type=str, default="data/evaluation/master_benchmark_report.md",
                        help="Path to save GitHub markdown evaluation summary")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Quiet execution (suppress per-case outputs)")

    args = parser.parse_args()

    # Load corpus stats
    catalog = CorpusCatalogBuilder.build_catalog(output_file=None)
    corpus_stats = {
        "total_documents": 110,
        "total_products": len(catalog.products),
        "total_standards": len(catalog.standards),
        "total_chunks": 1961
    }

    # Load cases
    if os.path.isfile(args.dataset):
        cases = BenchmarkRunner.load_cases_from_file(args.dataset)
    else:
        cases = BenchmarkRunner.load_cases_from_directory(args.dataset)

    # Smoke tier selection: sample cases across categories
    if args.smoke and not args.max_cases:
        smoke_cases = []
        cat_groups = {}
        for c in cases:
            cat_groups.setdefault(c.category, []).append(c)
        for cat, group in cat_groups.items():
            smoke_cases.extend(group[:15])  # Up to 15 cases per category
        cases = smoke_cases

    if not cases:
        print(f"❌ Error: No benchmark cases found at '{args.dataset}'")
        sys.exit(1)

    runner = BenchmarkRunner()
    report = runner.run_cases(
        cases=cases,
        max_cases=args.max_cases,
        category_filter=args.category,
        quiet=args.quiet,
        corpus_stats=corpus_stats
    )

    # Output Reports
    BenchmarkReporter.print_terminal_report(report)
    BenchmarkReporter.save_json_report(report, args.report)
    BenchmarkReporter.save_markdown_report(report, args.markdown)

    print(f"📁 Full JSON report saved to: {args.report}")
    print(f"📁 Markdown report saved to:  {args.markdown}")

    # Release Gate Exit Code: 0 if passed, 1 if critical failures or <95% accuracy
    if not report.release_gate_passed:
        print(f"❌ Release Gate FAILED! Critical Failures: {report.critical_failures}")
        sys.exit(1)
    else:
        print("🎉 Release Gate PASSED! Zero critical failures and high precision.")
        sys.exit(0)


if __name__ == "__main__":
    main()
