"""
Relationship Extractor Module.
Constructs explicit semantic graph relationships (triples) linking standards,
products, parameters, tests, and regulations with provenance.
"""

import logging
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """Extracts typed semantic relationships from document structure and entities."""

    def extract_relationships(
        self, processed_doc: Dict[str, Any], entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extracts semantic graph triples (subject, predicate, object) with provenance.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        std_num = doc_meta.get("standard_number") or doc_meta.get("title", doc_id)

        relationships: List[Dict[str, Any]] = []
        seen_triples: Set[str] = set()

        def add_rel(subj: str, pred: str, obj: str, clause: str, pages: List[int]):
            triple_key = f"{subj}:{pred}:{obj}"
            if triple_key in seen_triples:
                return
            seen_triples.add(triple_key)

            relationships.append({
                "relationship_id": f"REL-{doc_id}-{len(relationships) + 1:04d}",
                "subject": subj,
                "predicate": pred,
                "object": obj,
                "document_id": doc_id,
                "source_clause": clause,
                "source_pages": sorted(list(set(pages))),
            })

        # 1. Standard -> Product applicability
        if "16102" in std_num or "LED" in doc_meta.get("title", ""):
            add_rel(std_num, "applies_to", "Self-Ballasted LED Lamp", "1", [6])

        # 2. Standard -> Referenced Standards
        for ent in entities:
            if ent["entity_type"] == "referenced_standard":
                add_rel(std_num, "references", ent["name"], ent["source_clause"], ent["source_pages"])

        # 3. Standard -> Tests
        for clause in processed_doc.get("clauses", []):
            c_text = clause.get("content", "").lower()
            c_num = clause.get("clause_number", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])

            if "insulation resistance" in c_text:
                add_rel(std_num, "specifies_test", "Insulation Resistance Test", c_num, c_pages)
            if "electric strength" in c_text:
                add_rel(std_num, "specifies_test", "Electric Strength Test", c_num, c_pages)
            if "torque" in c_text:
                add_rel(std_num, "specifies_test", "Mechanical Torque Test", c_num, c_pages)
            if "glow-wire" in c_text or "glow wire" in c_text:
                add_rel(std_num, "specifies_test", "Glow-Wire Flammability Test", c_num, c_pages)
            if "fault condition" in c_text:
                add_rel(std_num, "specifies_test", "Fault Condition Safety Test", c_num, c_pages)
            if "marking" in c_text:
                add_rel(std_num, "specifies_marking", "Mandatory Markings", c_num, c_pages)

        # 4. Regulatory relations (for QCOs)
        if "CRO" in std_num or "Compulsory Registration" in doc_meta.get("title", ""):
            add_rel(std_num, "mandates_scheme", "Scheme-II (Compulsory Registration Scheme)", "2", [1])
            add_rel(std_num, "mandates_standard", "IS 16102 (Part 1)", "SCHEDULE", [1])
            add_rel(std_num, "mandates_standard", "IS 15885 (Part 2/Sec 13)", "SCHEDULE", [1])

        logger.info("Extracted %d relationships for %s", len(relationships), doc_id)
        return relationships
