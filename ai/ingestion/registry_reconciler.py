"""
Phase 5D: Standards Catalog & Registry Reconciler.
Determines semantic meaning of detected changes:
- EDITION_CHANGE
- SUPERSEDES / SUPERSEDED_BY
- STATUS_CHANGE
- AMENDMENT_ADDED
- QCO_CHANGED
Preserves historical version trees in data/registry/standards_catalog.jsonl.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
CATALOG_FILE = REGISTRY_DIR / "standards_catalog.jsonl"


class RegistryReconciler:
    """
    Reconciles new or updated catalog items into versioned standards revision trees.
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CATALOG_FILE
        self.catalog_records: Dict[str, Dict[str, Any]] = {}
        self._load_catalog()

    def _load_catalog(self):
        if not self.catalog_path.exists():
            return
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    cid = item.get("catalog_id")
                    if cid:
                        self.catalog_records[cid] = item

    def reconcile_item(self, candidate_meta: Dict[str, Any], change_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconciles a candidate change and determines semantic relationship.
        """
        entity_type = candidate_meta.get("entity_type", "standard")
        std_num = candidate_meta.get("standard_number")
        new_edition = str(candidate_meta.get("edition", "2024"))
        
        reconciliation = {
            "catalog_id": candidate_meta.get("catalog_id"),
            "standard_number": std_num,
            "entity_type": entity_type,
            "semantic_change": "NO_CHANGE",
            "previous_edition": None,
            "superseded_record": None,
            "updated_catalog_record": None
        }

        # Check existing standards with same standard_number
        existing_editions = []
        for cid, record in self.catalog_records.items():
            if record.get("entity_type") == "standard" and record.get("standard_number") == std_num:
                existing_editions.append(record)

        if not existing_editions:
            reconciliation["semantic_change"] = "NEW_STANDARD_REGISTERED"
            new_record = dict(candidate_meta)
            new_record["status"] = "active"
            new_record["supersedes"] = None
            reconciliation["updated_catalog_record"] = new_record
            return reconciliation

        # Find if there is an existing record with different edition
        for old_rec in existing_editions:
            old_edition = str(old_rec.get("edition", ""))
            if old_edition != new_edition and old_rec.get("status") == "active":
                # Compare years
                try:
                    if int(new_edition) > int(old_edition):
                        reconciliation["semantic_change"] = "EDITION_CHANGE"
                        reconciliation["previous_edition"] = old_edition
                        
                        # Mark old record as superseded
                        old_rec["status"] = "superseded"
                        old_rec["superseded_by"] = f"{std_num}:{new_edition}"
                        reconciliation["superseded_record"] = old_rec

                        # Create new active record
                        new_record = dict(candidate_meta)
                        new_record["status"] = "active"
                        new_record["supersedes"] = f"{std_num}:{old_edition}"
                        reconciliation["updated_catalog_record"] = new_record
                        return reconciliation
                except ValueError:
                    pass

        # If amendment added
        if entity_type == "amendment":
            reconciliation["semantic_change"] = "AMENDMENT_ADDED"
            reconciliation["updated_catalog_record"] = dict(candidate_meta)
            return reconciliation

        # If QCO modified
        if entity_type == "qco":
            reconciliation["semantic_change"] = "QCO_CHANGED"
            reconciliation["updated_catalog_record"] = dict(candidate_meta)
            return reconciliation

        reconciliation["updated_catalog_record"] = dict(candidate_meta)
        return reconciliation

    def save_reconciled_catalog(self, output_path: Optional[Path] = None):
        """Saves current in-memory catalog records back to JSONL."""
        out_p = output_path or self.catalog_path
        with open(out_p, "w", encoding="utf-8") as f:
            for rec in self.catalog_records.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info(f"Saved reconciled catalog to: {out_p}")
