"""
Clause Classifier Module for Phase 2D.
Classifies clauses into distinct semantic roles:
- scope
- definition
- reference
- requirement
- test_method
- acceptance_criterion
- marking_requirement
- sampling_requirement
- procedure
- exception
- note
- table_requirement
- annex
- compliance_condition
- classification
"""

import logging
import re
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

# Semantic classification keywords & regexes
SCOPE_KEYWORDS = {"scope", "applies to", "application", "covered by this standard", "shall apply to"}
DEFINITION_KEYWORDS = {"terminology", "terms and definitions", "definition", "means a", "is defined as"}
REFERENCE_KEYWORDS = {"normative references", "references", "referred to in", "in accordance with is"}
MARKING_KEYWORDS = {"marking", "marked on the", "standard mark", "legibility", "packaging marking"}
SAMPLING_KEYWORDS = {"sampling", "initial test quantity", "itq", "sample size", "batch size", "inspection lot"}
EXCEPTION_KEYWORDS = {"exemption", "except", "not apply to", "unless otherwise specified"}
TEST_METHOD_KEYWORDS = {"test method", "tested in accordance", "conditioning", "measured in accordance", "application of test"}
ACCEPTANCE_KEYWORDS = {"shall not be less than", "shall withstand", "no flashover", "no breakdown", "shall be not more than", "compliance is checked"}


class ClauseClassifier:
    """Classifies standard clauses into semantic knowledge categories."""

    def classify_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assigns a primary semantic_type and a list of semantic_tags to a clause.
        """
        c_num = str(clause.get("clause_number", ""))
        c_title = str(clause.get("title", "")).lower()
        c_text = str(clause.get("content", "")).lower()

        tags: Set[str] = set()

        # 1. Check Scope
        if c_num in ("1", "1.0", "1.1") or any(k in c_title or k in c_text[:100] for k in SCOPE_KEYWORDS):
            tags.add("scope")

        # 2. Check Definitions
        if c_num.startswith("3") or any(k in c_title or k in c_text[:100] for k in DEFINITION_KEYWORDS):
            tags.add("definition")

        # 3. Check References
        if c_num == "2" or any(k in c_title for k in REFERENCE_KEYWORDS):
            tags.add("reference")

        # 4. Check Marking
        if c_num.startswith("5") or c_num.startswith("6") or any(k in c_title or k in c_text for k in MARKING_KEYWORDS):
            if "marking" in c_title or "marked" in c_text:
                tags.add("marking_requirement")

        # 5. Check Sampling
        if any(k in c_title or k in c_text for k in SAMPLING_KEYWORDS):
            tags.add("sampling_requirement")

        # 6. Check Exceptions
        if any(k in c_text for k in EXCEPTION_KEYWORDS):
            tags.add("exception")

        # 7. Check Test Method
        if any(k in c_title or k in c_text for k in TEST_METHOD_KEYWORDS) or "test" in c_title:
            tags.add("test_method")

        # 8. Check Acceptance Criterion
        if any(k in c_text for k in ACCEPTANCE_KEYWORDS) or "pass" in c_text or "fail" in c_text:
            tags.add("acceptance_criterion")

        # 9. Default Technical Requirement
        if "shall" in c_text or "must" in c_text or "requirement" in c_title:
            tags.add("requirement")

        if not tags:
            tags.add("note" if "note" in c_text[:50] else "requirement")

        # Determine primary type
        priority_order = [
            "scope",
            "marking_requirement",
            "sampling_requirement",
            "definition",
            "reference",
            "acceptance_criterion",
            "test_method",
            "requirement",
            "exception",
            "note",
        ]
        primary_type = next((t for t in priority_order if t in tags), list(tags)[0])

        return {
            "primary_type": primary_type,
            "semantic_tags": sorted(list(tags)),
        }

    def classify_all_clauses(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively classifies all clauses in a hierarchical tree."""
        classified_list = []
        for c in clauses:
            node = dict(c)
            classification = self.classify_clause(c)
            node["semantic_type"] = classification["primary_type"]
            node["semantic_tags"] = classification["semantic_tags"]

            if c.get("subclauses"):
                node["subclauses"] = self.classify_all_clauses(c["subclauses"])

            classified_list.append(node)
        return classified_list


def classify_clauses(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convenience helper function to classify a list of clauses."""
    classifier = ClauseClassifier()
    return classifier.classify_all_clauses(clauses)
