"""
Formal Relationship Graph Mapper (Phase 3F).
Discovers and validates explicit, typed, evidence-backed cross-document relationships across the BIS regulatory ecosystem.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SUPPORTED_RELATIONSHIP_TYPES = {
    "AMENDS",
    "SUPERSEDES",
    "WITHDRAWS",
    "CORRIGES",
    "CERTIFICATION_GUIDELINE_FOR",
    "TESTING_SCHEDULE_FOR",
    "MANDATES_CERTIFICATION_FOR",
    "TESTED_BY_LAB",
    "LAB_SCOPE_FOR",
    "LICENCE_FOR_STANDARD",
    "REGISTRATION_FOR_PRODUCT",
    "RELATED_STANDARD",
    "REFERENCES_STANDARD"
}


class RelationshipEdge(BaseModel):
    """Formal data contract for a directed, typed, evidence-backed knowledge graph edge."""
    relationship_id: str = Field(..., description="Deterministic hash ID (source + target + type)")
    source_document_id: str
    target_document_id: str
    relationship_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_type: str = Field(..., description="EXPLICIT_FIELD, DOCUMENT_TEXT, REGULATORY_SCHEDULE, CATALOG_CROSS_REFERENCE")
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)
    discovered_via: str = Field(..., description="Source endpoint ID or extraction method")
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_status: str = Field(default="VALIDATED")


def generate_edge_id(source_id: str, target_id: str, rel_type: str) -> str:
    """Generates a deterministic unique hash for an edge."""
    key = f"{source_id}|{target_id}|{rel_type}".encode("utf-8")
    return f"REL-{hashlib.sha256(key).hexdigest()[:16]}"


class RelationshipDiscoverer:
    """Discovers, validates, and formalizes graph edges between regulatory documents."""

    def discover_relationships(self, documents_manifest: List[Dict[str, Any]]) -> List[RelationshipEdge]:
        """
        Discovers verified cross-document relationships using exact structured identity matching.
        """
        relationships: List[RelationshipEdge] = []
        seen_edge_ids: Set[str] = set()

        doc_map = {d["document"]["document_id"]: d for d in documents_manifest if "document" in d}
        std_family_map: Dict[str, List[str]] = {}

        # Index standards by base family (e.g. 'IS-1786' -> ['IS-1786-2008'])
        for doc_id, item in doc_map.items():
            doc = item["document"]
            if doc.get("document_type") == "INDIAN_STANDARD":
                fam = doc.get("document_family_id")
                if fam:
                    std_family_map.setdefault(fam, []).append(doc_id)

        for doc_id, item in doc_map.items():
            doc = item["document"]
            dtype = doc.get("document_type")
            src_id = item.get("source", {}).get("source_id", "DISCOVERY")

            # 1. Amendment -> Standard (AMENDS)
            if dtype == "AMENDMENT":
                parent_id = doc.get("parent_document_id")
                if parent_id and parent_id in doc_map:
                    edge_id = generate_edge_id(doc_id, parent_id, "AMENDS")
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        relationships.append(
                            RelationshipEdge(
                                relationship_id=edge_id,
                                source_document_id=doc_id,
                                target_document_id=parent_id,
                                relationship_type="AMENDS",
                                confidence=1.0,
                                evidence_type="EXPLICIT_FIELD",
                                evidence_payload={"field": "parent_document_id", "value": parent_id},
                                discovered_via=src_id
                            )
                        )

            # 2. Product Manual -> Standard (CERTIFICATION_GUIDELINE_FOR)
            elif dtype in {"PRODUCT_MANUAL", "GROUPING_GUIDELINE"}:
                fam_id = doc.get("document_family_id", "")
                if fam_id.startswith("PM-IS-"):
                    target_fam = fam_id.replace("PM-", "")
                    matching_stds = std_family_map.get(target_fam, [])
                    for target_std in matching_stds:
                        edge_id = generate_edge_id(doc_id, target_std, "CERTIFICATION_GUIDELINE_FOR")
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            relationships.append(
                                RelationshipEdge(
                                    relationship_id=edge_id,
                                    source_document_id=doc_id,
                                    target_document_id=target_std,
                                    relationship_type="CERTIFICATION_GUIDELINE_FOR",
                                    confidence=0.95,
                                    evidence_type="CATALOG_CROSS_REFERENCE",
                                    evidence_payload={"source_family": fam_id, "target_family": target_fam},
                                    discovered_via=src_id
                                )
                            )

            # 3. SIT Schedule -> Standard (TESTING_SCHEDULE_FOR)
            elif dtype == "SIT_SCHEDULE":
                fam_id = doc.get("document_family_id", "")
                if fam_id.startswith("SIT-IS-"):
                    target_fam = fam_id.replace("SIT-", "")
                    matching_stds = std_family_map.get(target_fam, [])
                    for target_std in matching_stds:
                        edge_id = generate_edge_id(doc_id, target_std, "TESTING_SCHEDULE_FOR")
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            relationships.append(
                                RelationshipEdge(
                                    relationship_id=edge_id,
                                    source_document_id=doc_id,
                                    target_document_id=target_std,
                                    relationship_type="TESTING_SCHEDULE_FOR",
                                    confidence=0.95,
                                    evidence_type="CATALOG_CROSS_REFERENCE",
                                    evidence_payload={"source_family": fam_id, "target_family": target_fam},
                                    discovered_via=src_id
                                )
                            )

            # 4. Licence -> Standard (LICENCE_FOR_STANDARD)
            elif dtype == "LICENCE_RECORD":
                title = doc.get("title", "")
                # Find matching standard in corpus
                for fam, std_ids in std_family_map.items():
                    raw_num = fam.replace("IS-", "")
                    if f"IS {raw_num}" in title or f"IS-{raw_num}" in title:
                        for target_std in std_ids:
                            edge_id = generate_edge_id(doc_id, target_std, "LICENCE_FOR_STANDARD")
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                relationships.append(
                                    RelationshipEdge(
                                        relationship_id=edge_id,
                                        source_document_id=doc_id,
                                        target_document_id=target_std,
                                        relationship_type="LICENCE_FOR_STANDARD",
                                        confidence=0.90,
                                        evidence_type="DOCUMENT_TEXT",
                                        evidence_payload={"standard_reference": fam},
                                        discovered_via=src_id
                                    )
                                )

            # 5. CRS Registration -> Standard (REGISTRATION_FOR_PRODUCT)
            elif dtype == "CRS_REGISTRATION":
                title = doc.get("title", "")
                for fam, std_ids in std_family_map.items():
                    raw_num = fam.replace("IS-", "")
                    if f"IS {raw_num}" in title or f"IS-{raw_num}" in title:
                        for target_std in std_ids:
                            edge_id = generate_edge_id(doc_id, target_std, "REGISTRATION_FOR_PRODUCT")
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                relationships.append(
                                    RelationshipEdge(
                                        relationship_id=edge_id,
                                        source_document_id=doc_id,
                                        target_document_id=target_std,
                                        relationship_type="REGISTRATION_FOR_PRODUCT",
                                        confidence=0.90,
                                        evidence_type="DOCUMENT_TEXT",
                                        evidence_payload={"standard_reference": fam},
                                        discovered_via=src_id
                                    )
                                )

        return relationships
