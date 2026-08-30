"""
Chunk Boundary Rules and Normative Analysis for Phase 2E.
Determines semantic boundaries, modal force, and hierarchy path lineage.
"""

import re
from typing import Any, Dict, List, Tuple
from ai.chunking.schema import NormativeContext, NormativeForce

MODAL_PATTERNS = [
    (r"\bshall\s+not\b", "shall not"),
    (r"\bshall\b", "shall"),
    (r"\bmust\s+not\b", "must not"),
    (r"\bmust\b", "must"),
    (r"\bshould\b", "should"),
    (r"\bmay\b", "may"),
    (r"\bunder\s+consideration\b", "under consideration"),
    (r"\bcompliance\s+is\s+checked\b", "compliance is checked by"),
    (r"\bnote\b", "note"),
]


def extract_normative_context(text: str, reqs: List[Dict[str, Any]]) -> NormativeContext:
    """Extracts modal auxiliary keywords, normative force, and verbatim statements."""
    text_lower = text.lower()
    modals = []
    for pat, label in MODAL_PATTERNS:
        if re.search(pat, text_lower):
            modals.append(label)

    # Determine Normative Force accurately
    if any(r.get("status") == "mandatory" for r in reqs):
        force = NormativeForce.MANDATORY
    elif reqs and all(r.get("status") == "under_consideration" for r in reqs):
        force = NormativeForce.UNDER_CONSIDERATION
    elif "shall not" in modals or "must not" in modals:
        force = NormativeForce.PROHIBITION
    elif "shall" in modals or "must" in modals:
        force = NormativeForce.MANDATORY
    elif "under consideration" in text_lower and not any(r.get("status") == "mandatory" for r in reqs):
        force = NormativeForce.UNDER_CONSIDERATION
    elif "should" in modals:
        force = NormativeForce.RECOMMENDATION
    else:
        force = NormativeForce.INFORMATIVE

    verbatim = []
    for line in text.splitlines():
        l_str = line.strip()
        if any(m in l_str.lower() for m in ("shall", "must", "not less than", "shall not exceed", "under consideration")):
            if len(l_str) > 10:
                verbatim.append(l_str)

    comp_method = None
    if "compliance is checked" in text_lower or "test" in text_lower:
        for line in text.splitlines():
            if "compliance is checked" in line.lower() or "is checked by" in line.lower():
                comp_method = line.strip()
                break

    return NormativeContext(
        normative_force=force,
        modal_keywords=modals,
        verbatim_normative_statements=verbatim,
        compliance_verification_method=comp_method,
    )
