"""
PS Discovery Validator Module (Phase F).
Audits and validates the completeness of data/ps_coverage/source_registry.json against expected sources.
"""
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY = ROOT_DIR / "data" / "ps_coverage" / "source_registry.json"


class DiscoveryValidator:
    """
    Audits the discovered source registry against expected product regulatory requirements.
    """
    def __init__(self, registry_path: Path = DEFAULT_REGISTRY):
        self.registry_path = registry_path
        self.registry: Dict[str, Any] = {}
        if self.registry_path.exists():
            self.load()

    def load(self) -> None:
        with open(self.registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def validate(self) -> Dict[str, Any]:
        products = self.registry.get("products", {})
        total = len(products)
        
        counts = {
            "standards": 0,
            "qcos": 0,
            "product_manuals": 0,
            "sit": 0,
            "schemes": 0,
            "tests": 0,
            "laboratories": 0,
            "licences": 0
        }

        flaws: List[Dict[str, Any]] = []

        for ps_id, p in products.items():
            expected = p.get("expected_sources", {})
            p_flaws = []

            # Standards
            if len(p.get("standards", [])) > 0:
                counts["standards"] += 1
            elif expected.get("standard") == "required":
                p_flaws.append("Missing required Indian Standard")

            # QCOs
            if len(p.get("qcos", [])) > 0:
                counts["qcos"] += 1
            elif expected.get("qco") == "required":
                p_flaws.append("Missing required QCO statutory order")

            # Product Manuals
            if len(p.get("product_manuals", [])) > 0:
                counts["product_manuals"] += 1
            elif expected.get("product_manual") == "required":
                p_flaws.append("Missing required Product Manual")

            # SIT
            if len(p.get("sit", [])) > 0:
                counts["sit"] += 1
            elif expected.get("sit") == "required":
                p_flaws.append("Missing required Scheme of Inspection & Testing (SIT)")

            # Schemes
            if len(p.get("schemes", [])) > 0:
                counts["schemes"] += 1
            elif expected.get("scheme") == "required":
                p_flaws.append("Missing required Conformity Scheme")

            # Tests
            if len(p.get("tests", [])) > 0:
                counts["tests"] += 1
            elif expected.get("testing") == "required":
                p_flaws.append("Missing required Test specifications")

            # Laboratories
            if len(p.get("laboratories", [])) > 0:
                counts["laboratories"] += 1
            elif expected.get("laboratory") == "required":
                p_flaws.append("Missing required Testing Laboratories")

            # Licences / CRS / Hallmarking
            if len(p.get("licences", [])) > 0:
                counts["licences"] += 1
            elif expected.get("licence") == "required":
                p_flaws.append("Missing required Licences / CRS / Hallmarking records")

            if p_flaws:
                flaws.append({
                    "ps_id": ps_id,
                    "product_name": p.get("product_name"),
                    "flaws": p_flaws
                })

        is_valid = len(flaws) == 0
        return {
            "total_products": total,
            "counts": counts,
            "is_valid": is_valid,
            "flaws": flaws
        }

    def print_report(self, results: Dict[str, Any]) -> None:
        total = results["total_products"]
        counts = results["counts"]
        print("==================================================")
        print("🏛️  BIS PS DISCOVERY VALIDATION REPORT")
        print("==================================================")
        print(f"Total PS Products Discovered : {total}")
        print(f"Standards Coverage           : {counts['standards']}/{total}")
        print(f"QCO Statutory Orders         : {counts['qcos']}/{total}")
        print(f"Conformity Schemes           : {counts['schemes']}/{total}")
        print(f"Product Manuals              : {counts['product_manuals']}/{total}")
        print(f"SIT Testing Schedules        : {counts['sit']}/{total}")
        print(f"Prescribed Compliance Tests  : {counts['tests']}/{total}")
        print(f"Recognized Laboratories      : {counts['laboratories']}/{total}")
        print(f"Licence / CRS / Hallmarking  : {counts['licences']}/{total}")
        print("--------------------------------------------------")
        if results["is_valid"]:
            print("🎯 VALIDATION RESULT: ✅ ALL REQUIRED SOURCES PRESENT & VERIFIED")
        else:
            print(f"⚠️  VALIDATION RESULT: ❌ {len(results['flaws'])} PRODUCTS REQUIRE ATTENTION")
            for f in results["flaws"]:
                print(f"  - {f['ps_id']} ({f['product_name']}):")
                for item in f["flaws"]:
                    print(f"      • {item}")
        print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="PS Discovery Validator CLI")
    parser.add_argument("--registry", type=str, default=str(DEFAULT_REGISTRY), help="Path to source_registry.json")
    args = parser.parse_args()

    validator = DiscoveryValidator(registry_path=Path(args.registry))
    res = validator.validate()
    validator.print_report(res)
    if not res["is_valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
