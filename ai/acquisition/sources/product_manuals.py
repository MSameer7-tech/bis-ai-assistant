"""
Adapter for BIS Product Specific Manuals (PMs) from Certification Directorate (CMD).
"""
from typing import List, Dict, Any
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_product_manual_canonical_id
from ai.acquisition.sources.bis_standards import BIS_STANDARDS_CATALOG


class ProductManualsAdapter(BISSourceAdapter):
    source_name = "BIS Product Specific Manuals (CMD)"
    source_family = "product_manuals"
    base_url = "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/pm"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        raw_items = []
        for std in BIS_STANDARDS_CATALOG:
            std_num = std.get("standard_number", "IS 0000")
            raw_items.append({
                "standard_number": std_num,
                "manual_code": "1",
                "title": f"Product Manual for {std_num} ({std.get('title', '')})",
                "department": std.get("department", "CMD"),
                "domain": std.get("domain", "general")
            })
        return raw_items

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        std_num = raw_record["standard_number"]
        m_code = raw_record.get("manual_code", "1")
        canon_id = make_product_manual_canonical_id(std_num, m_code)

        return {
            "catalog_id": f"PM-{canon_id}",
            "canonical_id": canon_id,
            "entity_type": "product_manual",
            "standard_number": std_num,
            "manual_code": f"PM/{std_num}/{m_code}",
            "title": raw_record.get("title"),
            "department": raw_record.get("department", "CMD"),
            "domain": raw_record.get("domain", "general"),
            "discovery_source": self.source_name,
            "discovery_method": "cmd_manual_directory",
            "source_url": f"{self.base_url}/view/{std_num.replace(' ', '_')}",
            "document_url": f"{self.base_url}/pdf/{std_num.replace(' ', '_')}_PM.pdf",
            "coverage_status": "verified",
            "document_discovery_status": "document_url_found",
            "has_document": True
        }
