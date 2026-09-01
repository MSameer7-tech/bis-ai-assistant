"""
Phase 5E: Dynamic Knowledge Graph Reconciler with Formalized Evidence.
Formalizes every knowledge graph edge with:
- relationship_id
- source
- relation
- target
- confidence
- evidence: {source_type, source_document, clause_or_table, retrieved_at}
- document_available
- verification_status: 'verified' | 'unverified'
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
RELATIONSHIPS_FILE = REGISTRY_DIR / "relationships.jsonl"


class GraphReconciler:
    """
    Maintains and reconciles knowledge graph edges with verified evidence blocks.
    """

    def __init__(self, relationships_path: Optional[Path] = None):
        self.relationships_path = relationships_path or RELATIONSHIPS_FILE
        self.edges: List[Dict[str, Any]] = []
        self._load_edges()

    def _load_edges(self):
        if not self.relationships_path.exists():
            return
        with open(self.relationships_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.edges.append(json.loads(line))

    def add_or_update_edge(
        self,
        source: str,
        relation: str,
        target: str,
        evidence_source_type: str,
        evidence_doc: str,
        clause_or_table: Optional[str] = None,
        confidence: float = 1.0,
        doc_available: bool = True,
        verification_status: str = "verified"
    ) -> Dict[str, Any]:
        """
        Adds or updates a verified knowledge graph edge.
        """
        # Check if edge already exists
        for edge in self.edges:
            if edge.get("source") == source and edge.get("relation") == relation and edge.get("target") == target:
                edge["confidence"] = confidence
                edge["document_available"] = doc_available
                edge["verification_status"] = verification_status
                edge["evidence"] = {
                    "source_type": evidence_source_type,
                    "source_document": evidence_doc,
                    "clause_or_table": clause_or_table,
                    "retrieved_at": datetime.now().isoformat()
                }
                return edge

        # Create new edge
        new_edge_id = f"REL-{len(self.edges) + 1:06d}"
        new_edge = {
            "relationship_id": new_edge_id,
            "source": source,
            "relation": relation,
            "target": target,
            "confidence": confidence,
            "evidence": {
                "source_type": evidence_source_type,
                "source_document": evidence_doc,
                "clause_or_table": clause_or_table,
                "retrieved_at": datetime.now().isoformat()
            },
            "document_available": doc_available,
            "verification_status": verification_status
        }
        self.edges.append(new_edge)
        return new_edge

    def save_edges(self, output_path: Optional[Path] = None):
        out_p = output_path or self.relationships_path
        with open(out_p, "w", encoding="utf-8") as f:
            for edge in self.edges:
                f.write(json.dumps(edge, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(self.edges)} reconciled graph edges to: {out_p}")
