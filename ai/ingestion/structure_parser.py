"""
Deterministic Structure Parser Module for Indian Standards and Gazette Orders.
Extracts hierarchical sections, clauses, subclauses, annexes, and schedules
with full page range boundaries and page reference arrays.
No LLM dependencies.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Deterministic regex patterns
SECTION_PATTERN = re.compile(
    r"^(?:(?:SECTION\s+)?([0-9]{1,2})\s+([A-Z\s\(\)\-\,\/]{3,80})|"
    r"(ANNEX(?:URE)?\s+[A-Z])\s*([A-Z\s\(\)\-\,\/]*)|"
    r"(SCHEDULE)\b|"
    r"(APPENDIX\s+[A-Z0-9]+)\b)",
    re.MULTILINE,
)

CLAUSE_NUMBER_PATTERN = re.compile(
    r"^([0-9]{1,2}(?:\.[0-9]{1,2}){0,4})\b(?:\s*[\.\—\-])?\s*([^\n\r]*)",
    re.MULTILINE,
)


class StructureParser:
    """Deterministic hierarchical parser for standard specifications and statutory orders."""

    def parse_document_structure(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses page-level text into structured sections, hierarchical clauses, and annexes.
        Maintains page_start, page_end, and explicit page_refs arrays for every unit.
        """
        sections: List[Dict[str, Any]] = []
        annexes: List[Dict[str, Any]] = []
        flat_clauses: List[Dict[str, Any]] = []

        full_doc_lines: List[Dict[str, Any]] = []
        for page in pages:
            p_num = page["page_number"]
            for line in page["text"].splitlines():
                stripped = line.strip()
                if stripped:
                    full_doc_lines.append({"page": p_num, "text": stripped})

        current_clause: Optional[Dict[str, Any]] = None
        current_annex: Optional[Dict[str, Any]] = None

        for item in full_doc_lines:
            line_text = item["text"]
            p_num = item["page"]

            # 1. Section / Annex Detection
            sec_match = SECTION_PATTERN.match(line_text)
            if sec_match:
                sec_num = sec_match.group(1) or sec_match.group(3) or sec_match.group(5) or "ANNEX"
                sec_title = sec_match.group(2) or sec_match.group(4) or line_text
                sec_title = sec_title.strip() if sec_title else line_text

                # Finalize any active clause before switching to an annex
                if "ANNEX" in line_text.upper():
                    if current_clause:
                        current_clause["page_end"] = current_clause["_page_set_max"]
                        current_clause["page_refs"] = sorted(list(current_clause["_page_set"]))
                        del current_clause["_page_set"]
                        del current_clause["_page_set_max"]
                        flat_clauses.append(current_clause)
                        current_clause = None

                    if current_annex:
                        current_annex["page_end"] = current_annex["_page_set_max"]
                        current_annex["page_refs"] = sorted(list(set(current_annex["_page_set"])))
                        del current_annex["_page_set"]
                        del current_annex["_page_set_max"]
                        annexes.append(current_annex)

                    current_annex = {
                        "annex_id": sec_num if "ANNEX" in sec_num else f"ANNEX {sec_num}",
                        "title": sec_title,
                        "page_start": p_num,
                        "page_end": p_num,
                        "page_refs": [p_num],
                        "_page_set": {p_num},
                        "_page_set_max": p_num,
                        "content": line_text,
                    }
                    continue
                else:
                    sections.append({
                        "section_number": sec_num,
                        "title": sec_title,
                        "page_start": p_num,
                        "page_end": p_num,
                        "page_refs": [p_num],
                    })

            # If inside an annex, continue accumulating annex content
            if current_annex:
                current_annex["content"] += "\n" + line_text
                current_annex["_page_set"].add(p_num)
                current_annex["_page_set_max"] = p_num
                continue

            # 2. Clause / Subclause Detection
            clause_match = CLAUSE_NUMBER_PATTERN.match(line_text)
            if clause_match:
                clause_num = clause_match.group(1).rstrip(".")
                clause_title = clause_match.group(2).strip() or clause_num

                if "." in clause_num:
                    parent_clause = clause_num.rsplit(".", 1)[0]
                    depth = clause_num.count(".") + 1
                else:
                    parent_clause = None
                    depth = 1

                # Finalize previous clause
                if current_clause:
                    current_clause["page_end"] = current_clause["_page_set_max"]
                    current_clause["page_refs"] = sorted(list(current_clause["_page_set"]))
                    del current_clause["_page_set"]
                    del current_clause["_page_set_max"]
                    flat_clauses.append(current_clause)

                current_clause = {
                    "clause_number": clause_num,
                    "title": clause_title,
                    "parent_clause": parent_clause,
                    "depth": depth,
                    "page_start": p_num,
                    "page_end": p_num,
                    "page_refs": [p_num],
                    "_page_set": {p_num},
                    "_page_set_max": p_num,
                    "content": line_text,
                    "subclauses": [],
                }
            else:
                if current_clause:
                    current_clause["content"] += "\n" + line_text
                    current_clause["_page_set"].add(p_num)
                    current_clause["_page_set_max"] = p_num

        # Finalize open clause
        if current_clause:
            current_clause["page_end"] = current_clause["_page_set_max"]
            current_clause["page_refs"] = sorted(list(current_clause["_page_set"]))
            del current_clause["_page_set"]
            del current_clause["_page_set_max"]
            flat_clauses.append(current_clause)

        # Finalize open annex
        if current_annex:
            current_annex["page_end"] = current_annex["_page_set_max"]
            current_annex["page_refs"] = sorted(list(set(current_annex["_page_set"])))
            del current_annex["_page_set"]
            del current_annex["_page_set_max"]
            annexes.append(current_annex)

        # 3. Build hierarchical tree from flat clauses
        hierarchical_clauses = self._build_clause_tree(flat_clauses)

        logger.info(
            "Deterministic parse complete: %d sections, %d total clauses (%d top-level), %d annexes",
            len(sections),
            len(flat_clauses),
            len(hierarchical_clauses),
            len(annexes),
        )

        return {
            "sections": sections,
            "clauses": hierarchical_clauses,
            "flat_clauses": flat_clauses,
            "flat_clauses_count": len(flat_clauses),
            "annexes": annexes,
        }

    def _build_clause_tree(self, flat_clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Constructs a nested hierarchical tree from a flat list of clauses."""
        clause_map: Dict[str, Dict[str, Any]] = {}
        root_clauses: List[Dict[str, Any]] = []

        for c in flat_clauses:
            clause_num = c["clause_number"]
            node = dict(c)
            node["subclauses"] = []
            clause_map[clause_num] = node

        for c in flat_clauses:
            clause_num = c["clause_number"]
            node = clause_map[clause_num]
            parent_num = c.get("parent_clause")

            if parent_num and parent_num in clause_map:
                clause_map[parent_num]["subclauses"].append(node)
                for p in node.get("page_refs", []):
                    if p not in clause_map[parent_num]["page_refs"]:
                        clause_map[parent_num]["page_refs"].append(p)
                clause_map[parent_num]["page_refs"].sort()
                clause_map[parent_num]["page_start"] = min(clause_map[parent_num]["page_refs"])
                clause_map[parent_num]["page_end"] = max(clause_map[parent_num]["page_refs"])
            else:
                root_clauses.append(node)

        return root_clauses


def parse_structure(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience helper function to parse document structure."""
    parser = StructureParser()
    return parser.parse_document_structure(pages)
