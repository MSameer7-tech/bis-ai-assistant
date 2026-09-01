"""
Unit tests for Master Benchmark datasets and schema integrity (Phase 4I).
"""
import os
import glob
import pytest
from ai.benchmark.models import BenchmarkCase
from ai.benchmark.catalog import CorpusCatalogBuilder, CorpusCatalog
from ai.benchmark.runner import BenchmarkRunner


def test_catalog_builder_extracts_corpus():
    catalog = CorpusCatalogBuilder.build_catalog(output_file=None)
    assert isinstance(catalog, CorpusCatalog)
    assert len(catalog.products) > 50
    assert len(catalog.standards) > 50
    assert len(catalog.requirements) > 10
    assert len(catalog.domains) >= 5


def test_benchmark_files_exist():
    expected_files = [
        "tests/benchmarks/products/all_products.jsonl",
        "tests/benchmarks/technical/technical_values.jsonl",
        "tests/benchmarks/safety/unsupported_materials.jsonl",
        "tests/benchmarks/safety/cross_domain.jsonl",
        "tests/benchmarks/safety/ambiguity.jsonl",
        "tests/benchmarks/precedence/explicit_is.jsonl",
        "tests/benchmarks/multilingual/hinglish.jsonl",
        "tests/benchmarks/certification/certification.jsonl"
    ]
    for ef in expected_files:
        assert os.path.exists(ef), f"Missing expected benchmark file: {ef}"
        assert os.path.getsize(ef) > 0, f"Benchmark file is empty: {ef}"


def test_all_benchmark_cases_are_valid_pydantic_models():
    all_files = glob.glob("tests/benchmarks/**/*.jsonl", recursive=True)
    assert len(all_files) >= 8

    total_validated = 0
    for f_path in all_files:
        cases = BenchmarkRunner.load_cases_from_file(f_path)
        assert len(cases) > 0, f"No cases loaded from {f_path}"
        for c in cases:
            assert isinstance(c, BenchmarkCase)
            assert c.id.strip() != ""
            assert c.query.strip() != ""
            assert c.expected_status in ("VERIFIED", "ABSTAINED", "CLARIFICATION_REQUIRED")
            total_validated += 1

    assert total_validated > 1500, f"Expected >1500 total cases, validated {total_validated}"


def test_safety_datasets_strict_abstention_contract():
    safety_files = [
        "tests/benchmarks/safety/unsupported_materials.jsonl",
        "tests/benchmarks/safety/cross_domain.jsonl",
        "tests/benchmarks/safety/ambiguity.jsonl"
    ]
    for sf in safety_files:
        cases = BenchmarkRunner.load_cases_from_file(sf)
        assert len(cases) > 0
        for c in cases:
            assert c.expected_status == "ABSTAINED"


def test_precedence_datasets_structure():
    cases = BenchmarkRunner.load_cases_from_file("tests/benchmarks/precedence/explicit_is.jsonl")
    assert len(cases) > 50
    for c in cases:
        assert c.expected_standard is not None
        assert len(c.expected_standard) >= 3
