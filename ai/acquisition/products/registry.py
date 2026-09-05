"""
Product Registry Manager.
Manages authoritative BIS Product Search & Canonical Product Records (data/registry/products.jsonl).
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from ai.acquisition.products.models import ProductRecord

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PRODUCTS_PATH = ROOT_DIR / "data" / "registry" / "products.jsonl"


class ProductRegistry:
    """Master registry managing all authoritative BIS product search entities."""
    def __init__(self, registry_file: Path = PRODUCTS_PATH):
        self.registry_file = registry_file
        self.products: Dict[str, ProductRecord] = {}
        self.term_to_product: Dict[str, str] = {}
        self.std_to_products: Dict[str, List[str]] = {}
        if self.registry_file.exists():
            self.load()

    def load(self) -> None:
        self.products.clear()
        self.term_to_product.clear()
        self.std_to_products.clear()
        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        data = json.loads(line_str)
                        rec = ProductRecord(**data)
                        self.products[rec.product_id] = rec
                        term_key = rec.term.lower().strip()
                        self.term_to_product[term_key] = rec.product_id
                        if rec.canonical_name:
                            self.term_to_product[rec.canonical_name.lower().strip()] = rec.product_id
                        if rec.normalized_name:
                            self.term_to_product[rec.normalized_name.lower().strip()] = rec.product_id
                        if rec.standard_number:
                            std_clean = rec.standard_number.upper().strip().split(":")[0].strip()
                            if std_clean not in self.std_to_products:
                                self.std_to_products[std_clean] = []
                            self.std_to_products[std_clean].append(rec.product_id)
                    except Exception:
                        pass

    def get_by_id(self, product_id: str) -> Optional[ProductRecord]:
        return self.products.get(product_id)

    def get_by_term(self, term: str) -> Optional[ProductRecord]:
        t_clean = term.lower().strip()
        pid = self.term_to_product.get(t_clean)
        if pid and pid in self.products:
            return self.products[pid]
        if len(t_clean) > 5 and not t_clean.startswith("is "):
            for k, p_id in self.term_to_product.items():
                if len(k) > 5 and (k == t_clean or (len(t_clean) > 12 and k in t_clean)):
                    return self.products.get(p_id)
        return None

    def get_by_standard(self, is_number: str) -> List[ProductRecord]:
        std_clean = is_number.upper().strip().split(":")[0].strip()
        pids = self.std_to_products.get(std_clean, [])
        return [self.products[pid] for pid in pids if pid in self.products]
