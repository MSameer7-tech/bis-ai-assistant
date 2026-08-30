"""
Amendment Processor and Specification Consolidation Engine (Steps 13 & 14).
Synthesizes Base Standards with successive Amendments to produce:
BASE STANDARD + AMENDMENTS -> CURRENT EFFECTIVE REQUIREMENTS
Maintains temporal validity windows (valid_from, valid_until) and tracks superseded requirements.
"""

import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AmendmentProcessor:
    """Consolidates base standards with amendments and applies temporal validity constraints."""

    def apply_amendment_to_base(
        self,
        base_norm_doc: Dict[str, Any],
        amendment_norm_doc: Dict[str, Any],
        effective_date: str,
        amendment_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a base document with an amendment.
        Updates temporal validity on superseded requirements and inserts new active requirements.
        """
        consolidated = copy.deepcopy(base_norm_doc)
        base_id = base_norm_doc.get("document_id", "BASE")
        amd_id = amendment_norm_doc.get("document_id", "AMD")
        amd_label = amendment_label or amendment_norm_doc.get("document_metadata", {}).get("title", amd_id)

        base_meta = base_norm_doc.get("document_metadata", {})
        base_pub_date = base_meta.get("publication_date", "2012-08-01")

        # Map base requirements by parameter + clause key
        base_reqs = consolidated.get("requirements", [])
        for r in base_reqs:
            if not r.get("valid_from"):
                r["valid_from"] = base_pub_date
            if "valid_until" not in r:
                r["valid_until"] = None
            if not r.get("temporal_status"):
                r["temporal_status"] = "current"

        req_map = {r.get("parameter", "") + "@" + str(r.get("clause", "")): r for r in base_reqs}

        amended_reqs = amendment_norm_doc.get("requirements", [])
        modified_count = 0
        added_count = 0

        for amd_r in amended_reqs:
            key = amd_r.get("parameter", "") + "@" + str(amd_r.get("clause", ""))
            amd_r_copy = copy.deepcopy(amd_r)
            amd_r_copy["valid_from"] = effective_date
            amd_r_copy["valid_until"] = None
            amd_r_copy["temporal_status"] = "current"
            amd_r_copy["amendment_id"] = amd_id
            amd_r_copy["amendment_label"] = amd_label

            if key in req_map:
                # Existing requirement is superseded by amendment
                old_r = req_map[key]
                old_r["valid_until"] = effective_date
                old_r["temporal_status"] = "superseded"
                old_r["superseded_by"] = amd_r_copy.get("requirement_id")
                modified_count += 1
                consolidated["requirements"].append(amd_r_copy)
            else:
                # Newly added requirement from amendment
                added_count += 1
                consolidated["requirements"].append(amd_r_copy)

        # Merge or update tables if amendment has tables
        amd_tables = amendment_norm_doc.get("tables", [])
        if amd_tables:
            base_t_ids = {t.get("table_id") for t in consolidated.get("tables", [])}
            for at in amd_tables:
                if at.get("table_id") not in base_t_ids:
                    consolidated.setdefault("tables", []).append(at)

        # Update metadata
        consolidated["document_metadata"]["amendments_applied"] = consolidated.get("document_metadata", {}).get("amendments_applied", [])
        consolidated["document_metadata"]["amendments_applied"].append({
            "amendment_id": amd_id,
            "amendment_label": amd_label,
            "effective_date": effective_date,
            "applied_at": datetime.now().isoformat(),
            "requirements_modified_count": modified_count,
            "requirements_added_count": added_count,
        })

        consolidated["consolidation_summary"] = {
            "base_document_id": base_id,
            "amendment_document_id": amd_id,
            "effective_date": effective_date,
            "total_active_requirements": len([r for r in consolidated["requirements"] if r.get("temporal_status") == "current"]),
            "total_superseded_requirements": len([r for r in consolidated["requirements"] if r.get("temporal_status") == "superseded"]),
        }

        logger.info(
            "✅ Applied amendment %s onto %s: %d modified (superseded), %d added -> Active Reqs: %d",
            amd_id,
            base_id,
            modified_count,
            added_count,
            consolidated["consolidation_summary"]["total_active_requirements"],
        )

        return consolidated
