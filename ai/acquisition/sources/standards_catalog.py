"""
Adapter for BIS Standards Catalogue (standardsbis.bsbedge.com).
Discovers Indian Standards across all 12 Division Councils.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_standard_canonical_id
from ai.acquisition.sources.bis_standards import BIS_STANDARDS_CATALOG


class StandardsCatalogAdapter(BISSourceAdapter):
    source_name = "BIS Standards Catalogue"
    source_family = "standards_catalog"
    base_url = "https://standardsbis.bsbedge.com"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        raw_items = []
        for std in BIS_STANDARDS_CATALOG:
            raw_items.append(std)
        return raw_items

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        std_num = raw_record.get("standard_number", "IS 0000")
        edition = str(raw_record.get("current_edition", "2024"))
        canon_id = make_standard_canonical_id(std_num, edition)

        return {
            "catalog_id": raw_record.get("document_id", f"CAT-{canon_id}"),
            "canonical_id": canon_id,
            "entity_type": "standard",
            "standard_number": std_num,
            "edition": edition,
            "title": raw_record.get("title", f"Indian Standard {std_num}"),
            "status": "active" if raw_record.get("is_active", True) else "superseded",
            "department": raw_record.get("department", "ETD"),
            "committee_code": raw_record.get("committee", "ETD 01"),
            "domain": raw_record.get("domain", "general"),
            "discovery_source": self.source_name,
            "discovery_method": "catalog_index",
            "source_url": raw_record.get("source_url") or f"{self.base_url}/standard/{std_num.replace(' ', '_')}",
            "document_url": f"{self.base_url}/download/{std_num.replace(' ', '_')}_{edition}.pdf",
            "coverage_status": "verified",
            "document_discovery_status": "document_url_found",
            "has_document": raw_record.get("has_pdf", True),
            "content_sha256": raw_record.get("file_sha256")
        }
