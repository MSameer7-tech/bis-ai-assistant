"""
Relationship Extractor Module for Phase 2D Knowledge Graph Edges.
Constructs semantic graph triples (subject, predicate, object) using the standardized vocabulary:
- applies_to
- defines
- requires
- prohibits
- specifies
- tested_by
- measured_by
- has_limit
- has_condition
- references
- amends
- supersedes
- part_of
"""

import logging
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """Extracts typed semantic knowledge graph edges with full clause and page provenance."""

    def extract_relationships(
        self,
        processed_doc: Dict[str, Any],
        entities: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]] = None,
        cross_references: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Constructs rich semantic graph edges linking standards, clauses, requirements,
        parameters, tests, conditions, and regulations.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        std_num = str(doc_meta.get("standard_number") or doc_meta.get("title", doc_id)).strip()

        relationships: List[Dict[str, Any]] = []
        seen_triples: Set[str] = set()

        def add_edge(subj: str, pred: str, obj: str, clause: str, pages: List[int], extra: Dict[str, Any] = None):
            triple_key = f"{str(subj).strip()}:{pred}:{str(obj).strip()}"
            if triple_key in seen_triples:
                return
            seen_triples.add(triple_key)

            edge = {
                "relationship_id": f"REL-{doc_id.replace('-', '')}-{len(relationships) + 1:04d}",
                "subject": str(subj).strip(),
                "predicate": pred,
                "object": str(obj).strip(),
                "document_id": doc_id,
                "source_clause": clause,
                "source_pages": sorted(list(set(pages))),
            }
            if extra:
                edge.update(extra)
            relationships.append(edge)

        # 1. Standard -> Product applicability (applies_to)
        if "16102" in std_num or "Self-Ballasted" in doc_meta.get("title", ""):
            add_edge(std_num, "applies_to", "Self-Ballasted LED Lamp", "1", [6])
        if "15885" in std_num or "Controlgear" in doc_meta.get("title", ""):
            add_edge(std_num, "applies_to", "LED Controlgear", "1", [1])

        # 2. Document -> Clauses (part_of & defines)
        def traverse_clause_hierarchy(clauses: List[Dict[str, Any]], parent_title: str = None):
            for c in clauses:
                c_num = c.get("clause_number", "")
                c_title = c.get("title", f"Clause {c_num}")
                c_pages = c.get("page_refs", [c.get("page_start", 1)])
                c_text = c.get("content", "").lower()

                # Clause part_of Standard
                add_edge(f"Clause {c_num}: {c_title}", "part_of", std_num, c_num, c_pages)

                # Definitions (defines)
                if c_num.startswith("3") or "terminology" in c_text:
                    term_name = c_title.replace("Terminology", "").strip() or f"Term {c_num}"
                    add_edge(f"Clause {c_num}", "defines", term_name, c_num, c_pages)

                # Safety Prohibitions (prohibits)
                if "shall not" in c_text or "prohibited" in c_text or "must not" in c_text:
                    if "live parts" in c_text or "shock" in c_text:
                        add_edge(f"Clause {c_num}", "prohibits", "Access to Live Conductive Parts", c_num, c_pages)
                    if "exceed" in c_text and "temperature" in c_text:
                        add_edge(f"Clause {c_num}", "prohibits", "Cap Temperature Rise > 120 K", c_num, c_pages)

                if c.get("subclauses"):
                    traverse_clause_hierarchy(c["subclauses"], c_title)

        traverse_clause_hierarchy(processed_doc.get("clauses", []))

        # 3. Requirements -> Parameters, Limits, Tests, & Conditions (requires, has_limit, tested_by, has_condition)
        if requirements:
            for req in requirements:
                req_id = req["requirement_id"]
                clause_num = req["clause"]
                pages = req.get("source_pages", [1])
                param = req.get("parameter", req.get("property", "requirement"))

                add_edge(f"Clause {clause_num}", "requires", param, clause_num, pages)

                # Limit
                val = req.get("value")
                unit = req.get("unit", "")
                if val is not None:
                    limit_str = f"{req.get('operator', '')} {val} {unit}".strip()
                    add_edge(param, "has_limit", limit_str, clause_num, pages)

                # Tests & Measurement
                test_info = req.get("test", {})
                if test_info:
                    test_label = next(iter(test_info.values()), "Standard Test Method")
                    add_edge(param, "tested_by", str(test_label), clause_num, pages)

                # Ambient Conditions
                cond_info = req.get("conditions", {})
                if cond_info:
                    for cond_k, cond_v in cond_info.items():
                        add_edge(param, "has_condition", f"{cond_k}: {cond_v}", clause_num, pages)

        # 4. Cross-References (references, normative, test_method)
        if cross_references:
            for ref in cross_references:
                target = ref["target_standard"]
                if ref.get("target_location"):
                    target += f" ({ref['target_location']})"
                add_edge(std_num, "references", target, ref["source_clause"], ref["source_pages"], {"reference_type": ref["reference_type"]})

        # 5. Regulatory Orders (amends, supersedes, mandates_standard)
        if "CRO_Amendment" in doc_id or "Amendment" in doc_meta.get("title", ""):
            add_edge(std_num, "amends", "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order, 2021", "1", [1])
        if "2026" in std_num and "Part 1" in std_num:
            add_edge(std_num, "supersedes", "IS 16102 (Part 1) : 2012", "1", [1])

        logger.info("Extracted %d typed relationships for %s", len(relationships), doc_id)
        return relationships
