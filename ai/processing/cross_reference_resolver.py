"""
Cross-Reference Resolver Module for Phase 2D.
Identifies and categorizes all standard and clause references into typed relationships:
- normative
- informative
- test_method
- definition
- related_standard
"""

import logging
import re
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

# Standard reference regex
STANDARD_REF_REGEX = re.compile(
    r"\b((?:IS(?:/IEC)?|IEC)\s+[0-9]{3,6}(?:\s*\([^\)\n]+\))?(?:\s*:\s*[0-9]{4})?)\b",
    re.IGNORECASE,
)

TARGET_LOCATION_REGEX = re.compile(
    r"\b(?:(Clause|Section|Annex|Table|Part)\s+([A-Z0-9\.\-]+))\b",
    re.IGNORECASE,
)


class CrossReferenceResolver:
    """Resolves cross-references from clause text into structured typed references."""

    def resolve_references(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts structured cross-reference objects with target standard, target location,
        and typed classification (normative, test_method, definition, related_standard, informative).
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        doc_meta = processed_doc.get("document_metadata", {})
        std_num = str(doc_meta.get("standard_number", "")).upper()

        references: List[Dict[str, Any]] = []
        seen_refs: Set[str] = set()

        def scan_clause(clause: Dict[str, Any]):
            c_num = str(clause.get("clause_number", ""))
            c_text = clause.get("content", "")
            c_pages = clause.get("page_refs", [clause.get("page_start", 1)])
            c_lower = c_text.lower()

            for match in STANDARD_REF_REGEX.finditer(c_text):
                target_std = match.group(1).strip()
                if target_std.upper() == std_num:
                    continue

                # Context snippet around match
                start_pos = max(0, match.start() - 60)
                end_pos = min(len(c_text), match.end() + 80)
                snippet = c_text[start_pos:end_pos].replace("\n", " ").strip()

                # Determine target sub-location if cited (e.g. "Annex A", "Clause 4")
                target_loc = None
                loc_match = TARGET_LOCATION_REGEX.search(c_text[match.end():match.end() + 40])
                if loc_match:
                    target_loc = f"{loc_match.group(1)} {loc_match.group(2)}"

                # Classify reference type
                if c_num == "3" or c_num.startswith("3.") or "terminology" in c_lower or "definition" in c_lower:
                    ref_type = "definition"
                elif "test" in c_lower or "method" in c_lower or "measured" in c_lower or "checked" in c_lower or "8913" in target_std or "11000" in target_std:
                    ref_type = "test_method"
                elif "16102" in target_std or "16103" in target_std or "part 2" in target_std.lower():
                    ref_type = "related_standard"
                elif "note" in snippet.lower() or "foreword" in c_lower:
                    ref_type = "informative"
                else:
                    ref_type = "normative"

                ref_key = f"{c_num}:{target_std}:{target_loc or ''}"
                if ref_key in seen_refs:
                    continue
                seen_refs.add(ref_key)

                references.append({
                    "reference_id": f"REF-{doc_id.replace('-', '')}-{len(references) + 1:04d}",
                    "document_id": doc_id,
                    "source_clause": c_num,
                    "source_pages": c_pages,
                    "target_standard": target_std,
                    "target_location": target_loc,
                    "reference_type": ref_type,
                    "context_snippet": snippet,
                })

            if clause.get("subclauses"):
                for sub in clause["subclauses"]:
                    scan_clause(sub)

        for root in processed_doc.get("clauses", []):
            scan_clause(root)

        logger.info("Resolved %d structured cross-references for %s", len(references), doc_id)
        return references


def resolve_cross_references(processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience helper function to resolve cross-references."""
    resolver = CrossReferenceResolver()
    return resolver.resolve_references(processed_doc)
