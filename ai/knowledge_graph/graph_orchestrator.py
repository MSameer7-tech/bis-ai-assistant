#!/usr/bin/env python3
"""
Knowledge Graph Construction & Export Orchestrator (Phase 5).
Builds, validates, serializes, and verifies the unified BIS Knowledge Graph.
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from ai.knowledge_graph.graph_traversal import KnowledgeGraphTraversal
from ai.knowledge_graph.schema import NodeType, EdgeType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KnowledgeGraphOrchestrator")

GRAPH_EXPORT_ROOT = ROOT_DIR / "data" / "processed" / "knowledge_graph"


class KnowledgeGraphOrchestrator:
    """Builds and serializes the complete BIS Knowledge Graph."""

    def __init__(self):
        self.builder = KnowledgeGraphBuilder()

    def run_build_and_export(self) -> Dict[str, Any]:
        """Executes graph assembly and exports artifacts."""
        logger.info("🚀 Starting Phase 5 Knowledge Graph Construction...")

        nodes, edges = self.builder.build_graph()

        # Quality Gate: Validate Zero Dangling Edges
        dangling_edges = []
        for edge_id, edge in edges.items():
            if edge.source_id not in nodes or edge.target_id not in nodes:
                dangling_edges.append(edge_id)

        if dangling_edges:
            logger.error("🚨 Detected %d dangling edges in graph!", len(dangling_edges))
            sys.exit(1)

        GRAPH_EXPORT_ROOT.mkdir(parents=True, exist_ok=True)

        # 1. Export nodes.json
        nodes_payload = [n.model_dump() for n in nodes.values()]
        with open(GRAPH_EXPORT_ROOT / "nodes.json", "w", encoding="utf-8") as f:
            json.dump(nodes_payload, f, indent=2)

        # 2. Export edges.json
        edges_payload = [e.model_dump() for e in edges.values()]
        with open(GRAPH_EXPORT_ROOT / "edges.json", "w", encoding="utf-8") as f:
            json.dump(edges_payload, f, indent=2)

        # 3. Export complete graph snapshot
        graph_snapshot = {
            "version": "1.0",
            "phase": "Phase 5: Knowledge Graph Construction & Structured BIS Relationships",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": nodes_payload,
            "edges": edges_payload
        }
        with open(GRAPH_EXPORT_ROOT / "knowledge_graph.json", "w", encoding="utf-8") as f:
            json.dump(graph_snapshot, f, indent=2)

        # 4. Export graph statistics
        node_counts_by_type = {}
        for n in nodes.values():
            node_counts_by_type[n.node_type.value] = node_counts_by_type.get(n.node_type.value, 0) + 1

        edge_counts_by_type = {}
        for e in edges.values():
            edge_counts_by_type[e.edge_type.value] = edge_counts_by_type.get(e.edge_type.value, 0) + 1

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_distribution": node_counts_by_type,
            "edge_distribution": edge_counts_by_type,
            "dangling_edges_count": len(dangling_edges),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(GRAPH_EXPORT_ROOT / "graph_statistics.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        logger.info(
            "💾 Saved Knowledge Graph: %d nodes, %d edges to %s",
            len(nodes),
            len(edges),
            GRAPH_EXPORT_ROOT
        )
        return stats


def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph Construction Orchestrator")
    parser.add_argument("--query", type=str, help="Test compliance chain traversal for a product")
    args = parser.parse_args()

    orchestrator = KnowledgeGraphOrchestrator()
    stats = orchestrator.run_build_and_export()

    if args.query:
        traversal = KnowledgeGraphTraversal(orchestrator.builder)
        chain = traversal.get_compliance_chain(args.query)
        print(f"\n🔍 Compliance Chain Traversal for '{args.query}':")
        print(f"  Product: {chain.product_node.label if chain.product_node else 'N/A'}")
        print(f"  Standard: {chain.standard_node.label if chain.standard_node else 'N/A'}")
        print(f"  Mandatory Status: {'MANDATORY (QCO Enforced)' if chain.is_mandatory else 'Voluntary'}")
        print(f"  QCO Order: {chain.qco_node.label if chain.qco_node else 'N/A'}")
        print(f"  Scheme: {chain.scheme_node.label if chain.scheme_node else 'N/A'}")
        print(f"  Product Manual: {chain.product_manual_node.label if chain.product_manual_node else 'N/A'}")
        print(f"  SIT Schedule: {chain.sit_schedule_node.label if chain.sit_schedule_node else 'N/A'}")
        print(f"  Amendments Found: {len(chain.amendments)}")
        print(f"  Testing Labs Linked: {len(chain.testing_laboratories)}")
        print(f"  Evidence Units Linked: {len(chain.evidence_units)}")


if __name__ == "__main__":
    main()
