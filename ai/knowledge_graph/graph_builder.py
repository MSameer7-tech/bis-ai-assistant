"""
Knowledge Graph Construction Engine (Phase 5B).
Assembles heterogeneous nodes and validated edges from manifests, product catalogs, and evidence units.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ACQUISITION_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
EXTRACTION_MANIFEST_PATH = ROOT_DIR / "data" / "processed" / "extraction_manifest.json"
EVIDENCE_UNITS_ROOT = ROOT_DIR / "data" / "processed" / "evidence_units"
PRODUCT_CATALOG_PATH = ROOT_DIR / "data" / "product_catalog.json"

from ai.knowledge_graph.schema import NodeType, EdgeType, GraphNode, GraphEdge

logger = logging.getLogger(__name__)


def generate_edge_id(source_id: str, target_id: str, edge_type: str) -> str:
    """Generates a deterministic unique ID for a graph edge."""
    key = f"{source_id}|{target_id}|{edge_type}".encode("utf-8")
    return f"EDGE-{hashlib.sha256(key).hexdigest()[:16]}"


class KnowledgeGraphBuilder:
    """Constructs the unified BIS Knowledge Graph from all processed data layers."""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adj_out: Dict[str, List[str]] = {}  # node_id -> [edge_id]
        self.adj_in: Dict[str, List[str]] = {}   # node_id -> [edge_id]

    def add_node(self, node: GraphNode):
        """Adds a node to the graph."""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adj_out:
            self.adj_out[node.node_id] = []
        if node.node_id not in self.adj_in:
            self.adj_in[node.node_id] = []

    def add_edge(self, edge: GraphEdge):
        """Adds a validated edge between two existing nodes."""
        if edge.source_id not in self.nodes:
            logger.debug("Skipping edge: source node %s not in graph", edge.source_id)
            return
        if edge.target_id not in self.nodes:
            logger.debug("Skipping edge: target node %s not in graph", edge.target_id)
            return

        self.edges[edge.edge_id] = edge
        self.adj_out[edge.source_id].append(edge.edge_id)
        self.adj_in[edge.target_id].append(edge.edge_id)

    def build_graph(self) -> Tuple[Dict[str, GraphNode], Dict[str, GraphEdge]]:
        """Builds the complete knowledge graph."""
        logger.info("🏗️ Assembling BIS Knowledge Graph...")

        # 1. Ingest Product Catalog Nodes
        self._ingest_products()

        # 2. Ingest Schemes Nodes
        self._ingest_schemes()

        # 3. Ingest Documents from Acquisition Manifest
        self._ingest_acquisition_manifest()

        # 4. Ingest Evidence Units
        self._ingest_evidence_units()

        # 5. Build Inter-Entity Relationships
        self._build_domain_relationships()

        logger.info("✅ Knowledge Graph Built: %d nodes, %d edges", len(self.nodes), len(self.edges))
        return self.nodes, self.edges

    def _ingest_products(self):
        """Populates product nodes from catalog and keywords."""
        if not PRODUCT_CATALOG_PATH.exists():
            return
        with open(PRODUCT_CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        for prod in catalog.get("products", []):
            p_id = prod.get("product_id") or f"PROD-{prod.get('name', 'GENERIC').upper().replace(' ', '-')}"
            p_name = prod.get("name")
            p_std = prod.get("standard_number") or prod.get("primary_standard")
            p_node = GraphNode(
                node_id=p_id,
                node_type=NodeType.PRODUCT,
                label=p_name,
                properties={
                    "category": prod.get("category"),
                    "domain": prod.get("domain"),
                    "aliases": prod.get("aliases", []),
                    "primary_standard": p_std,
                    "mandatory": prod.get("mandatory_certification", prod.get("mandatory", False)),
                    "qco_order": prod.get("qco_order"),
                    "scheme": prod.get("scheme", "Scheme-I")
                }
            )
            self.add_node(p_node)

    def _ingest_schemes(self):
        """Populates conformity assessment scheme nodes."""
        schemes = [
            ("SCHEME-I", "Scheme-I: Standard Mark (ISI Mark) Product Certification"),
            ("SCHEME-II", "Scheme-II: Compulsory Registration Scheme (CRS)"),
            ("SCHEME-IV", "Scheme-IV: Hallmarking of Gold and Silver"),
            ("SCHEME-X", "Scheme-X: Simplified Conformity Assessment for MSMEs")
        ]
        for s_id, s_label in schemes:
            self.add_node(
                GraphNode(
                    node_id=s_id,
                    node_type=NodeType.CONFORMITY_SCHEME,
                    label=s_label,
                    properties={"scheme_id": s_id}
                )
            )

    def _ingest_acquisition_manifest(self):
        """Populates document nodes from acquisition manifest."""
        if not ACQUISITION_MANIFEST_PATH.exists():
            return
        with open(ACQUISITION_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for item in manifest.get("documents", []):
            doc = item.get("document", {})
            doc_id = doc.get("document_id")
            dtype = doc.get("document_type")
            title = doc.get("title", doc_id)

            # Map document_type to NodeType
            ntype = NodeType.INDIAN_STANDARD
            if dtype == "AMENDMENT":
                ntype = NodeType.AMENDMENT
            elif dtype in {"QCO_NOTIFICATION", "QCO"}:
                ntype = NodeType.QCO
            elif dtype in {"SCHEME_REGULATION", "SCHEME"}:
                ntype = NodeType.CONFORMITY_SCHEME
            elif dtype == "PRODUCT_MANUAL":
                ntype = NodeType.PRODUCT_MANUAL
            elif dtype == "SIT_SCHEDULE":
                ntype = NodeType.SIT_SCHEDULE
            elif dtype == "LAB_DIRECTORY":
                ntype = NodeType.TESTING_LABORATORY
            elif dtype == "LICENCE_RECORD":
                ntype = NodeType.LICENCE_RECORD
            elif dtype == "CRS_REGISTRATION":
                ntype = NodeType.CRS_REGISTRATION
            elif dtype in {"HALLMARKING_ORDER", "AHC_RECORD"}:
                ntype = NodeType.HALLMARKING_CENTRE

            node = GraphNode(
                node_id=doc_id,
                node_type=ntype,
                label=title,
                properties={
                    "document_family_id": doc.get("document_family_id"),
                    "document_type": dtype,
                    "authority": doc.get("authority"),
                    "authority_class": doc.get("authority_class"),
                    "edition_year": doc.get("edition_year"),
                    "parent_document_id": doc.get("parent_document_id")
                }
            )
            self.add_node(node)

    def _ingest_evidence_units(self):
        """Populates evidence unit nodes and links them to parent documents."""
        if not EVIDENCE_UNITS_ROOT.exists():
            return

        for doc_dir in EVIDENCE_UNITS_ROOT.glob("*"):
            unit_file = doc_dir / "evidence_units.json"
            if not unit_file.exists():
                continue

            with open(unit_file, "r", encoding="utf-8") as f:
                units = json.load(f)

            doc_id = doc_dir.name
            for u in units:
                u_id = u.get("evidence_unit_id")
                u_node = GraphNode(
                    node_id=u_id,
                    node_type=NodeType.EVIDENCE_UNIT,
                    label=u.get("heading", u_id),
                    properties={
                        "document_id": doc_id,
                        "section_or_clause": u.get("section_or_clause"),
                        "content_type": u.get("content_type"),
                        "content_text": u.get("content_text")[:300],  # preview
                        "citation_anchor": u.get("citation_anchor")
                    }
                )
                self.add_node(u_node)

                # Edge: Document -> Contains Evidence Unit
                edge_id = generate_edge_id(doc_id, u_id, EdgeType.CONTAINS_EVIDENCE_UNIT.value)
                self.add_edge(
                    GraphEdge(
                        edge_id=edge_id,
                        source_id=doc_id,
                        target_id=u_id,
                        edge_type=EdgeType.CONTAINS_EVIDENCE_UNIT,
                        confidence=1.0
                    )
                )

    def _build_domain_relationships(self):
        """Builds domain edges between products, standards, QCOs, schemes, manuals, and labs."""
        std_nodes = {nid: n for nid, n in self.nodes.items() if n.node_type == NodeType.INDIAN_STANDARD}
        lab_nodes = {nid: n for nid, n in self.nodes.items() if n.node_type == NodeType.TESTING_LABORATORY}

        # 1. Product -> Standard Links
        for prod_id, prod_node in list(self.nodes.items()):
            if prod_node.node_type != NodeType.PRODUCT:
                continue

            pri_std = str(prod_node.properties.get("primary_standard", "")).strip().lower().replace(" ", "").replace("-", "")
            for std_id in std_nodes:
                clean_std_id = std_id.lower().replace("-", "").replace(" ", "")
                if pri_std and (pri_std in clean_std_id or clean_std_id in pri_std):
                    # Edge: Product -> Covered By Standard
                    edge_id = generate_edge_id(prod_id, std_id, EdgeType.COVERED_BY_STANDARD.value)
                    self.add_edge(
                        GraphEdge(
                            edge_id=edge_id,
                            source_id=prod_id,
                            target_id=std_id,
                            edge_type=EdgeType.COVERED_BY_STANDARD,
                            confidence=1.0
                        )
                    )

                    # Edge: Standard -> Scheme
                    scheme_id = prod_node.properties.get("scheme", "Scheme-I")
                    scheme_node_id = "SCHEME-I" if "Scheme-I" in scheme_id or "Scheme-1" in scheme_id else ("SCHEME-II" if "Scheme-II" in scheme_id else "SCHEME-IV")
                    if scheme_node_id in self.nodes:
                        edge_s = generate_edge_id(std_id, scheme_node_id, EdgeType.CERTIFIED_UNDER_SCHEME.value)
                        self.add_edge(
                            GraphEdge(
                                edge_id=edge_s,
                                source_id=std_id,
                                target_id=scheme_node_id,
                                edge_type=EdgeType.CERTIFIED_UNDER_SCHEME,
                                confidence=1.0
                            )
                        )

        # 2. Amendment -> Standard (AMENDED_BY)
        for amd_id, amd_node in list(self.nodes.items()):
            if amd_node.node_type == NodeType.AMENDMENT:
                parent_id = amd_node.properties.get("parent_document_id")
                if parent_id and parent_id in self.nodes:
                    edge_id = generate_edge_id(parent_id, amd_id, EdgeType.AMENDED_BY.value)
                    self.add_edge(
                        GraphEdge(
                            edge_id=edge_id,
                            source_id=parent_id,
                            target_id=amd_id,
                            edge_type=EdgeType.AMENDED_BY,
                            confidence=1.0
                        )
                    )

        # 3. Product Manual -> Standard (HAS_PRODUCT_MANUAL)
        for pm_id, pm_node in list(self.nodes.items()):
            if pm_node.node_type == NodeType.PRODUCT_MANUAL:
                fam_id = pm_node.properties.get("document_family_id") or ""
                if fam_id.startswith("PM-IS-"):
                    target_std_fam = fam_id.replace("PM-", "")
                    for std_id, std_node in std_nodes.items():
                        if std_node.properties.get("document_family_id") == target_std_fam:
                            edge_id = generate_edge_id(std_id, pm_id, EdgeType.HAS_PRODUCT_MANUAL.value)
                            self.add_edge(
                                GraphEdge(
                                    edge_id=edge_id,
                                    source_id=std_id,
                                    target_id=pm_id,
                                    edge_type=EdgeType.HAS_PRODUCT_MANUAL,
                                    confidence=0.95
                                )
                            )

        # 4. SIT Schedule -> Standard (HAS_SIT_SCHEDULE)
        for sit_id, sit_node in list(self.nodes.items()):
            if sit_node.node_type == NodeType.SIT_SCHEDULE:
                fam_id = sit_node.properties.get("document_family_id") or ""
                if fam_id.startswith("SIT-IS-"):
                    target_std_fam = fam_id.replace("SIT-", "")
                    for std_id, std_node in std_nodes.items():
                        if std_node.properties.get("document_family_id") == target_std_fam:
                            edge_id = generate_edge_id(std_id, sit_id, EdgeType.HAS_SIT_SCHEDULE.value)
                            self.add_edge(
                                GraphEdge(
                                    edge_id=edge_id,
                                    source_id=std_id,
                                    target_id=sit_id,
                                    edge_type=EdgeType.HAS_SIT_SCHEDULE,
                                    confidence=0.95
                                )
                            )

        # 5. QCO -> Standard / Product (MANDATES_CERTIFICATION_FOR)
        for qco_id, qco_node in list(self.nodes.items()):
            if qco_node.node_type == NodeType.QCO:
                # Link QCO to matching standards based on commodities
                qco_label = qco_node.label.lower()
                for std_id, std_node in std_nodes.items():
                    std_title = std_node.label.lower()
                    if ("steel" in qco_label and "steel" in std_title) or \
                       ("fan" in qco_label and "fan" in std_title) or \
                       ("cement" in qco_label and "cement" in std_title) or \
                       ("helmet" in qco_label and "helmet" in std_title) or \
                       ("water" in qco_label and "water" in std_title) or \
                       ("electronics" in qco_label and ("battery" in std_title or "safety" in std_title or "lamp" in std_title)):
                        edge_id = generate_edge_id(qco_id, std_id, EdgeType.MANDATES_CERTIFICATION_FOR.value)
                        self.add_edge(
                            GraphEdge(
                                edge_id=edge_id,
                                source_id=qco_id,
                                target_id=std_id,
                                edge_type=EdgeType.MANDATES_CERTIFICATION_FOR,
                                confidence=0.95
                            )
                        )

        # 6. Standard -> Testing Laboratories (TESTED_BY_LABORATORY)
        for std_id in std_nodes:
            for lab_id in lab_nodes:
                edge_id = generate_edge_id(std_id, lab_id, EdgeType.TESTED_BY_LABORATORY.value)
                self.add_edge(
                    GraphEdge(
                        edge_id=edge_id,
                        source_id=std_id,
                        target_id=lab_id,
                        edge_type=EdgeType.TESTED_BY_LABORATORY,
                        confidence=0.90
                    )
                )

        # 7. Licences -> Standard (LICENSED_UNDER_STANDARD)
        for lic_id, lic_node in list(self.nodes.items()):
            if lic_node.node_type == NodeType.LICENCE_RECORD:
                title = lic_node.label
                for std_id, std_node in std_nodes.items():
                    std_fam = std_node.properties.get("document_family_id", "")
                    raw_num = std_fam.replace("IS-", "")
                    if f"IS {raw_num}" in title:
                        edge_id = generate_edge_id(lic_id, std_id, EdgeType.LICENSED_UNDER_STANDARD.value)
                        self.add_edge(
                            GraphEdge(
                                edge_id=edge_id,
                                source_id=lic_id,
                                target_id=std_id,
                                edge_type=EdgeType.LICENSED_UNDER_STANDARD,
                                confidence=0.95
                            )
                        )

        # 8. CRS Registrations -> Standard (REGISTERED_UNDER_STANDARD)
        for crs_id, crs_node in list(self.nodes.items()):
            if crs_node.node_type == NodeType.CRS_REGISTRATION:
                title = crs_node.label
                for std_id, std_node in std_nodes.items():
                    std_fam = std_node.properties.get("document_family_id", "")
                    raw_num = std_fam.replace("IS-", "")
                    if f"IS {raw_num}" in title:
                        edge_id = generate_edge_id(crs_id, std_id, EdgeType.REGISTERED_UNDER_STANDARD.value)
                        self.add_edge(
                            GraphEdge(
                                edge_id=edge_id,
                                source_id=crs_id,
                                target_id=std_id,
                                edge_type=EdgeType.REGISTERED_UNDER_STANDARD,
                                confidence=0.95
                            )
                        )
