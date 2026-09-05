import logging
from typing import List, Dict, Any, Optional

from ai.retrieval.structured_retrieval import StructuredRetrievalRouter
from ai.rag.retriever import RAGRetriever
from ai.retrieval.structured_retrieval_models import RetrievalSourceType, RetrievalResult
from ai.retrieval.integrated_retrieval_models import IntegratedRetrievalResult, EvidenceRole
from ai.retrieval.query_parser import StructuredQuery
from ai.retrieval.intent_classifier import QueryIntent

logger = logging.getLogger(__name__)

class IntegratedRetrievalOrchestrator:
    """
    Higher-level retrieval integration layer (Phase 8.12).
    Combines structured identity/catalogue lookup (Phase 8.11) with normative document evidence (Phase 6).
    Applies strict routing boundaries to prevent metadata from being treated as technical evidence.
    """

    def __init__(self, structured_router: Optional[StructuredRetrievalRouter] = None, rag_retriever: Optional[RAGRetriever] = None):
        self.structured_router = structured_router or StructuredRetrievalRouter()
        self.rag_retriever = rag_retriever or RAGRetriever()

    def retrieve(self, query: str, intent: str, sq: StructuredQuery, as_of_date: Optional[str] = None, top_k: int = 5) -> List[IntegratedRetrievalResult]:
        """
        Orchestrates retrieval across the different domains according to intent and query structure.
        """
        results: List[IntegratedRetrievalResult] = []
        
        needs_normative = intent in [QueryIntent.CLAUSE_LOOKUP.value, QueryIntent.TECHNICAL_VALUE.value]
        
        # 1. Ask Phase 8.11 Structured Router
        # It natively handles Product (B) and Exact Identity (A) queries.
        structured_raw = self.structured_router.route_query(query)
        
        for sr in structured_raw:
            # Check for normative requirement signal from structured router
            if sr.source_type == RetrievalSourceType.DOCUMENT_EVIDENCE and sr.record_id == "ROUTING_SIGNAL":
                needs_normative = True
                continue
                
            # Determine evidence role based on source
            role = EvidenceRole.IDENTITY_EVIDENCE
            if sr.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP:
                role = EvidenceRole.RELATIONSHIP_EVIDENCE
                
            integrated = IntegratedRetrievalResult(
                query=query,
                retrieval_source_type=sr.source_type,
                evidence_role=role,
                document_id=None,
                standard_number=sr.standard_number,
                internal_bis_id=sr.metadata.get("internal_bis_id"),
                relationship_id=sr.metadata.get("relationship_id") if sr.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP else None,
                title=sr.title,
                matched_text=sr.text,
                score=sr.score,
                lifecycle_status=sr.metadata.get("status") or sr.metadata.get("authoritative_status"),
                ambiguity_state=sr.metadata.get("reconciliation_status"),
                confidence=0.9 if sr.source_type == RetrievalSourceType.STANDARD_METADATA else 0.85,
                source_url=sr.provenance.get("source_url"),
                sha256=sr.provenance.get("sha256") or sr.provenance.get("source_sha256"),
                provenance=sr.provenance
            )
            results.append(integrated)
            
        # 2. Phase 6 Normative Evidence Retrieval
        if needs_normative:
            # Gather any cross-linked deterministic standard identities
            linked_standard = sq.standard_code
            if not linked_standard:
                for ir in results:
                    if ir.standard_number and ir.ambiguity_state not in ["AMBIGUOUS_MATCH", "YEAR_MISMATCH"]:
                        linked_standard = ir.standard_number
                        break
            
            # For Phase 6, we pass the query. If we established a linked standard, we could theoretically filter,
            # but we rely on the existing HybridSearchEngine to handle the standard_code in the query or from sq.
            normative_chunks = self.rag_retriever.retrieve(
                query=query,
                top_k=top_k,
                as_of_date=as_of_date
            )
            
            for chunk in normative_chunks:
                # --- PHASE 8.12 RELEVANCE VALIDATION GATE ---
                # A query being classified as normative does NOT automatically make retrieved chunks NORMATIVE_EVIDENCE.
                is_relevant = True
                
                # 1. Standard Identity Match (if known)
                if linked_standard and chunk.standard_number:
                    linked_clean = linked_standard.upper().replace(" ", "")
                    chunk_clean = chunk.standard_number.upper().replace(" ", "")
                    if linked_clean not in chunk_clean and chunk_clean not in linked_clean:
                        is_relevant = False
                
                # 2. Clause Identifier Match (if known)
                if sq.clause:
                    clause_clean = sq.clause.lower().replace("clause", "").strip()
                    chunk_clause_clean = str(chunk.clause_number).lower().replace("clause", "").strip()
                    # Must be the exact clause OR the clause string must exist in the text in a meaningful way
                    if clause_clean != chunk_clause_clean:
                        # Fallback: check text for clause mentions
                        if f"clause {clause_clean}" not in chunk.text.lower() and f"{clause_clean}." not in chunk.text.lower():
                            is_relevant = False
                            
                # 3. Evidence Text Availability
                if not chunk.text or len(chunk.text.strip()) < 10:
                    is_relevant = False
                    
                if not is_relevant:
                    logger.debug(f"Chunk rejected by Relevance Gate. Expected std {linked_standard}, clause {sq.clause}. Got std {chunk.standard_number}, clause {chunk.clause_number}")
                    continue
                # --------------------------------------------

                integrated = IntegratedRetrievalResult(
                    query=query,
                    retrieval_source_type=RetrievalSourceType.DOCUMENT_EVIDENCE,
                    evidence_role=EvidenceRole.NORMATIVE_EVIDENCE,
                    document_id=chunk.document_id,
                    standard_number=chunk.standard_number,
                    internal_bis_id=None,
                    relationship_id=None,
                    title=chunk.title or f"Document {chunk.document_id} Clause {chunk.clause_number}",
                    matched_text=chunk.text,
                    score=chunk.score,
                    lifecycle_status=chunk.temporal_status,
                    ambiguity_state=None,
                    confidence=chunk.score,
                    source_url=chunk.provenance.get("source_url"),
                    sha256=chunk.content_hash,
                    provenance=chunk.provenance
                )
                results.append(integrated)
                
        # We also handle Procedural Evidence if intent is CERTIFICATION_QCO
        if intent == QueryIntent.CERTIFICATION_QCO.value:
            # We would retrieve procedural evidence here (Phase 6 retrieves it natively)
            normative_chunks = self.rag_retriever.retrieve(
                query=query,
                top_k=top_k,
                as_of_date=as_of_date
            )
            for chunk in normative_chunks:
                integrated = IntegratedRetrievalResult(
                    query=query,
                    retrieval_source_type=RetrievalSourceType.DOCUMENT_EVIDENCE,
                    evidence_role=EvidenceRole.PROCEDURAL_EVIDENCE,
                    document_id=chunk.document_id,
                    standard_number=chunk.standard_number,
                    internal_bis_id=None,
                    relationship_id=None,
                    title=chunk.title or f"Document {chunk.document_id} Clause {chunk.clause_number}",
                    matched_text=chunk.text,
                    score=chunk.score,
                    lifecycle_status=chunk.temporal_status,
                    ambiguity_state=None,
                    confidence=chunk.score,
                    source_url=chunk.provenance.get("source_url"),
                    sha256=chunk.content_hash,
                    provenance=chunk.provenance
                )
                results.append(integrated)
                
        # Deduplicate results if normative and procedural overlapped
        unique_results = []
        seen = set()
        for r in results:
            key = (r.retrieval_source_type, r.document_id or r.internal_bis_id or r.relationship_id or r.standard_number, r.sha256)
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results
