"""
PS Product Resolver Module (Phase B).
Maps natural-language user queries to authoritative Problem Statement (PS) Canonical Products.
"""
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PS_PRODUCTS_PATH = ROOT_DIR / "data" / "ps_coverage" / "ps_products.json"


class PSProduct(BaseModel):
    id: str
    canonical_name: str
    category: str
    canonical_standard: str
    aliases: List[str] = Field(default_factory=list)
    expected_sources: Dict[str, str] = Field(default_factory=dict)
    expected_intents: List[str] = Field(default_factory=list)
    department: str = "CMD"
    scheme: str = "SCHEME-I"
    mandatory_certification: bool = True
    priority: str = "HIGH"


class PSProductMatch(BaseModel):
    product: PSProduct
    matched_term: str
    match_confidence: float
    is_standard_match: bool = False


class ProductResolver:
    """
    Authoritative Product Resolver backed strictly by the PS Product Manifest.
    Prevents hallucinated canonical products and ensures robust multi-token alias resolution.
    """
    def __init__(self, manifest_path: Path = PS_PRODUCTS_PATH):
        self.manifest_path = manifest_path
        self.products: Dict[str, PSProduct] = {}
        self.std_to_product: Dict[str, str] = {}
        self.alias_to_product: Dict[str, str] = {}
        self.sorted_aliases: List[tuple[str, str]] = []
        if self.manifest_path.exists():
            self.load()

    def load(self) -> None:
        self.products.clear()
        self.std_to_product.clear()
        self.alias_to_product.clear()
        self.sorted_aliases.clear()

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("products", []):
                p = PSProduct(**item)
                self.products[p.id] = p
                
                # Standard mapping
                std_clean = self._normalize_is(p.canonical_standard)
                self.std_to_product[std_clean] = p.id
                
                # Name mapping
                name_clean = p.canonical_name.lower().strip()
                self.alias_to_product[name_clean] = p.id
                
                # Aliases mapping
                for al in p.aliases:
                    al_clean = al.lower().strip()
                    self.alias_to_product[al_clean] = p.id

        # Sort all aliases by length descending so compound multi-word phrases take precedence
        raw_aliases = list(self.alias_to_product.items())
        raw_aliases.sort(key=lambda x: len(x[0]), reverse=True)
        self.sorted_aliases = raw_aliases

    def _normalize_is(self, is_str: str) -> str:
        if not is_str:
            return ""
        s = is_str.upper().strip()
        s = re.sub(r"\s+", " ", s)
        s = s.split(":")[0].strip()
        return s

    def resolve_from_query(self, query: str) -> Optional[PSProductMatch]:
        """Resolves raw query text to canonical PS Product with exact/phrase matching."""
        if not query:
            return None
        q_clean = query.lower().strip()

        # 1. Check sorted compound aliases with word boundary check first
        STOPWORDS = {"order", "safety", "standard", "table", "part", "unit", "system", "general", "do", "follow", "is"}
        for alias, ps_id in self.sorted_aliases:
            if alias in STOPWORDS or len(alias) < 3:
                continue
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, q_clean):
                p = self.products[ps_id]
                return PSProductMatch(
                    product=p,
                    matched_term=alias,
                    match_confidence=0.98 if len(alias) > 6 else 0.90,
                    is_standard_match=False
                )

        # 2. Sub-token matching for multi-word aliases (e.g. "tmt" + "reinforcement", "lithium" + "battery")
        TOKEN_SYNONYMS = [
            ({"tmt", "steel"}, "PS-002"),
            ({"tmt", "bar"}, "PS-002"),
            ({"tmt", "bars"}, "PS-002"),
            ({"tmt", "rebar"}, "PS-002"),
            ({"rebar", "reinforcement"}, "PS-002"),
            ({"fe", "500"}, "PS-002"),
            ({"ceiling", "fan"}, "PS-001"),
            ({"ceiling", "fans"}, "PS-001"),
            ({"lithium", "battery"}, "PS-003"),
            ({"lithium", "batteries"}, "PS-003"),
            ({"li-ion", "battery"}, "PS-003"),
            ({"gold", "jewellery"}, "PS-004"),
            ({"gold", "jewelry"}, "PS-004"),
            ({"gold", "hallmark"}, "PS-004"),
            ({"gold", "hallmarking"}, "PS-004"),
            ({"gold", "artefact"}, "PS-004"),
            ({"gold", "artefacts"}, "PS-004"),
            ({"silver", "jewellery"}, "PS-005"),
            ({"silver", "jewelry"}, "PS-005"),
            ({"silver", "hallmark"}, "PS-005"),
            ({"silver", "hallmarking"}, "PS-005"),
            ({"silver", "artefact"}, "PS-005"),
            ({"silver", "artefacts"}, "PS-005"),
            ({"led", "bulb"}, "PS-006"),
            ({"led", "lamp"}, "PS-006"),
            ({"led", "lamps"}, "PS-006"),
            ({"portland", "cement"}, "PS-007"),
            ({"opc", "cement"}, "PS-007"),
            ({"ppc", "cement"}, "PS-008"),
            ({"pozzolana", "cement"}, "PS-008"),
            ({"drinking", "water"}, "PS-009"),
            ({"packaged", "water"}, "PS-009"),
            ({"gas", "stove"}, "PS-010"),
            ({"gas", "stoves"}, "PS-010"),
            ({"pressure", "cooker"}, "PS-011"),
            ({"pressure", "cookers"}, "PS-011"),
            ({"laptop"}, "PS-015"),
            ({"laptops"}, "PS-015"),
            ({"notebook"}, "PS-015"),
            ({"notebooks"}, "PS-015"),
            ({"smartphone"}, "PS-016"),
            ({"smartphones"}, "PS-016"),
            ({"mobile", "phone"}, "PS-016"),
            ({"mobile", "phones"}, "PS-016")
        ]
        q_tokens = set(re.findall(r"\w+", q_clean))
        for token_set, ps_id in TOKEN_SYNONYMS:
            if token_set.issubset(q_tokens):
                p = self.products[ps_id]
                return PSProductMatch(
                    product=p,
                    matched_term=" + ".join(token_set),
                    match_confidence=0.92,
                    is_standard_match=False
                )

        # 3. Check for explicit IS code if no product name was mentioned
        is_pattern = re.search(r"\bIS\s*([0-9]{3,5})(?:\s*\(PART\s*([0-9A-Z]+)\))?", q_clean, re.IGNORECASE)
        if is_pattern:
            main_num = is_pattern.group(1)
            part_num = is_pattern.group(2)
            cand_std = f"IS {main_num}" + (f" (PART {part_num.upper()})" if part_num else "")
            match = self.resolve_from_standard(cand_std)
            if match:
                return match
            # Fallback to base IS
            match_base = self.resolve_from_standard(f"IS {main_num}")
            if match_base:
                return match_base

        return None

    def resolve_from_standard(self, is_code: str) -> Optional[PSProductMatch]:
        """Resolves by exact standard number or standard prefix."""
        if not is_code:
            return None
        std_clean = self._normalize_is(is_code)
        
        # Direct lookup
        ps_id = self.std_to_product.get(std_clean)
        if ps_id and ps_id in self.products:
            return PSProductMatch(
                product=self.products[ps_id],
                matched_term=is_code,
                match_confidence=1.0,
                is_standard_match=True
            )

        # Prefix search for multi-part standards
        for std_key, p_id in self.std_to_product.items():
            if std_key.startswith(std_clean) or std_clean.startswith(std_key):
                return PSProductMatch(
                    product=self.products[p_id],
                    matched_term=is_code,
                    match_confidence=0.95,
                    is_standard_match=True
                )

        return None

    def resolve_from_term(self, term: str) -> Optional[PSProductMatch]:
        """Direct lookup on normalized term or alias."""
        t_clean = term.lower().strip()
        ps_id = self.alias_to_product.get(t_clean)
        if ps_id and ps_id in self.products:
            return PSProductMatch(
                product=self.products[ps_id],
                matched_term=term,
                match_confidence=1.0,
                is_standard_match=False
            )
        return self.resolve_from_query(term)

    def get_all_products(self) -> List[PSProduct]:
        return list(self.products.values())

    def count(self) -> int:
        return len(self.products)


def main():
    parser = argparse.ArgumentParser(description="PS Product Resolver CLI")
    parser.add_argument("--manifest", type=str, default=str(PS_PRODUCTS_PATH), help="Path to ps_products.json")
    parser.add_argument("--query", type=str, required=True, help="Natural language query or product string")
    args = parser.parse_args()

    resolver = ProductResolver(manifest_path=Path(args.manifest))
    match = resolver.resolve_from_query(args.query)
    if match:
        print(f"✅ Resolved PS Product:")
        print(f"  ID        : {match.product.id}")
        print(f"  Name      : {match.product.canonical_name}")
        print(f"  Standard  : {match.product.canonical_standard}")
        print(f"  Category  : {match.product.category}")
        print(f"  Scheme    : {match.product.scheme}")
        print(f"  Confidence: {match.match_confidence:.2f}")
    else:
        print("❌ No verified PS product match found.")


if __name__ == "__main__":
    main()
