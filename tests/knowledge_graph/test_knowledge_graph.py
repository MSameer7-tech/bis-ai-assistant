"""
Automated Verification Suite for Phase 5: Knowledge Graph Construction & Structured BIS Relationships.
Validates heterogeneous node schemas, edge referential integrity (zero dangling edges),
multi-hop compliance chain traversal, and graph export artifacts.
"""
import json
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GRAPH_ROOT = ROOT_DIR / "data" / "processed" / "knowledge_graph"
DOCS_PHASE5_DIR = ROOT_DIR / "docs" / "phase5"

from ai.knowledge_graph.schema import NodeType, EdgeType, GraphNode, GraphEdge, ComplianceChain
from ai.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from ai.knowledge_graph.graph_traversal import KnowledgeGraphTraversal
from ai.knowledge_graph.graph_orchestrator import KnowledgeGraphOrchestrator


@pytest.fixture(scope="module")
def graph_traversal():
    builder = KnowledgeGraphBuilder()
    builder.build_graph()
    return KnowledgeGraphTraversal(builder)


def test_knowledge_graph_node_and_edge_types(graph_traversal):
    """Verifies that the knowledge graph contains diverse heterogeneous node types and edge types."""
    nodes = graph_traversal.nodes
    edges = graph_traversal.edges

    assert len(nodes) >= 100, f"Expected >= 100 nodes, got {len(nodes)}"
    assert len(edges) >= 100, f"Expected >= 100 edges, got {len(edges)}"

    node_types = {n.node_type for n in nodes.values()}
    assert NodeType.PRODUCT in node_types
    assert NodeType.INDIAN_STANDARD in node_types
    assert NodeType.QCO in node_types
    assert NodeType.CONFORMITY_SCHEME in node_types
    assert NodeType.PRODUCT_MANUAL in node_types
    assert NodeType.TESTING_LABORATORY in node_types
    assert NodeType.EVIDENCE_UNIT in node_types

    edge_types = {e.edge_type for e in edges.values()}
    assert EdgeType.COVERED_BY_STANDARD in edge_types
    assert EdgeType.CERTIFIED_UNDER_SCHEME in edge_types
    assert EdgeType.TESTED_BY_LABORATORY in edge_types
    assert EdgeType.CONTAINS_EVIDENCE_UNIT in edge_types


def test_knowledge_graph_zero_dangling_edges(graph_traversal):
    """Verifies 100% referential integrity with zero dangling edges."""
    nodes = graph_traversal.nodes
    edges = graph_traversal.edges

    for edge_id, edge in edges.items():
        assert edge.source_id in nodes, f"Dangling edge {edge_id}: source {edge.source_id} not found in nodes"
        assert edge.target_id in nodes, f"Dangling edge {edge_id}: target {edge.target_id} not found in nodes"


def test_compliance_chain_traversal_ceiling_fans(graph_traversal):
    """Verifies end-to-end multi-hop compliance chain traversal for Electric Ceiling Fans."""
    chain: ComplianceChain = graph_traversal.get_compliance_chain("Electric Ceiling Fans")
    assert chain.product_node is not None
    assert chain.standard_node is not None
    assert "374" in chain.standard_node.node_id

    # Must be mandatory under Electrical Appliances QCO
    assert chain.is_mandatory is True
    assert chain.qco_node is not None
    assert chain.scheme_node is not None
    assert "SCHEME-I" in chain.scheme_node.node_id

    # Product Manual and SIT Schedule must be resolved
    assert chain.product_manual_node is not None
    assert "PM-IS-374" in chain.product_manual_node.node_id
    assert chain.sit_schedule_node is not None

    # Testing laboratories and evidence units must be linked
    assert len(chain.testing_laboratories) >= 5
    assert len(chain.evidence_units) >= 3


def test_compliance_chain_traversal_tmt_steel(graph_traversal):
    """Verifies end-to-end multi-hop compliance chain traversal for TMT Steel Bars."""
    chain: ComplianceChain = graph_traversal.get_compliance_chain("TMT")
    assert chain.standard_node is not None
    assert "1786" in chain.standard_node.node_id
    assert chain.is_mandatory is True
    assert chain.qco_node is not None

    # Check Amendments and Evidence Units
    assert len(chain.amendments) >= 2
    assert len(chain.evidence_units) >= 5


def test_testing_laboratories_lookup(graph_traversal):
    """Verifies that standards can lookup recognized laboratories via outgoing graph edges."""
    labs = graph_traversal.get_neighbors_out("IS-1786-2008", EdgeType.TESTED_BY_LABORATORY)
    assert len(labs) >= 5
    lab_names = [l.label for l in labs]
    assert any("Central Laboratory" in name or "Sahibabad" in name for name in lab_names)


def test_graph_persistence_artifacts_exist():
    """Verifies that all required graph export artifacts exist in data/processed/knowledge_graph/."""
    orchestrator = KnowledgeGraphOrchestrator()
    orchestrator.run_build_and_export()

    expected_files = [
        GRAPH_ROOT / "nodes.json",
        GRAPH_ROOT / "edges.json",
        GRAPH_ROOT / "knowledge_graph.json",
        GRAPH_ROOT / "graph_statistics.json"
    ]
    for ef in expected_files:
        assert ef.exists(), f"Missing graph persistence file: {ef}"
        assert ef.stat().st_size > 100

    with open(GRAPH_ROOT / "graph_statistics.json", "r", encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["total_nodes"] >= 100
    assert stats["total_edges"] >= 100
    assert stats["dangling_edges_count"] == 0


def test_phase5_documentation_artifacts_exist():
    """Verifies that all 5 required Phase 5 documentation artifacts exist in docs/phase5/."""
    expected_docs = [
        "KNOWLEDGE_GRAPH_ARCHITECTURE.md",
        "GRAPH_ONTOLOGY_SPEC.md",
        "COMPLIANCE_TRAVERSAL_SPEC.md",
        "PHASE_5_ACCEPTANCE_CRITERIA.md",
        "PHASE_5_COMPLETION_REPORT.md"
    ]
    for doc in expected_docs:
        doc_path = DOCS_PHASE5_DIR / doc
        assert doc_path.exists(), f"Missing documentation artifact: {doc}"
        assert doc_path.stat().st_size > 150, f"Document {doc} is too short / empty"
