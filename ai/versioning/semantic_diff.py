"""
Semantic Diff Engine for BIS Standards (Step 6).
Performs deep comparison between normalized documents across:
- Requirements (added, removed, modified limits/operators)
- Definitions (added, removed, modified terms)
- Entities (added, removed, modified parameters/components)
- Cross-References (added, removed, modified citations)
- Tables (added, removed, modified rows/limits)
- Metadata (revision changed, publication date changed, status changed)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SemanticDiffEngine:
    """Computes full semantic difference between two normalized BIS document artifacts."""

    def compare_documents(
        self, old_norm_doc: Dict[str, Any], new_norm_doc: Dict[str, Any]
    ) -> Dict[str, Any]:
        old_id = old_norm_doc.get("document_id", "OLD")
        new_id = new_norm_doc.get("document_id", "NEW")

        # 1. Metadata Changes
        old_meta = old_norm_doc.get("document_metadata", {})
        new_meta = new_norm_doc.get("document_metadata", {})

        meta_changes: List[Dict[str, Any]] = []
        for field in ("edition", "revision", "publication_date", "status", "standard_number", "title"):
            o_val = old_meta.get(field) or old_norm_doc.get(field)
            n_val = new_meta.get(field) or new_norm_doc.get(field)
            if o_val != n_val:
                meta_changes.append({"field": field, "old": o_val, "new": n_val})

        # 2. Compare Requirements
        old_reqs = {r.get("parameter", "") + "@" + str(r.get("clause", "")): r for r in old_norm_doc.get("requirements", [])}
        new_reqs = {r.get("parameter", "") + "@" + str(r.get("clause", "")): r for r in new_norm_doc.get("requirements", [])}

        added_reqs: List[Dict[str, Any]] = []
        removed_reqs: List[Dict[str, Any]] = []
        modified_reqs: List[Dict[str, Any]] = []

        for key, n_req in new_reqs.items():
            if key not in old_reqs:
                added_reqs.append(n_req)
            else:
                o_req = old_reqs[key]
                is_diff = (
                    o_req.get("value") != n_req.get("value")
                    or o_req.get("operator") != n_req.get("operator")
                    or o_req.get("unit") != n_req.get("unit")
                    or o_req.get("status") != n_req.get("status")
                )
                if is_diff:
                    modified_reqs.append({
                        "parameter": n_req.get("parameter"),
                        "clause": n_req.get("clause"),
                        "old_operator": o_req.get("operator"),
                        "old_value": o_req.get("value"),
                        "old_unit": o_req.get("unit"),
                        "old_status": o_req.get("status"),
                        "new_operator": n_req.get("operator"),
                        "new_value": n_req.get("value"),
                        "new_unit": n_req.get("unit"),
                        "new_status": n_req.get("status"),
                        "change_description": f"Limit changed from {o_req.get('operator', '')} {o_req.get('value')} {o_req.get('unit', '')} to {n_req.get('operator', '')} {n_req.get('value')} {n_req.get('unit', '')}",
                    })

        for key, o_req in old_reqs.items():
            if key not in new_reqs:
                removed_reqs.append(o_req)

        # 3. Compare Definitions (Clause 3)
        old_defs = {d.get("term", "").upper().strip(): d for d in old_norm_doc.get("definitions", [])}
        new_defs = {d.get("term", "").upper().strip(): d for d in new_norm_doc.get("definitions", [])}

        added_defs: List[Dict[str, Any]] = []
        removed_defs: List[Dict[str, Any]] = []
        modified_defs: List[Dict[str, Any]] = []

        for term, n_def in new_defs.items():
            if term not in old_defs:
                added_defs.append(n_def)
            else:
                o_def = old_defs[term]
                if o_def.get("definition", "").strip() != n_def.get("definition", "").strip():
                    modified_defs.append({
                        "term": n_def.get("term"),
                        "old_definition": o_def.get("definition"),
                        "new_definition": n_def.get("definition"),
                    })

        for term, o_def in old_defs.items():
            if term not in new_defs:
                removed_defs.append(o_def)

        # 4. Compare Entities
        old_ents = {e.get("name", "").upper().strip() + "@" + e.get("entity_type", ""): e for e in old_norm_doc.get("entities", [])}
        new_ents = {e.get("name", "").upper().strip() + "@" + e.get("entity_type", ""): e for e in new_norm_doc.get("entities", [])}

        added_ents = [e for k, e in new_ents.items() if k not in old_ents]
        removed_ents = [e for k, e in old_ents.items() if k not in new_ents]

        # 5. Compare Tables
        old_tables = {str(t.get("table_id", "")): t for t in old_norm_doc.get("tables", [])}
        new_tables = {str(t.get("table_id", "")): t for t in new_norm_doc.get("tables", [])}

        modified_tables: List[Dict[str, Any]] = []
        for t_id, n_tab in new_tables.items():
            if t_id in old_tables:
                o_tab = old_tables[t_id]
                o_rows = {r.get("cap", ""): r for r in o_tab.get("rows", []) if isinstance(r, dict)}
                n_rows = {r.get("cap", ""): r for r in n_tab.get("rows", []) if isinstance(r, dict)}

                changed_rows = []
                for cap, nr in n_rows.items():
                    if cap in o_rows:
                        orw = o_rows[cap]
                        if orw != nr:
                            changed_rows.append({"cap": cap, "old": orw, "new": nr})
                    else:
                        changed_rows.append({"cap": cap, "status": "new_row", "data": nr})

                if changed_rows:
                    modified_tables.append({
                        "table_id": t_id,
                        "title": n_tab.get("title"),
                        "changed_rows": changed_rows,
                    })

        # 6. Compare Cross-References
        old_refs = {r.get("target_standard", "") + "@" + str(r.get("source_clause", "")): r for r in old_norm_doc.get("cross_references", [])}
        new_refs = {r.get("target_standard", "") + "@" + str(r.get("source_clause", "")): r for r in new_norm_doc.get("cross_references", [])}

        added_refs = [r for k, r in new_refs.items() if k not in old_refs]
        removed_refs = [r for k, r in old_refs.items() if k not in new_refs]

        total_changes = (
            len(meta_changes)
            + len(added_reqs)
            + len(removed_reqs)
            + len(modified_reqs)
            + len(added_defs)
            + len(removed_defs)
            + len(modified_defs)
            + len(added_ents)
            + len(removed_ents)
            + len(modified_tables)
            + len(added_refs)
            + len(removed_refs)
        )

        return {
            "old_document_id": old_id,
            "new_document_id": new_id,
            "has_semantic_changes": total_changes > 0,
            "total_changes_count": total_changes,
            "metadata_diff": {
                "changes_count": len(meta_changes),
                "changes": meta_changes,
            },
            "requirements_diff": {
                "added_count": len(added_reqs),
                "removed_count": len(removed_reqs),
                "modified_count": len(modified_reqs),
                "added": added_reqs,
                "removed": removed_reqs,
                "modified": modified_reqs,
            },
            "definitions_diff": {
                "added_count": len(added_defs),
                "removed_count": len(removed_defs),
                "modified_count": len(modified_defs),
                "added": added_defs,
                "removed": removed_defs,
                "modified": modified_defs,
            },
            "entities_diff": {
                "added_count": len(added_ents),
                "removed_count": len(removed_ents),
                "added": added_ents,
                "removed": removed_ents,
            },
            "tables_diff": {
                "modified_count": len(modified_tables),
                "tables": modified_tables,
            },
            "references_diff": {
                "added_count": len(added_refs),
                "removed_count": len(removed_refs),
                "added": added_refs,
                "removed": removed_refs,
            },
        }

    def compare_files(self, old_norm_path: Path, new_norm_path: Path) -> Dict[str, Any]:
        with open(old_norm_path, "r", encoding="utf-8") as f:
            old_doc = json.load(f)
        with open(new_norm_path, "r", encoding="utf-8") as f:
            new_doc = json.load(f)
        return self.compare_documents(old_doc, new_doc)


def compare_normalized_documents(old_path: Path, new_path: Path) -> Dict[str, Any]:
    """Convenience helper function to compare two normalized JSON files."""
    engine = SemanticDiffEngine()
    return engine.compare_files(old_path, new_path)
