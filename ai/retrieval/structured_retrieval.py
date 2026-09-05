import re
from typing import List, Dict, Any, Optional

from ai.retrieval.structured_retrieval_models import RetrievalResult, RetrievalSourceType
from ai.retrieval.standards_metadata_index import StandardsMetadataIndex
from ai.retrieval.product_standard_index import ProductStandardIndex

class StructuredRetrievalRouter:
    """
    Independent structured retrieval layer.
    Routes query intents to STANDARD_METADATA or PRODUCT_STANDARD_RELATIONSHIP.
    Returns DOCUMENT_EVIDENCE_REQUIRED signal for normative clause queries without invoking Phase 6 directly.
    """
    def __init__(self, metadata_index: Optional[StandardsMetadataIndex] = None, product_index: Optional[ProductStandardIndex] = None):
        self.metadata_index = metadata_index or StandardsMetadataIndex()
        self.product_index = product_index or ProductStandardIndex()
        
        # Build reverse map for relationship enrichment
        self.rel_to_internal_id = {}
        for internal_id, rec in self.metadata_index.records_by_id.items():
            for link in rec.get("relationship_links", []):
                rel_id = link.get("relationship_id")
                if rel_id:
                    self.rel_to_internal_id[rel_id] = internal_id

    def route_query(self, query: str) -> List[RetrievalResult]:
        """
        Determines the query class and executes the appropriate retrieval strategy.
        Returns a special dummy result for DOCUMENT_EVIDENCE_REQUIRED if normative.
        """
        q_lower = query.strip().lower()

        # E. Clause query (e.g. "What does clause 6.2 require?")
        if re.search(r"\b(clause|subclause|table|figure|requirement)\s+([0-9A-Z\.]+)", q_lower) and not re.search(r"standard for", q_lower):
            # We return a routing signal result to indicate higher-level RAG should invoke Phase 6
            return [RetrievalResult(
                source_type=RetrievalSourceType.DOCUMENT_EVIDENCE,
                record_id="ROUTING_SIGNAL",
                score=1.0,
                standard_number="",
                title="DOCUMENT_EVIDENCE_REQUIRED",
                text="Normative clause queries must be answered by authoritative DOCUMENT_EVIDENCE. The structured layer delegates this to Phase 6.",
                metadata={},
                provenance={}
            )]

        # A. Exact standard query & C. Lifecycle query
        std_match = re.search(r"\b(is\s*/\s*iec|is|iec)?\s*([0-9]{3,})", q_lower)
        if std_match and not ("standard for" in q_lower or "covers" in q_lower or "which standard" in q_lower):
            # Prefer STANDARD_METADATA
            exact_results = self.metadata_index.exact_lookup(query)
            if exact_results:
                return exact_results

        # B. Standard title query or D. Product-to-standard query
        # We search both product relationships and metadata titles.
        results: List[RetrievalResult] = []
        
        # 1. Product relationships
        prod_results = self.product_index.search_by_product(query)
        seen_rels = set()
        
        for p in prod_results:
            rel_id = p.record_id
            seen_rels.add(rel_id)
            
            # Enrich with internal_bis_id and authoritative metadata if resolved
            internal_id = self.rel_to_internal_id.get(rel_id)
            if internal_id:
                p.metadata["internal_bis_id"] = internal_id
                auth_meta = self.metadata_index.get_by_internal_id(internal_id)
                if auth_meta:
                    p.metadata["authoritative_status"] = auth_meta.metadata.get("status")
                    p.metadata["authoritative_title"] = auth_meta.title
            
            results.append(p)
            
        # 2. Metadata lexical search (Title)
        meta_results = self.metadata_index.lexical_search(query)
        for m in meta_results:
            # Avoid adding metadata if we already retrieved it via enriched product relationship?
            # No, keep both source types separate.
            results.append(m)

        # Sort combined results by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results

