"""
PS Coverage Auditor Module (Phase P).
Computes formal, audit-verified coverage metrics for all Problem Statement commodities.
"""
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

from ai.coverage.product_resolver import ProductResolver, PSProduct
from ai.acquisition.provenance.registry import EvidenceRegistry

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MANIFEST = ROOT_DIR / "data" / "ps_coverage" / "ps_products.json"
DEFAULT_REGISTRY = ROOT_DIR / "data" / "ps_coverage" / "source_registry.json"
DEFAULT_REPORT = ROOT_DIR / "data" / "ps_coverage" / "coverage_report.json"


class PSCoverageAuditor:
    """
    Formal Coverage Auditor checking every Problem Statement commodity across all regulatory dimensions.
    """
    def __init__(
        self,
        manifest_path: Path = DEFAULT_MANIFEST,
        registry_path: Path = DEFAULT_REGISTRY
    ):
        self.manifest_path = manifest_path
        self.registry_path = registry_path
        self.resolver = ProductResolver(manifest_path)
        self.evidence_reg = EvidenceRegistry()
        self.registry: Dict[str, Any] = {}
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry = json.load(f)

    def audit(self, output_report: Path = DEFAULT_REPORT) -> Dict[str, Any]:
        """Runs the comprehensive coverage audit."""
        products_dict = self.registry.get("products", {})
        total_products = self.resolver.count()

        resolved_count = 0
        standard_count = 0
        qco_count = 0
        scheme_count = 0
        manual_count = 0
        sit_count = 0
        test_count = 0
        lab_count = 0
        licence_count = 0
        evidence_count = 0

        fully_covered: List[str] = []
        partially_covered: List[Dict[str, Any]] = []
        uncovered: List[str] = []

        for p in self.resolver.get_all_products():
            reg_entry = products_dict.get(p.id)
            if not reg_entry:
                uncovered.append(p.id)
                continue

            resolved_count += 1
            expected = p.expected_sources
            missing_dimensions = []

            # 1. Standard
            if len(reg_entry.get("standards", [])) > 0:
                standard_count += 1
            else:
                missing_dimensions.append("STANDARD")

            # 2. QCO
            if len(reg_entry.get("qcos", [])) > 0:
                qco_count += 1
            elif expected.get("qco") == "required":
                missing_dimensions.append("QCO")

            # 3. Scheme
            if len(reg_entry.get("schemes", [])) > 0:
                scheme_count += 1
            elif expected.get("scheme") == "required":
                missing_dimensions.append("SCHEME")

            # 4. Product Manual
            if len(reg_entry.get("product_manuals", [])) > 0:
                manual_count += 1
            elif expected.get("product_manual") == "required":
                missing_dimensions.append("PRODUCT_MANUAL")

            # 5. SIT
            if len(reg_entry.get("sit", [])) > 0:
                sit_count += 1
            elif expected.get("sit") == "required":
                missing_dimensions.append("SIT")

            # 6. Tests
            if len(reg_entry.get("tests", [])) > 0:
                test_count += 1
            elif expected.get("testing") == "required":
                missing_dimensions.append("TEST")

            # 7. Laboratories
            if len(reg_entry.get("laboratories", [])) > 0:
                lab_count += 1
            elif expected.get("laboratory") == "required":
                missing_dimensions.append("LABORATORY")

            # 8. Licences
            if len(reg_entry.get("licences", [])) > 0:
                licence_count += 1
            elif expected.get("licence") == "required":
                missing_dimensions.append("LICENCE")

            # 9. Evidence Records
            std_clean = p.canonical_standard.upper().split(":")[0].strip()
            evs = self.evidence_reg.get_by_entity(std_clean)
            if not evs:
                std_base = std_clean.split("(")[0].strip()
                evs = self.evidence_reg.get_by_entity(std_base)
            if evs:
                evidence_count += 1
            else:
                missing_dimensions.append("EVIDENCE")

            if not missing_dimensions:
                fully_covered.append(p.id)
            else:
                partially_covered.append({
                    "id": p.id,
                    "name": p.canonical_name,
                    "standard": p.canonical_standard,
                    "missing": missing_dimensions
                })

        overall_coverage_pct = round((len(fully_covered) / total_products) * 100.0, 2) if total_products > 0 else 0.0

        report = {
            "version": "1.0",
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "total_ps_products": total_products,
            "resolved_products": resolved_count,
            "standards_coverage": f"{standard_count}/{total_products}",
            "qco_coverage": f"{qco_count}/{total_products}",
            "scheme_coverage": f"{scheme_count}/{total_products}",
            "product_manual_coverage": f"{manual_count}/{total_products}",
            "sit_coverage": f"{sit_count}/{total_products}",
            "test_coverage": f"{test_count}/{total_products}",
            "laboratory_coverage": f"{lab_count}/{total_products}",
            "licence_coverage": f"{licence_count}/{total_products}",
            "evidence_coverage": f"{evidence_count}/{total_products}",
            "fully_covered_count": len(fully_covered),
            "partially_covered_count": len(partially_covered),
            "uncovered_count": len(uncovered),
            "overall_ps_coverage_pct": overall_coverage_pct,
            "fully_covered_products": fully_covered,
            "partially_covered_details": partially_covered,
            "uncovered_details": uncovered,
            "gate_passed": overall_coverage_pct == 100.0
        }

        output_report.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def print_audit_summary(self, report: Dict[str, Any]) -> None:
        print("==================================================")
        print("🏛️  BUREAU OF INDIAN STANDARDS — PS COVERAGE AUDIT")
        print("==================================================")
        print(f"Total PS Products Manifest  : {report['total_ps_products']}")
        print(f"Products Resolved           : {report['resolved_products']} / {report['total_ps_products']}")
        print(f"Standards Coverage          : {report['standards_coverage']}")
        print(f"QCO Statutory Orders        : {report['qco_coverage']}")
        print(f"Conformity Schemes          : {report['scheme_coverage']}")
        print(f"Product Manuals             : {report['product_manual_coverage']}")
        print(f"SIT Testing Schedules       : {report['sit_coverage']}")
        print(f"Prescribed Compliance Tests : {report['test_coverage']}")
        print(f"Recognized Laboratories     : {report['laboratory_coverage']}")
        print(f"Licence / CRS / Hallmarking : {report['licence_coverage']}")
        print(f"Evidence & Provenance Bound : {report['evidence_coverage']}")
        print("--------------------------------------------------")
        print(f"FULLY COVERED COMMODITIES   : {report['fully_covered_count']} / {report['total_ps_products']}")
        print(f"PARTIALLY COVERED           : {report['partially_covered_count']}")
        print(f"UNCOVERED                   : {report['uncovered_count']}")
        print(f"OVERALL PS COVERAGE         : {report['overall_ps_coverage_pct']}%")
        print("--------------------------------------------------")
        if report["gate_passed"]:
            print("🎯 PS COVERAGE GATE: ✅ PASSED (100.00% AUDITED COVERAGE)")
        else:
            print(f"⚠️  PS COVERAGE GATE: ❌ FAILED ({report['overall_ps_coverage_pct']}% < 100.00%)")
            for p in report["partially_covered_details"]:
                print(f"  • {p['id']} - {p['name']} ({p['standard']}): Missing {p['missing']}")
        print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Run PS Coverage Auditor")
    parser.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST), help="Path to ps_products.json")
    parser.add_argument("--registry", type=str, default=str(DEFAULT_REGISTRY), help="Path to source_registry.json")
    parser.add_argument("--output", type=str, default=str(DEFAULT_REPORT), help="Path to coverage_report.json")
    args = parser.parse_args()

    auditor = PSCoverageAuditor(manifest_path=Path(args.manifest), registry_path=Path(args.registry))
    report = auditor.audit(output_report=Path(args.output))
    auditor.print_audit_summary(report)
    if not report["gate_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
