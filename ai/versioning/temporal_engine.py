"""
Temporal Query and Effective Date Evaluation Engine (Step 14).
Evaluates whether a standard requirement was in force on a given historical or current date.
Enables answering:
- "What is the current requirement today?"
- "What was the requirement on 2015-06-01 (before Amendment No. 1)?"
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class TemporalEngine:
    """Filters and retrieves requirements by effective date window."""

    def filter_effective_requirements(
        self,
        requirements: List[Dict[str, Any]],
        query_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns requirements active on query_date (format YYYY-MM-DD or ISO).
        If query_date is None, returns current active requirements (valid_until is None or > today).
        """
        target_date = datetime.fromisoformat(query_date.split("T")[0]) if query_date else datetime.now()

        effective_reqs: List[Dict[str, Any]] = []

        for req in requirements:
            v_from_str = req.get("valid_from")
            v_until_str = req.get("valid_until")

            v_from = datetime.fromisoformat(v_from_str.split("T")[0]) if v_from_str else datetime.min
            v_until = datetime.fromisoformat(v_until_str.split("T")[0]) if v_until_str else datetime.max

            if v_from <= target_date <= v_until:
                effective_reqs.append(req)

        return effective_reqs
