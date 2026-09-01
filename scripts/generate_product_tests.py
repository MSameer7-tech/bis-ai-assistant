"""
Master Benchmark Test Dataset Generator (Phase 4J).
Extracts products, clauses, and standards from the active BIS corpus
and generates modular JSONL benchmark datasets.
"""
import os
import json
import logging
from ai.benchmark.catalog import CorpusCatalogBuilder
from ai.benchmark.generators import BenchmarkGenerators

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def generate_all_datasets(output_dir: str = "tests/benchmarks"):
    """Generates all modular benchmark datasets from the active BIS corpus."""
    logger.info("Discovering and compiling normalized BIS corpus catalog...")
    catalog = CorpusCatalogBuilder.build_catalog(
        data_dir="data",
        output_file="data/product_catalog.json"
    )

    os.makedirs(output_dir, exist_ok=True)
    stats = {}

    # 1. Product Lookup Tests (Across all products and individual domains)
    prod_cases = BenchmarkGenerators.generate_product_lookup_cases(catalog, max_per_product=3)
    prod_dir = os.path.join(output_dir, "products")
    os.makedirs(prod_dir, exist_ok=True)

    # Save all_products.jsonl
    all_prod_path = os.path.join(prod_dir, "all_products.jsonl")
    with open(all_prod_path, "w", encoding="utf-8") as f:
        for c in prod_cases:
            f.write(c.model_dump_json() + "\n")
    stats["products/all_products.jsonl"] = len(prod_cases)

    # Save per-domain JSONL files
    domain_groups = {}
    for c in prod_cases:
        domain_groups.setdefault(c.category, []).append(c)

    for domain_name, cases in domain_groups.items():
        dom_file = os.path.join(prod_dir, f"{domain_name}.jsonl")
        with open(dom_file, "w", encoding="utf-8") as f:
            for c in cases:
                f.write(c.model_dump_json() + "\n")
        stats[f"products/{domain_name}.jsonl"] = len(cases)

    # 2. Technical Value & Clause Questions Tests
    tech_cases = BenchmarkGenerators.generate_technical_value_cases(catalog)
    tech_dir = os.path.join(output_dir, "technical")
    os.makedirs(tech_dir, exist_ok=True)

    tech_file = os.path.join(tech_dir, "technical_values.jsonl")
    with open(tech_file, "w", encoding="utf-8") as f:
        for c in tech_cases:
            f.write(c.model_dump_json() + "\n")
    stats["technical/technical_values.jsonl"] = len(tech_cases)

    # 3. Safety: Unsupported Materials
    unsup_cases = BenchmarkGenerators.generate_unsupported_materials_cases()
    safety_dir = os.path.join(output_dir, "safety")
    os.makedirs(safety_dir, exist_ok=True)

    unsup_file = os.path.join(safety_dir, "unsupported_materials.jsonl")
    with open(unsup_file, "w", encoding="utf-8") as f:
        for c in unsup_cases:
            f.write(c.model_dump_json() + "\n")
    stats["safety/unsupported_materials.jsonl"] = len(unsup_cases)

    # 4. Safety: Cross-Domain Traps
    cross_cases = BenchmarkGenerators.generate_cross_domain_cases(catalog)
    cross_file = os.path.join(safety_dir, "cross_domain.jsonl")
    with open(cross_file, "w", encoding="utf-8") as f:
        for c in cross_cases:
            f.write(c.model_dump_json() + "\n")
    stats["safety/cross_domain.jsonl"] = len(cross_cases)

    # 5. Safety: Ambiguity & Underspecified Queries
    amb_cases = BenchmarkGenerators.generate_ambiguity_cases()
    amb_file = os.path.join(safety_dir, "ambiguity.jsonl")
    with open(amb_file, "w", encoding="utf-8") as f:
        for c in amb_cases:
            f.write(c.model_dump_json() + "\n")
    stats["safety/ambiguity.jsonl"] = len(amb_cases)

    # 6. Precedence: Explicit IS & Revision Collisions
    prec_cases = BenchmarkGenerators.generate_explicit_is_precedence_cases(catalog)
    prec_dir = os.path.join(output_dir, "precedence")
    os.makedirs(prec_dir, exist_ok=True)

    prec_file = os.path.join(prec_dir, "explicit_is.jsonl")
    with open(prec_file, "w", encoding="utf-8") as f:
        for c in prec_cases:
            f.write(c.model_dump_json() + "\n")
    stats["precedence/explicit_is.jsonl"] = len(prec_cases)

    # 7. Multilingual: Hinglish Product & Technical Questions
    multi_cases = BenchmarkGenerators.generate_multilingual_cases(catalog)
    multi_dir = os.path.join(output_dir, "multilingual")
    os.makedirs(multi_dir, exist_ok=True)

    multi_file = os.path.join(multi_dir, "hinglish.jsonl")
    with open(multi_file, "w", encoding="utf-8") as f:
        for c in multi_cases:
            f.write(c.model_dump_json() + "\n")
    stats["multilingual/hinglish.jsonl"] = len(multi_cases)

    # 8. Certification & Mandatory ISI Mark Tests
    cert_cases = BenchmarkGenerators.generate_certification_cases(catalog)
    cert_dir = os.path.join(output_dir, "certification")
    os.makedirs(cert_dir, exist_ok=True)

    cert_file = os.path.join(cert_dir, "certification.jsonl")
    with open(cert_file, "w", encoding="utf-8") as f:
        for c in cert_cases:
            f.write(c.model_dump_json() + "\n")
    stats["certification/certification.jsonl"] = len(cert_cases)

    total_generated = sum(
        count for k, count in stats.items() if not k.startswith("products/") or k == "products/all_products.jsonl"
    )

    print("\n" + "=" * 70)
    print("✨ CORPUS-GROUNDED BENCHMARK DATASET GENERATION COMPLETED")
    print("=" * 70)
    for file_rel, count in sorted(stats.items()):
        print(f"  📁 {file_rel:<42} : {count:>5} test cases")
    print("-" * 70)
    print(f"🎯 Total Distinct Benchmark Cases Generated: {total_generated:,}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    generate_all_datasets()
