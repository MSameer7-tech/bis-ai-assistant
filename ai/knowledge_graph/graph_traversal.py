"""
Multi-Hop Graph Traversal Engine (Phase 5C).
Executes high-performance multi-hop graph queries for end-to-end compliance chains, laboratory lookups, and clause citations.
"""
import logging
from typing import Any, Dict, List, Optional, Set

from ai.knowledge_graph.schema import NodeType, EdgeType, GraphNode, GraphEdge, ComplianceChain
from ai.knowledge_graph.graph_builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)


class KnowledgeGraphTraversal:
    """Provides querying and multi-hop traversal interfaces over the BIS Knowledge Graph."""

    def __init__(self, builder: Optional[KnowledgeGraphBuilder] = None):
        if builder is None:
            self.builder = KnowledgeGraphBuilder()
            self.builder.build_graph()
        else:
            self.builder = builder

        self.nodes = self.builder.nodes
        self.edges = self.builder.edges
        self.adj_out = self.builder.adj_out
        self.adj_in = self.builder.adj_in

    def find_product_node(self, query: str) -> Optional[GraphNode]:
        """Finds a product node by exact ID, exact label, or keyword match."""
        q_clean = query.strip().lower()

        # 1. Exact ID match
        for nid, node in self.nodes.items():
            if node.node_type == NodeType.PRODUCT:
                if nid.lower() == q_clean:
                    return node

        # 2. Exact label match
        for nid, node in self.nodes.items():
            if node.node_type == NodeType.PRODUCT:
                if node.label.lower() == q_clean:
                    return node

        # 3. Alias list match
        for nid, node in self.nodes.items():
            if node.node_type == NodeType.PRODUCT:
                for alias in node.properties.get("aliases", []):
                    if alias.lower() == q_clean or q_clean in alias.lower():
                        return node

        # 4. Substring / keyword match
        for nid, node in self.nodes.items():
            if node.node_type == NodeType.PRODUCT:
                if q_clean in node.label.lower() or q_clean in nid.lower():
                    return node

        return None

    def find_standard_node(self, query: str) -> Optional[GraphNode]:
        """Finds an Indian Standard node by standard number, ID, or title."""
        q_clean = query.strip().lower().replace(" ", "").replace(":", "")

        for nid, node in self.nodes.items():
            if node.node_type == NodeType.INDIAN_STANDARD:
                clean_nid = nid.lower().replace("-", "").replace("is", "")
                if q_clean in clean_nid or q_clean in node.label.lower().replace(" ", ""):
                    return node
        return None

    def get_neighbors_out(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphNode]:
        """Gets target nodes for outgoing edges from node_id."""
        out_nodes = []
        for edge_id in self.adj_out.get(node_id, []):
            edge = self.edges.get(edge_id)
            if edge and (edge_type is None or edge.edge_type == edge_type):
                target = self.nodes.get(edge.target_id)
                if target:
                    out_nodes.append(target)
        return out_nodes

    def get_neighbors_in(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphNode]:
        """Gets source nodes for incoming edges to node_id."""
        in_nodes = []
        for edge_id in self.adj_in.get(node_id, []):
            edge = self.edges.get(edge_id)
            if edge and (edge_type is None or edge.edge_type == edge_type):
                src = self.nodes.get(edge.source_id)
                if src:
                    in_nodes.append(src)
        return in_nodes

    def get_compliance_chain(self, query: str) -> ComplianceChain:
        """
        Executes multi-hop traversal to construct the complete end-to-end regulatory compliance chain.
        Traverses: Product -> Standard -> QCO -> Scheme -> Product Manual -> SIT -> Labs -> Licences -> Evidence Units.
        """
        chain = ComplianceChain(product_name=query)

        # 1. Resolve Product Node
        prod_node = self.find_product_node(query)
        if prod_node:
            chain.product_node = prod_node
            chain.is_mandatory = prod_node.properties.get("mandatory", False)

        # 2. Resolve Standard Node (either via edge or direct lookup)
        std_node = None
        if prod_node:
            stds = self.get_neighbors_out(prod_node.node_id, EdgeType.COVERED_BY_STANDARD)
            if stds:
                std_node = stds[0]

        if not std_node:
            std_node = self.find_standard_node(query)

        if std_node:
            chain.standard_node = std_node
            std_id = std_node.node_id

            # 3. Find QCO Mandate Node (incoming MANDATES_CERTIFICATION_FOR edge)
            qcos = self.get_neighbors_in(std_id, EdgeType.MANDATES_CERTIFICATION_FOR)
            if qcos:
                chain.qco_node = qcos[0]
                chain.is_mandatory = True

            # 4. Find Scheme Node
            schemes = self.get_neighbors_out(std_id, EdgeType.CERTIFIED_UNDER_SCHEME)
            if schemes:
                chain.scheme_node = schemes[0]

            # 5. Find Product Manual
            manuals = self.get_neighbors_out(std_id, EdgeType.HAS_PRODUCT_MANUAL)
            if manuals:
                chain.product_manual_node = manuals[0]

            # 6. Find SIT Schedule
            sits = self.get_neighbors_out(std_id, EdgeType.HAS_SIT_SCHEDULE)
            if sits:
                chain.sit_schedule_node = sits[0]

            # 7. Find Amendments
            chain.amendments = self.get_neighbors_out(std_id, EdgeType.AMENDED_BY)

            # 8. Find Testing Laboratories
            chain.testing_laboratories = self.get_neighbors_out(std_id, EdgeType.TESTED_BY_LABORATORY)

            # 9. Find Licences / Registrations
            lics = self.get_neighbors_in(std_id, EdgeType.LICENSED_UNDER_STANDARD)
            crs = self.get_neighbors_in(std_id, EdgeType.REGISTERED_UNDER_STANDARD)
            chain.licences_or_registrations = lics + crs

            # 10. Find Evidence Units
            chain.evidence_units = self.get_neighbors_out(std_id, EdgeType.CONTAINS_EVIDENCE_UNIT)

        return chain
