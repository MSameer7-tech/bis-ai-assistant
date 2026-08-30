"""
Structure Parser Module to detect sections, clauses, subclauses, annexes, and schedules
from page-level text streams with exact page range preservation.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regex patterns for Indian Standards and Gazette Orders
# e.g., "1 SCOPE", "8 INSULATION RESISTANCE", "1.1", "8.2.1", "ANNEX A", "SCHEDULE"
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:(?:SECTION\s+)?(\d{1,2})\s+([A-Z\s\(\)\-\,\/]{3,80})|"
    r"(ANNEX(?:URE)?\s+[A-Z])\s*([A-Z\s\(\)\-\,\/]*)|"
    r"(SCHEDULE)\b|"
    r"(APPENDIX\s+[A-Z0-9]+)\b)",
    re.MULTILINE,
)

CLAUSE_PATTERN = re.compile(
    r"^(\d{1,2}(?:\.\d{1,2}){0,4})\s+([^\n\r]+)",
    re.MULTILINE,
)

QCO_SECTION_PATTERN = re.compile(
    r"^(\d+)\.\s+([^\n\r—\.]+)[—\.\s]+",
    re.MULTILINE,
)


class StructureParser:
    """Parses page streams into hierarchical sections, clauses, and annexes."""

    def parse_document_structure(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses page-level text into structured sections, clauses, and annexes.
        Tracks physical start and end pages for every structural unit.
        """
        sections: List[Dict[str, Any]] = []
        clauses: List[Dict[str, Any]] = []
        annexes: List[Dict[str, Any]] = []

        full_doc_lines: List[Dict[str, Any]] = []
        for page in pages:
            p_num = page["page_number"]
            for line in page["text"].splitlines():
                stripped = line.strip()
                if stripped:
                    full_doc_lines.append({"page": p_num, "text": stripped})

        current_clause: Optional[Dict[str, Any]] = None

        for item in full_doc_lines:
            line_text = item["text"]
            p_num = item["page"]

            # 1. Check for Major Section / Annex
            section_match = SECTION_HEADING_PATTERN.match(line_text)
            if section_match:
                sec_num = section_match.group(1) or section_match.group(3) or section_match.group(5) or "ANNEX"
                sec_title = section_match.group(2) or section_match.group(4) or line_text
                sec_title = sec_title.strip() if sec_title else line_text

                if "ANNEX" in line_text.upper():
                    annexes.append({
                        "annex_id": sec_num,
                        "title": sec_title,
                        "page_start": p_num,
                        "page_end": p_num,
                        "content": line_text,
                    })
                else:
                    sections.append({
                        "section_number": sec_num,
                        "title": sec_title,
                        "page_start": p_num,
                        "page_end": p_num,
                    })

            # 2. Check for Standard Clause / Subclause (e.g. 1.1, 8.2) or QCO Section (e.g. 1. Short title)
            clause_match = CLAUSE_PATTERN.match(line_text) or QCO_SECTION_PATTERN.match(line_text)
            if clause_match:
                clause_num = clause_match.group(1)
                clause_title = clause_match.group(2).strip()

                # Determine parent clause (e.g., parent of 8.2.1 is 8.2, parent of 8.2 is 8)
                parent = clause_num.rsplit(".", 1)[0] if "." in clause_num else None

                # Finalize previous clause
                if current_clause:
                    current_clause["page_end"] = p_num
                    clauses.append(current_clause)

                current_clause = {
                    "clause_number": clause_num,
                    "title": clause_title,
                    "parent_clause": parent,
                    "page_start": p_num,
                    "page_end": p_num,
                    "content": line_text,
                }
            else:
                if current_clause:
                    current_clause["content"] += "\n" + line_text
                    current_clause["page_end"] = p_num

        if current_clause:
            clauses.append(current_clause)

        logger.info(
            "Parsed structure: %d sections, %d clauses, %d annexes",
            len(sections),
            len(clauses),
            len(annexes),
        )

        return {
            "sections": sections,
            "clauses": clauses,
            "annexes": annexes,
        }


def parse_structure(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience helper function to parse document structure."""
    parser = StructureParser()
    return parser.parse_document_structure(pages)
