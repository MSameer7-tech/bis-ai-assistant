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

# Pattern for Indian Standard main section headings:
# e.g., "1 SCOPE", "2 REFERENCES", "5 MARKING", "8 INSULATION RESISTANCE", "ANNEX A", "SCHEDULE"
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:([0-9]{1,2})\s+([A-Z][A-Z\s\(\)\-\,\/]{2,80})|"
    r"(ANNEX(?:URE)?\s+[A-Z])\s*([A-Z\s\(\)\-\,\/]*)|"
    r"(SCHEDULE)\b|"
    r"(APPENDIX\s+[A-Z0-9]+)\b)",
    re.MULTILINE,
)

# Pattern for subclauses with dots: e.g., "1.1", "5.4.1", "8.2.1", "13.1"
# or Gazette section format: e.g. "1. Short title", "2. Compulsory compliance"
SUBCLAUSE_PATTERN = re.compile(
    r"^([0-9]{1,2}(?:\.[0-9]{1,2}){1,4})\b(?:\s*[\.\—\-])?\s*([^\n\r]*)",
    re.MULTILINE,
)

QCO_SECTION_PATTERN = re.compile(
    r"^([0-9]{1,2})\.\s+([A-Z][^\n\r—\.]+)[—\.\s]+",
    re.MULTILINE,
)


class StructureParser:
    """Deterministic hierarchical parser for standard specifications and statutory orders."""

    def parse_document_structure(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses page-level text into structured sections, hierarchical clauses, and annexes.
        Filters running headers and maintains page_start, page_end, and page_refs.
        """
        sections: List[Dict[str, Any]] = []
        annexes: List[Dict[str, Any]] = []
        flat_clauses: List[Dict[str, Any]] = []

        # 1. Clean and collect lines while filtering header/footer page numbers
        full_doc_lines: List[Dict[str, Any]] = []
        for page in pages:
            p_num = page["page_number"]
            raw_lines = page["text"].splitlines()
            for idx, line in enumerate(raw_lines):
                stripped = line.strip()
                if not stripped:
                    continue

                # Filter running header page numbers (e.g., lone digit right above "IS 16102" or "IS 15885")
                if stripped.isdigit() and idx + 1 < len(raw_lines) and "IS " in raw_lines[idx + 1]:
                    continue
                if stripped.isdigit() and len(stripped) <= 2 and idx == 0:
                    continue

                full_doc_lines.append({"page": p_num, "text": stripped})

        current_clause: Optional[Dict[str, Any]] = None
        current_annex: Optional[Dict[str, Any]] = None

        for item in full_doc_lines:
            line_text = item["text"]
            p_num = item["page"]

            # Check for Major Section / Annex (e.g., "1 SCOPE", "8 INSULATION RESISTANCE", "ANNEX A")
            sec_match = SECTION_HEADING_PATTERN.match(line_text)
            if sec_match:
                # Annex detection
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

                    annex_id = sec_match.group(3) or "ANNEX A"
                    annex_title = sec_match.group(4) or line_text
                    current_annex = {
                        "annex_id": annex_id.strip(),
                        "title": annex_title.strip() if annex_title else line_text,
                        "page_start": p_num,
                        "page_end": p_num,
                        "page_refs": [p_num],
                        "_page_set": {p_num},
                        "_page_set_max": p_num,
                        "content": line_text,
                    }
                    continue
                else:
                    sec_num = sec_match.group(1) or "1"
                    sec_title = sec_match.group(2) or line_text
                    sec_title = sec_title.strip()

                    sections.append({
                        "section_number": sec_num,
                        "title": sec_title,
                        "page_start": p_num,
                        "page_end": p_num,
                        "page_refs": [p_num],
                    })

                    # Top-level Section as a Root Clause (e.g., Clause 1, Clause 8)
                    if current_clause:
                        current_clause["page_end"] = current_clause["_page_set_max"]
                        current_clause["page_refs"] = sorted(list(current_clause["_page_set"]))
                        del current_clause["_page_set"]
                        del current_clause["_page_set_max"]
                        flat_clauses.append(current_clause)

                    current_clause = {
                        "clause_number": sec_num,
                        "title": sec_title,
                        "parent_clause": None,
                        "depth": 1,
                        "page_start": p_num,
                        "page_end": p_num,
                        "page_refs": [p_num],
                        "_page_set": {p_num},
                        "_page_set_max": p_num,
                        "content": line_text,
                        "subclauses": [],
                    }
                    continue

            # If inside an annex, continue accumulating annex text
            if current_annex:
                current_annex["content"] += "\n" + line_text
                current_annex["_page_set"].add(p_num)
                current_annex["_page_set_max"] = p_num
                continue

            # Check for Subclause (e.g. "1.1", "5.4.1", "8.2") or QCO section ("1. Short title")
            subclause_match = SUBCLAUSE_PATTERN.match(line_text) or QCO_SECTION_PATTERN.match(line_text)
            if subclause_match:
                clause_num = subclause_match.group(1).rstrip(".")
                clause_title = subclause_match.group(2).strip() or clause_num

                if current_clause and current_clause["clause_number"] == clause_num:
                    current_clause["content"] += "\n" + line_text
                    current_clause["_page_set"].add(p_num)
                    current_clause["_page_set_max"] = p_num
                    continue

                if "." in clause_num:
                    parent_clause = clause_num.rsplit(".", 1)[0]
                    depth = clause_num.count(".") + 1
                else:
                    parent_clause = None
                    depth = 1

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
