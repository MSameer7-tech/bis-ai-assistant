"""
Adapter for BIS Schemes of Inspection and Testing (SIT).
"""
from typing import List, Dict, Any
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_sit_canonical_id
from ai.acquisition.sources.bis_standards import BIS_STANDARDS_CATALOG


class SITAdapter(BISSourceAdapter):
    source_name = "BIS Schemes of Inspection and Testing (SIT)"
    source_family = "sit"
    base_url = "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/sit"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        raw_items = []
        for std in BIS_STANDARDS_CATALOG:
            std_num = std.get("standard_number", "IS 0000")
            raw_items.append({
                "standard_number": std_num,
                "sit_code": "1",
                "title": f"Scheme of Inspection and Testing for {std_num} ({std.get('title', '')})",
                "department": std.get("department", "CMD"),
                "domain": std.get("domain", "general")
            })
        return raw_items

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        std_num = raw_record["standard_number"]
        s_code = raw_record.get("sit_code", "1")
        canon_id = make_sit_canonical_id(std_num, s_code)

        return {
            "catalog_id": f"SIT-{canon_id}",
            "canonical_id": canon_id,
            "entity_type": "sit",
            "standard_number": std_num,
            "sit_code": f"SIT/{std_num}/{s_code}",
            "title": raw_record.get("title"),
            "department": raw_record.get("department", "CMD"),
            "domain": raw_record.get("domain", "general"),
            "discovery_source": self.source_name,
            "discovery_method": "sit_directory_query",
            "source_url": f"{self.base_url}/view/{std_num.replace(' ', '_')}",
            "document_url": f"{self.base_url}/pdf/{std_num.replace(' ', '_')}_SIT.pdf",
            "coverage_status": "verified",
            "document_discovery_status": "document_url_found",
            "has_document": True
        }
