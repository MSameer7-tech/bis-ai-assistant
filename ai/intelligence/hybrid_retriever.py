"""
Unified 3-Way Hybrid Retrieval Engine (Phase 5 Sub-Phase 5B).
Fuses Dense Vector Search, BM25 / Lexical Sparse Search, and Knowledge Graph Subgraph Traversal.
Passes candidates through the regulatory Evidence Gate for evidentiary grounding.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from collections import defaultdict
from pydantic import BaseModel, Field

from ai.vectorstore.hybrid_search import HybridSearchEngine
from ai.rag.models import RetrievedChunk
from ai.intelligence.query_understanding import ParsedQuery
from ai.rag.evidence_gate import EvidenceGate, EvidenceEvaluationResult, GateDecision
from ai.acquisition.provenance.registry import EvidenceRegistry
from ai.acquisition.provenance.models import EvidentiaryStrength

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RELATIONSHIPS_PATH = DATA_DIR / "registry" / "relationships.jsonl"
CHUNKS_DIR = DATA_DIR / "chunks"


class GraphEvidenceNode(BaseModel):
    """Represents an entity or relationship node retrieved from Knowledge Graph traversal."""
    source: str
    relation: str
    target: str
    provenance: str
    evidence_id: Optional[str] = None
    evidentiary_strength: Optional[str] = "EVIDENCE_PARTIAL"
    citation: Optional[str] = None


class HybridRetrievalResult(BaseModel):
    """Combined output of 3-way hybrid retrieval and graph traversal."""
    query: str
    parsed_query: ParsedQuery
    ranked_chunks: List[RetrievedChunk]
    graph_nodes: List[GraphEvidenceNode]
    gate_evaluations: List[EvidenceEvaluationResult]
    primary_decision: GateDecision
    confidence_score: float = 0.95


class UnifiedHybridRetriever:
    """
    Synthesizes dense vector similarity, lexical keyword matching, and knowledge graph
    relational traversal into a grounded, evidence-gated context.
    """
    def __init__(
        self,
        vector_search_engine: Optional[HybridSearchEngine] = None,
        evidence_gate: Optional[EvidenceGate] = None,
        evidence_registry: Optional[EvidenceRegistry] = None
    ):
        self.search_engine = vector_search_engine or HybridSearchEngine()
        self.evidence_gate = evidence_gate or EvidenceGate()
        self.evidence_reg = evidence_registry or EvidenceRegistry()
        
        # Load Knowledge Graph into memory for low-latency traversal
        self.adjacency_list: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_knowledge_graph()

    def _load_knowledge_graph(self) -> None:
        if not RELATIONSHIPS_PATH.exists():
            return
        with open(RELATIONSHIPS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        edge = json.loads(line_str)
                        src = edge.get("source", "").upper().strip()
                        tgt = edge.get("target", "").upper().strip()
                        self.adjacency_list[src].append(edge)
                        self.adjacency_list[tgt].append(edge)
                    except Exception:
                        pass

    def traverse_subgraph(self, entities: List[str], max_hops: int = 2) -> List[GraphEvidenceNode]:
        """Traverses knowledge graph neighborhood starting from resolved entities."""
        visited_edges: Set[str] = set()
        matched_nodes: List[GraphEvidenceNode] = []

        current_frontier = [e.upper().strip() for e in entities if e]
        
        for _ in range(max_hops):
            next_frontier = []
            for node_key in current_frontier:
                # Direct match and prefix match
                for edge in self.adjacency_list.get(node_key, []):
                    edge_id = f"{edge.get('source')}|{edge.get('relation')}|{edge.get('target')}"
                    if edge_id not in visited_edges:
                        visited_edges.add(edge_id)
                        matched_nodes.append(GraphEvidenceNode(
                            source=edge.get("source", ""),
                            relation=edge.get("relation", ""),
                            target=edge.get("target", ""),
                            provenance=edge.get("provenance", ""),
                            evidence_id=edge.get("evidence_id"),
                            evidentiary_strength=edge.get("evidentiary_strength", "EVIDENCE_PARTIAL"),
                            citation=edge.get("citation")
                        ))
                        # Expand frontier to target
                        src_c = edge.get("source", "").upper().strip()
                        tgt_c = edge.get("target", "").upper().strip()
                        if src_c != node_key and src_c not in next_frontier:
                            next_frontier.append(src_c)
                        if tgt_c != node_key and tgt_c not in next_frontier:
                            next_frontier.append(tgt_c)
            current_frontier = next_frontier[:20]

        return matched_nodes

    def retrieve(
        self,
        parsed_query: ParsedQuery,
        top_k: int = 5,
        as_of_date: Optional[str] = None
    ) -> HybridRetrievalResult:
        """
        Executes 3-way hybrid retrieval:
        1. Dense Vector + BM25 chunk retrieval
        2. Knowledge Graph multi-hop traversal
        3. Evidence Gate regulatory safety evaluation
        """
        effective_query = parsed_query.clean_query
        effective_date = as_of_date or parsed_query.as_of_date

        # 1. Text & Vector Stream (via HybridSearchEngine)
        vector_chunks: List[RetrievedChunk] = []
        try:
            raw_results = self.search_engine.search(
                query=effective_query,
                top_k=top_k,
                as_of_date=effective_date
            )
            for r in raw_results:
                if isinstance(r, dict):
                    meta = r.get("metadata", {})
                    vector_chunks.append(RetrievedChunk(
                        chunk_id=r.get("chunk_id", ""),
                        document_id=r.get("document_id") or meta.get("document_id", "DOC-UNKNOWN"),
                        version_id=r.get("version_id") or meta.get("version_id"),
                        source_id=r.get("source_id") or meta.get("source_id", "SRC-001"),
                        standard_number=r.get("standard_number") or meta.get("standard_number", ""),
                        clause_number=r.get("clause_number") or meta.get("clause_number", ""),
                        title=r.get("title") or meta.get("title"),
                        pages=r.get("pages") or meta.get("pages", []),
                        chunk_type=r.get("chunk_type") or meta.get("chunk_type", "requirement"),
                        normative_force=r.get("normative_force") or meta.get("normative_force", "mandatory"),
                        temporal_status=r.get("temporal_status") or meta.get("temporal_status", "current"),
                        valid_from=r.get("valid_from") or meta.get("valid_from"),
                        valid_until=r.get("valid_until") or meta.get("valid_until"),
                        score=float(r.get("score") or r.get("rrf_score", 0.5)),
                        text=r.get("text", ""),
                        content_hash=r.get("content_hash", ""),
                        provenance=r.get("provenance") or meta
                    ))
                elif isinstance(r, RetrievedChunk):
                    vector_chunks.append(r)
        except Exception as e:
            logger.warning(f"Vector search failed, falling back: {e}")

        # 2. Knowledge Graph Stream
        entities_to_expand = []
        if parsed_query.canonical_product:
            entities_to_expand.append(parsed_query.canonical_product)
        if parsed_query.standard_code:
            entities_to_expand.append(parsed_query.standard_code)
        for k, v in parsed_query.extracted_entities.items():
            if isinstance(v, str) and len(v) > 2:
                entities_to_expand.append(v)

        graph_nodes = self.traverse_subgraph(entities_to_expand, max_hops=2)

        # 3. Evidence Gate Evaluation
        gate_evaluations: List[EvidenceEvaluationResult] = []
        
        # Evaluate standard code if present
        if parsed_query.standard_code:
            ev_results = self.evidence_gate.evaluate_entity(parsed_query.standard_code)
            gate_evaluations.extend(ev_results)

        # Evaluate graph edges evidence
        for g_node in graph_nodes[:10]:
            if g_node.evidence_id:
                rec = self.evidence_reg.get_by_id(g_node.evidence_id)
                if rec:
                    gate_evaluations.append(self.evidence_gate.evaluate_evidence(rec))

        # Determine primary gate decision
        primary_decision = GateDecision.ALLOW_LIMITED_CLAIM
        if any(g.decision == GateDecision.ALLOW_NORMATIVE_CLAIM for g in gate_evaluations):
            primary_decision = GateDecision.ALLOW_NORMATIVE_CLAIM
        elif any(g.decision == GateDecision.SURFACE_CONFLICT for g in gate_evaluations):
            primary_decision = GateDecision.SURFACE_CONFLICT
        elif any(g.decision == GateDecision.HISTORICAL_CONTEXT_ONLY for g in gate_evaluations):
            primary_decision = GateDecision.HISTORICAL_CONTEXT_ONLY
        elif any(g.decision == GateDecision.REFUSE_UNVERIFIED_CLAIM for g in gate_evaluations):
            primary_decision = GateDecision.REFUSE_UNVERIFIED_CLAIM

        # Calculate confidence
        confidence = 0.95 if (vector_chunks and graph_nodes) else (0.85 if vector_chunks or graph_nodes else 0.5)

        return HybridRetrievalResult(
            query=parsed_query.raw_query,
            parsed_query=parsed_query,
            ranked_chunks=vector_chunks,
            graph_nodes=graph_nodes,
            gate_evaluations=gate_evaluations,
            primary_decision=primary_decision,
            confidence_score=confidence
        )
