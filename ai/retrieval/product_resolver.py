"""
Phase 6D: Multi-Tier Ranked Product Resolver.
Resolves arbitrary natural language product queries to authoritative BIS Standards,
Editions, Departments, and Availability status across 5 tiers:
1. Exact canonical term match (score = 1.0)
2. Alias & synonym match (score >= 0.90)
3. Word overlap / semantic token similarity on normalized title (score >= 0.70)
4. Domain taxonomy scoping
5. Ranked candidate list generation
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
PRODUCTS_FILE = REGISTRY_DIR / "products.jsonl"


class ProductResolver:
    """
    In-memory indexed product resolver loaded dynamically from data/registry/products.jsonl.
    """
    _instance = None

    def __init__(self, products_path: Optional[Path] = None):
        self.products_path = products_path or PRODUCTS_FILE
        self.terms_index: List[Dict[str, Any]] = []
        self._load_registry()

    @classmethod
    def get_instance(cls) -> "ProductResolver":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_registry(self):
        """Loads and indexes products by descending length of term for greedy matching."""
        if not self.products_path.exists():
            logger.warning(f"Products registry {self.products_path} not found.")
            return

        entries = []
        seen_terms = set()
        invalid_subterms = {
            "part 2", "part 1", "part", "section", "general", "the", "for", "and", "with",
            "cement", "steel", "pipes", "fans", "wire", "glass", "rubber", "plastic",
            "polyvinyl chloride", "pvc", "polyethylene", "carbon steel", "structural steel",
            "stainless steel", "aluminium", "aluminum", "copper", "synthetic", "leather",
            "diagonal and radial ply", "unplasticized polyvinyl chloride", "upvc",
            "commercial vehicles", "passenger cars"
        }

        def add_entry(term_text: str, item_dict: dict, conf: float, source: str):
            clean_t = term_text.strip().lower()
            if not clean_t or len(clean_t) < 4 or clean_t in invalid_subterms:
                return
            for t_var in [clean_t, clean_t.replace("—", "-").replace("–", "-"), clean_t.replace("—", " ").replace("–", " ").replace("-", " ")]:
                t_var = re.sub(r"\s+", " ", t_var).strip()
                key = (t_var, item_dict.get("standard_number"))
                if key not in seen_terms:
                    seen_terms.add(key)
                    clone = dict(item_dict)
                    clone["term"] = t_var
                    clone["confidence"] = conf
                    clone["evidence_source"] = source
                    entries.append(clone)

        with open(self.products_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    item = json.loads(line_str)
                    raw_term = item.get("term", "").strip()
                    if raw_term:
                        add_entry(raw_term, item, item.get("confidence", 0.9), item.get("evidence_source", "Registry"))
                        # Clean term if it contains specification/revision suffix (non-greedy revision check)
                        clean_raw = re.sub(r"\s*—\s*Specification\b.*|\s*\([^)]*Revision\)", "", raw_term, flags=re.IGNORECASE).strip()
                        if clean_raw != raw_term:
                            add_entry(clean_raw, item, 0.95, f"Base Term ({item.get('standard_number')})")

                    # Also index normalized_name directly as a canonical term
                    norm_name = item.get("normalized_name", "").strip()
                    if norm_name:
                        add_entry(norm_name, item, 1.0, f"Canonical Product Name ({item.get('standard_number')})")
                        # Index clean base product name without revision/specification suffix
                        base_name = re.sub(r"\s*—\s*Specification\b.*|\s*\([^)]*Revision\)", "", norm_name, flags=re.IGNORECASE).strip()
                        if base_name != norm_name:
                            add_entry(base_name, item, 1.0, f"Canonical Base Name ({item.get('standard_number')})")

                        # Index variant without "Part X:" prefix (e.g. "Portland Pozzolana Cement - Calcined Clay Based")
                        no_part_name = re.sub(r"[\s—\-]+Part\s*\d+[^:]*:\s*", " - ", base_name, flags=re.IGNORECASE).strip()
                        if no_part_name != base_name:
                            add_entry(no_part_name, item, 1.0, f"No-Part Variant ({item.get('standard_number')})")
                            short_no_part = re.sub(r"\s*for\s*general\s*lighting(?:\s*services)?", "", no_part_name, flags=re.IGNORECASE).strip()
                            if short_no_part != no_part_name:
                                add_entry(short_no_part, item, 1.0, f"Short No-Part Variant ({item.get('standard_number')})")

                        if "performance" in norm_name.lower() and "requirement" not in norm_name.lower():
                            perf_variant = re.sub(r"\bPerformance\b", "Performance Requirements", norm_name, flags=re.IGNORECASE)
                            add_entry(perf_variant, item, 1.0, f"Performance Requirements Variant ({item.get('standard_number')})")
                            short_perf = re.sub(r"\s*for\s*general\s*lighting(?:\s*services)?", "", perf_variant, flags=re.IGNORECASE).strip()
                            if short_perf != perf_variant:
                                add_entry(short_perf, item, 1.0, f"Short Performance Variant ({item.get('standard_number')})")

        # Sort by term length descending to match multi-word phrases first (e.g. 'portland slag cement' before 'portland')
        entries.sort(key=lambda x: len(x.get("term", "")), reverse=True)
        self.terms_index = entries
        logger.debug(f"Loaded {len(self.terms_index)} product resolution rules.")

    def resolve_candidates(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Returns ranked candidate standards matching a user query across multiple tiers.
        Tier 0: Explicit IS Code match (e.g. 'IS 1786' -> strictly matches IS 1786, ignoring generic phrases).
        Tier 1: Exact canonical term match.
        Tier 2: Subphrase / alias match.
        Tier 3: Token similarity on normalized title.
        """
        q_clean = query.strip()
        q_lower = q_clean.lower()
        q_tokens = set(re.findall(r"\w+", q_lower))
        candidates: List[Dict[str, Any]] = []
        seen_standards = set()

        # Tier 0: Explicit Standard Number Precedence (Strict Winner)
        is_match = re.search(r"\b(IS\s+\d+(?:\s*\([^)]+\))?|CRO\s+(?:Amendment\s+)?\d+|QCO\s+\d+)\b", q_clean, re.IGNORECASE)
        if is_match:
            explicit_std_code = is_match.group(1).strip()
            explicit_clean = explicit_std_code.lower().replace(" ", "")
            for item in self.terms_index:
                item_std = item.get("standard_number", "")
                if item_std.lower().replace(" ", "").startswith(explicit_clean):
                    if item_std not in seen_standards:
                        seen_standards.add(item_std)
                        candidates.append({
                            "product_id": item["product_id"],
                            "matched_term": explicit_std_code,
                            "normalized_name": item["normalized_name"],
                            "standard_number": item_std,
                            "current_edition": item.get("current_edition", "2024"),
                            "domain": item.get("domain"),
                            "department": item.get("department"),
                            "mandatory_certification": item.get("mandatory_certification", True),
                            "document_available": item.get("document_available", False),
                            "match_tier": "EXACT_STANDARD_CODE",
                            "confidence": 1.0,
                            "evidence_source": f"Explicit Standard Code Match ({explicit_std_code})"
                        })
            if candidates:
                return candidates[:top_k]

        # Tier 1 & 2: Exact Phrase & Word Boundary Match (Longest Term First)
        # Stop-phrases that should not trigger standalone generic matches
        GENERIC_STOP_TERMS = {
            "fifth revision", "fourth revision", "third revision", "second revision", "first revision",
            "specification", "requirements", "general requirements", "safety requirements", "particular requirements",
            "part 1", "part 2", "part 3", "part 4", "edition", "standard", "indian standard"
        }

        # Sort terms by length in descending order so specific terms match before generic sub-phrases
        sorted_terms = sorted(self.terms_index, key=lambda x: len(x.get("term", "")), reverse=True)

        for item in sorted_terms:
            term = item.get("term", "").lower()
            if not term or term in GENERIC_STOP_TERMS:
                continue

            words = [re.escape(w) for w in re.findall(r"[\w]+", term)]
            if not words:
                continue
            pattern = rf"\b" + r"[^\w]+".join(words) + rf"\b"
            if re.search(pattern, q_lower, re.IGNORECASE):
                std = item["standard_number"]
                if std not in seen_standards:
                    seen_standards.add(std)
                    score = 1.0 if q_lower == term else item.get("confidence", 0.95)
                    candidates.append({
                        "product_id": item["product_id"],
                        "matched_term": term,
                        "normalized_name": item["normalized_name"],
                        "standard_number": std,
                        "current_edition": item.get("current_edition", "2024"),
                        "domain": item.get("domain"),
                        "department": item.get("department"),
                        "mandatory_certification": item.get("mandatory_certification", True),
                        "document_available": item.get("document_available", False),
                        "match_tier": "EXACT_TERM" if q_lower == term else "SUBPHRASE_MATCH",
                        "confidence": score,
                        "evidence_source": item.get("evidence_source")
                    })

        # Tier 3: Normalized Name & Significant Token Overlap Similarity (Only as Fallback)
        STOP_WORDS = {"safety", "requirements", "particular", "general", "part", "standard", "standards", "specification", "equipment", "apparatus", "indian", "system", "code", "the", "for", "and", "under", "with", "which", "what"}
        q_sig_tokens = {t for t in q_tokens if t not in STOP_WORDS and len(t) > 2}

        if len(candidates) == 0 and len(q_sig_tokens) >= 2:
            for item in self.terms_index:
                std = item["standard_number"]
                if std in seen_standards:
                    continue

                norm_name = item.get("normalized_name", "").lower()
                norm_tokens = {t for t in re.findall(r"\w+", norm_name) if t not in STOP_WORDS and len(t) > 2}
                overlap = len(q_sig_tokens & norm_tokens)
                
                # Check significant token overlap
                if overlap >= 2:
                    score = min(0.85, 0.50 + (overlap * 0.10))
                    seen_standards.add(std)
                    candidates.append({
                        "product_id": item["product_id"],
                        "matched_term": norm_name,
                        "normalized_name": item["normalized_name"],
                        "standard_number": std,
                        "current_edition": item.get("current_edition", "2024"),
                        "domain": item.get("domain"),
                        "department": item.get("department"),
                        "mandatory_certification": item.get("mandatory_certification", True),
                        "document_available": item.get("document_available", False),
                        "match_tier": "TOKEN_SIMILARITY",
                        "confidence": score,
                        "evidence_source": item.get("evidence_source")
                    })

        # Tier weighting: EXACT_TERM > SUBPHRASE_MATCH > TOKEN_SIMILARITY
        tier_weights = {
            "EXACT_TERM": 3,
            "SUBPHRASE_MATCH": 2,
            "TOKEN_SIMILARITY": 1
        }

        def get_sort_key(x):
            tier = x.get("match_tier")
            conf = x.get("confidence", 0.0)
            length = len(x.get("matched_term", ""))
            tier_w = tier_weights.get(tier, 0)
            if tier == "SUBPHRASE_MATCH":
                return (tier_w, length, conf)
            else:
                return (tier_w, conf, length)

        candidates.sort(key=get_sort_key, reverse=True)
        return candidates[:top_k]

    def resolve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a user query to the single highest-confidence matching product.
        """
        cands = self.resolve_candidates(query, top_k=1)
        return cands[0] if cands else None


def resolve_product(query: str) -> Optional[Dict[str, Any]]:
    """Convenience function to resolve a query."""
    return ProductResolver.get_instance().resolve(query)
