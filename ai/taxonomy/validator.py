"""
Taxonomy validation and lookup for BIS product domains, categories, and types.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "taxonomy" / "product_domains.json"


class TaxonomyValidator:
    """
    Validates that product domains, categories, and types belong to the controlled taxonomy.
    """

    def __init__(self, taxonomy_file: Optional[Path] = None):
        self.taxonomy_path = taxonomy_file or TAXONOMY_PATH
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found at: {self.taxonomy_path}")
        
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.version = data.get("version", "1.0.0")
        self.domains: Dict[str, Any] = data.get("domains", {})

    def get_valid_domains(self) -> List[str]:
        return list(self.domains.keys())

    def get_valid_categories(self, domain: str) -> List[str]:
        dom_data = self.domains.get(domain)
        if not dom_data:
            return []
        return list(dom_data.get("categories", {}).keys())

    def get_valid_types(self, domain: str, category: str) -> List[str]:
        dom_data = self.domains.get(domain, {})
        cat_data = dom_data.get("categories", {})
        return cat_data.get(category, [])

    def validate(
        self,
        domain: Optional[str],
        category: Optional[str] = None,
        product_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates the domain, category, and type hierarchy.
        
        Returns:
            (is_valid, error_message)
        """
        if not domain:
            return False, "product_domain is required"

        if domain not in self.domains:
            valid_doms = ", ".join(self.get_valid_domains())
            return False, f"Invalid domain '{domain}'. Must be one of: {valid_doms}"

        if category:
            valid_cats = self.get_valid_categories(domain)
            if category not in valid_cats:
                return False, f"Invalid category '{category}' for domain '{domain}'. Must be one of: {', '.join(valid_cats)}"

            if product_type:
                valid_types = self.get_valid_types(domain, category)
                if product_type not in valid_types:
                    return False, f"Invalid product_type '{product_type}' for domain/category '{domain}/{category}'. Must be one of: {', '.join(valid_types)}"

        return True, None


_default_validator: Optional[TaxonomyValidator] = None


def get_taxonomy_validator() -> TaxonomyValidator:
    global _default_validator
    if _default_validator is None:
        _default_validator = TaxonomyValidator()
    return _default_validator
