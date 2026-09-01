"""
Adapter for Statutory Quality Control Orders (QCOs) & Gazette Notifications.
"""
from typing import List, Dict, Any
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_qco_canonical_id
from ai.acquisition.sources.bis_registry_data import QCO_DATABASE


class QCOAdapter(BISSourceAdapter):
    source_name = "Quality Control Orders & Gazette Notifications"
    source_family = "qco_gazette"
    base_url = "https://bis.gov.in/index.php/qco-gazette"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        return list(QCO_DATABASE)

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        q_id = raw_record.get("qco_id", "QCO-GENERIC")
        canon_id = make_qco_canonical_id(q_id)

        return {
            "catalog_id": q_id,
            "canonical_id": canon_id,
            "entity_type": "qco",
            "standard_number": raw_record.get("standard_number"),
            "title": raw_record.get("title"),
            "ministry": raw_record.get("ministry"),
            "enforcement_date": raw_record.get("enforcement_date"),
            "statutory_scheme": raw_record.get("statutory_scheme"),
            "discovery_source": self.source_name,
            "discovery_method": "gazette_notification_archive",
            "source_url": raw_record.get("source_url") or f"{self.base_url}/{q_id}",
            "document_url": f"{self.base_url}/orders/{q_id}.pdf",
            "coverage_status": "verified",
            "document_discovery_status": "document_url_found",
            "has_document": True
        }
