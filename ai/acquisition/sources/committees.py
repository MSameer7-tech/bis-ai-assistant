"""
Adapter for BIS Technical Departments & Sectional Committees.
"""
from typing import List, Dict, Any
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_committee_canonical_id
from ai.acquisition.sources.bis_registry_data import COMMITTEE_DATABASE


class CommitteesAdapter(BISSourceAdapter):
    source_name = "BIS Technical Departments & Sectional Committees"
    source_family = "committees"
    base_url = "https://bis.gov.in/index.php/standards/technical-departments"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        return list(COMMITTEE_DATABASE)

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        c_id = raw_record.get("committee_id", "COMM-01")
        dept = raw_record.get("department_code", "ETD")
        c_num = raw_record.get("committee_code", "ETD 01")
        canon_id = make_committee_canonical_id(dept, c_num)

        return {
            "catalog_id": c_id,
            "canonical_id": canon_id,
            "entity_type": "committee",
            "department_code": dept,
            "committee_code": c_num,
            "title": raw_record.get("title"),
            "scope": raw_record.get("scope"),
            "discovery_source": self.source_name,
            "discovery_method": "directorate_hierarchy",
            "source_url": f"{self.base_url}/{dept.lower()}",
            "coverage_status": "verified",
            "has_document": False
        }
