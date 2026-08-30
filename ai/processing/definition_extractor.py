"""
Definition Normalizer Module for Phase 2D (Clause 3 / Terminology).
Extracts canonical domain definitions (Self-Ballasted LED Lamp, Type, Rated Voltage,
Rated Wattage, Rated Frequency, Live Part, Type Test, ITQ, Batch, etc.) with multiline
continuation and provenance.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Regex pattern for definition lines:
# e.g., "3.1 Self-Ballasted LED Lamp — Unit which cannot..."
# e.g., "3.7 Live Part — Conductive part which may cause..."
DEFINITION_HEADER_REGEX = re.compile(
    r"^(?:(?:Clause\s+)?([0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]+)?)\s+)?([A-Za-z0-9\s\(\)\/\-\,\'\"]+?)\s*(?:[\—\–]|\s+\-\s+|\:\s+)\s*(.*)$",
    re.DOTALL,
)


class DefinitionExtractor:
    """Extracts typed definition entities from Terminology/Definition clauses."""

    def extract_definitions(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans Clause 3 and terminology sections to produce canonical definition objects.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        source_id = processed_doc.get("source_id", "SRC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        std_num = str(doc_meta.get("standard_number") or doc_meta.get("title", doc_id)).strip()

        definitions: List[Dict[str, Any]] = []

        def parse_clause(clause: Dict[str, Any]):
            c_num = str(clause.get("clause_number", ""))
            c_title = str(clause.get("title", "")).strip()
            c_text = str(clause.get("content", "")).strip()
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])

            is_def_clause = (
                c_num.startswith("3.")
                or c_num == "3"
                or "terminology" in c_title.lower()
                or "definition" in c_title.lower()
                or clause.get("semantic_type") == "definition"
            )

            if is_def_clause:
                lines = [l.strip() for l in c_text.splitlines() if l.strip()]
                i = 0
                while i < len(lines):
                    line = lines[i]
                    match = DEFINITION_HEADER_REGEX.match(line)
                    if match:
                        clause_ref = match.group(1) or c_num
                        term_name = match.group(2).strip()
                        initial_def = match.group(3).strip()

                        # Collect continuation lines until next definition header
                        def_lines = [initial_def]
                        j = i + 1
                        while j < len(lines):
                            next_line = lines[j]
                            # If next line is a new definition header, break
                            if DEFINITION_HEADER_REGEX.match(next_line):
                                break
                            # If next line starts with a new subclause or section, break
                            if re.match(r"^[0-9]{1,2}\.[0-9]{1,2}", next_line):
                                break
                            def_lines.append(next_line)
                            j += 1

                        full_def = " ".join(def_lines).strip()
                        i = j

                        # Filter non-definition headers
                        if len(term_name) < 2 or len(full_def) < 10 or term_name.isdigit():
                            continue
                        if any(term_name.lower().startswith(skip) for skip in ("table", "annex", "fig", "note")):
                            continue

                        def_id = f"DEF-{doc_id.replace('-', '')}-{len(definitions) + 1:04d}"
                        definitions.append({
                            "entity_type": "definition",
                            "definition_id": def_id,
                            "term": term_name,
                            "definition": full_def,
                            "source_clause": clause_ref,
                            "source_pages": c_pages,
                            "provenance": {
                                "document_id": doc_id,
                                "source_id": source_id,
                                "standard": std_num,
                                "clause": clause_ref,
                                "page": c_pages[0] if c_pages else 1,
                                "pages": c_pages,
                                "section": "3 TERMINOLOGY",
                                "original_text": full_def[:250],
                            },
                        })
                    else:
                        i += 1

                # Fallback for structured subclauses (e.g. 3.1 Self-Ballasted LED Lamp)
                if not definitions and c_num.startswith("3."):
                    term_name = c_title if c_title and not c_title.startswith("3.") else f"Term {c_num}"
                    def_id = f"DEF-{doc_id.replace('-', '')}-{len(definitions) + 1:04d}"
                    definitions.append({
                        "entity_type": "definition",
                        "definition_id": def_id,
                        "term": term_name,
                        "definition": c_text,
                        "source_clause": c_num,
                        "source_pages": c_pages,
                        "provenance": {
                            "document_id": doc_id,
                            "source_id": source_id,
                            "standard": std_num,
                            "clause": c_num,
                            "page": c_pages[0] if c_pages else 1,
                            "pages": c_pages,
                            "section": "3 TERMINOLOGY",
                            "original_text": c_text[:250],
                        },
                    })

            if clause.get("subclauses"):
                for sub in clause["subclauses"]:
                    parse_clause(sub)

        for root in processed_doc.get("clauses", []):
            parse_clause(root)

        logger.info("Extracted %d normalized definitions from %s", len(definitions), doc_id)
        return definitions


def extract_definitions(processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience helper function to extract definitions."""
    extractor = DefinitionExtractor()
    return extractor.extract_definitions(processed_doc)
