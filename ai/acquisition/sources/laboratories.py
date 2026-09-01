"""
Adapter for BIS Central, Regional, Branch & NABL Testing Laboratories.
"""
from typing import List, Dict, Any
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_lab_canonical_id
from ai.acquisition.sources.bis_registry_data import LABORATORY_DATABASE


class LaboratoriesAdapter(BISSourceAdapter):
    source_name = "BIS & Recognized Laboratory Network"
    source_family = "laboratories"
    base_url = "https://bis.gov.in/index.php/laboratory-network"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        return list(LABORATORY_DATABASE)

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        l_id = raw_record.get("lab_id", "LAB-001")
        name = raw_record.get("name", "BIS Laboratory")
        loc = raw_record.get("location", "India")
        canon_id = make_lab_canonical_id(name, loc)

        return {
            "catalog_id": l_id,
            "canonical_id": canon_id,
            "entity_type": "laboratory",
            "title": name,
            "location": loc,
            "lab_type": raw_record.get("lab_type"),
            "capabilities": raw_record.get("capabilities"),
            "discovery_source": self.source_name,
            "discovery_method": "lppd_lab_directory",
            "source_url": f"{self.base_url}/{l_id}",
            "coverage_status": "verified",
            "has_document": False
        }
