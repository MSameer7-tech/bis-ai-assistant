import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from ai.retrieval.structured_retrieval_models import RetrievalResult, RetrievalSourceType

class ProductStandardIndex:
    """
    Read-only derived index over Phase 8.6 compulsory certification relationships.
    Preserves original product descriptions and unresolved statuses.
    """
    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or Path(__file__).resolve().parent.parent.parent / "data" / "catalog" / "compulsory_certification" / "product_standard_relationships.jsonl"
        self.recon_path = Path(__file__).resolve().parent.parent.parent / "data" / "catalog" / "standards" / "standard_identity_reconciliation.jsonl"
        self.records: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        if not self.dataset_path.exists():
            return
            
        # First load the reconciliation map to know which relationships got which internal IDs
        recon_map = {}
        if self.recon_path.exists():
            with open(self.recon_path, 'r', encoding='utf-8') as f:
                for line in f:
                    rec = json.loads(line)
                    rel_id = rec.get("relationship_id")
                    if rel_id:
                        recon_map[rel_id] = rec

        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                rel = json.loads(line)
                rel_id = rel.get("relationship_id")
                
                # Enrich with authoritative ID if resolved
                recon = recon_map.get(rel_id)
                if recon:
                    rel["reconciliation_status"] = recon.get("reconciliation", {}).get("status", "UNRESOLVED")
                    if rel["reconciliation_status"] == "MATCHED":
                        # We use the internal_id from the recon object if available (but Phase 8.8 didn't have it, Phase 8.10 puts it in standards_metadata.jsonl)
                        # Actually Phase 8.10 metadata holds the internal_id. We'll leave `internal_bis_id` null here and let the router join it, 
                        # OR we can assume `product_standard_index` just returns the relationship. 
                        pass
                else:
                    rel["reconciliation_status"] = "UNRESOLVED"
                    
                self.records.append(rel)

    def _to_result(self, rel: Dict[str, Any], score: float = 1.0) -> RetrievalResult:
        # Do not manufacture internal_bis_id. Leave it null or absent if unresolved.
        return RetrievalResult(
            source_type=RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP,
            record_id=rel.get("relationship_id", "unknown_rel_id"),
            score=score,
            standard_number=rel.get("standard_number", ""),
            title=rel.get("product_name", ""),
            text=f"Product: {rel.get('product_name')} -> Standard: {rel.get('standard_number')}",
            metadata={
                "original_product_description": rel.get("product_name"),
                "raw_standard_value": rel.get("standard_number"),
                "reconciliation_status": rel.get("reconciliation_status")
            },
            provenance={
                "relationship_id": rel.get("relationship_id"),
                "source_url": rel.get("source", {}).get("source_url"),
                "source_sha256": rel.get("source", {}).get("sha256"),
                "retrieved_at": rel.get("source", {}).get("retrieved_at"),
                "table_index": rel.get("table_index"),
                "row_index": rel.get("row_index")
            }
        )

    def search_by_product(self, query: str) -> List[RetrievalResult]:
        """Token overlap matching against the product description."""
        q_tokens = set(re.findall(r'\w+', query.lower()))
        if not q_tokens:
            return []
            
        scored = []
        for rel in self.records:
            prod = rel.get("product_name", "").lower()
            p_tokens = set(re.findall(r'\w+', prod))
            if not p_tokens:
                continue
                
            overlap = len(q_tokens.intersection(p_tokens))
            if overlap > 0:
                score = overlap / max(len(q_tokens), len(p_tokens))
                # For exact subset matches (e.g. query "what is the standard for household refrigerators" and product is "household refrigerators")
                if p_tokens.issubset(q_tokens):
                    score += 0.5
                    
                if score >= 0.3: # Threshold
                    scored.append((score, rel))
                    
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._to_result(r, score=s) for s, r in scored[:10]]
