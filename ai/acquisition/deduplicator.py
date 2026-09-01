"""
Phase 6A: Cross-Source Entity Deduplication & Provenance Aggregator.
Deduplicates records across the 9 BIS source adapters using deterministic keys first,
merges source discovery citations, and calculates metadata completeness.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CrossSourceDeduplicator:
    """
    Deduplicates entities discovered across multiple BIS source families.
    """

    def __init__(self):
        self.entities: Dict[str, Dict[str, Any]] = {}

    def add_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        cid = record.get("canonical_id")
        if not cid:
            raise ValueError("Record missing required 'canonical_id'")

        if cid not in self.entities:
            # New entity
            entry = dict(record)
            src_name = record.get("discovery_source", "unknown")
            entry["discovery_sources"] = [src_name]
            entry["first_seen"] = record.get("first_seen", datetime.now().isoformat())
            entry["last_verified"] = datetime.now().isoformat()
            entry["metadata_completeness"] = self.compute_completeness(entry)
            self.entities[cid] = entry
            return entry
        else:
            # Existing entity: merge metadata
            existing = self.entities[cid]
            src_name = record.get("discovery_source", "unknown")
            if src_name not in existing.get("discovery_sources", []):
                existing.setdefault("discovery_sources", []).append(src_name)

            # Fill in missing fields
            for k, v in record.items():
                if v is not None and (k not in existing or existing[k] is None):
                    existing[k] = v

            existing["last_verified"] = datetime.now().isoformat()
            existing["metadata_completeness"] = self.compute_completeness(existing)
            return existing

    def compute_completeness(self, record: Dict[str, Any]) -> float:
        """Calculates completeness score across expected fields."""
        entity_type = record.get("entity_type", "standard")
        if entity_type == "standard":
            fields = ["standard_number", "title", "edition", "department", "committee_code", "status", "source_url"]
        elif entity_type == "amendment":
            fields = ["standard_number", "edition", "amendment_number", "title", "source_url"]
        elif entity_type in ["product_manual", "sit"]:
            fields = ["standard_number", "title", "source_url"]
        elif entity_type == "qco":
            fields = ["title", "ministry", "enforcement_date", "statutory_scheme"]
        else:
            fields = ["title", "source_url"]

        present = sum(1 for f in fields if record.get(f) is not None and str(record.get(f)).strip() != "")
        return round(present / len(fields), 2)

    def deduplicate_all(self, record_batches: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Deduplicates multiple batches of records from different adapters."""
        for batch in record_batches:
            for rec in batch:
                self.add_record(rec)
        return list(self.entities.values())
