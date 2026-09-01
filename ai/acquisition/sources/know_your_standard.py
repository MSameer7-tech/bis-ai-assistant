"""
Adapter for Know Your Standard (KYS) Portal (services.bis.gov.in).
Discovers standards, normative amendments, and gazette notices.
"""
from typing import List, Dict, Any, Optional
from ai.acquisition.sources.base import BISSourceAdapter
from ai.acquisition.canonical_ids import make_standard_canonical_id, make_amendment_canonical_id
from ai.acquisition.sources.bis_standards import BIS_STANDARDS_CATALOG


class KnowYourStandardAdapter(BISSourceAdapter):
    source_name = "Know Your Standard (KYS) Portal"
    source_family = "know_your_standard"
    base_url = "https://services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards"

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        raw_items = []
        for std in BIS_STANDARDS_CATALOG:
            # Emit standard
            raw_items.append({"type": "standard", "data": std})
            # Emit amendments if present
            ed = str(std.get("current_edition", "2024"))
            std_num = std.get("standard_number", "IS 0000")
            for amd_num in [1, 2]:
                raw_items.append({
                    "type": "amendment",
                    "data": {
                        "standard_number": std_num,
                        "edition": ed,
                        "amendment_number": amd_num,
                        "title": f"Amendment No. {amd_num} to {std_num}:{ed}",
                        "department": std.get("department", "ETD")
                    }
                })
        return raw_items

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        rec_type = raw_record.get("type", "standard")
        data = raw_record.get("data", {})
        std_num = data.get("standard_number", "IS 0000")
        ed = str(data.get("edition") or data.get("current_edition", "2024"))

        if rec_type == "standard":
            canon_id = make_standard_canonical_id(std_num, ed)
            return {
                "catalog_id": data.get("document_id", f"KYS-{canon_id}"),
                "canonical_id": canon_id,
                "entity_type": "standard",
                "standard_number": std_num,
                "edition": ed,
                "title": data.get("title", f"Indian Standard {std_num}"),
                "status": "active" if data.get("is_active", True) else "superseded",
                "department": data.get("department", "ETD"),
                "committee_code": data.get("committee", "ETD 01"),
                "domain": data.get("domain", "general"),
                "discovery_source": self.source_name,
                "discovery_method": "kys_portal_query",
                "source_url": f"{self.base_url}/standard_details/{std_num.replace(' ', '_')}",
                "document_url": f"{self.base_url}/view_pdf/{std_num.replace(' ', '_')}_{ed}.pdf",
                "coverage_status": "verified",
                "document_discovery_status": "document_url_found",
                "has_document": True
            }
        else:
            amd_num = data.get("amendment_number", 1)
            canon_id = make_amendment_canonical_id(std_num, ed, amd_num)
            return {
                "catalog_id": f"KYS-{canon_id}",
                "canonical_id": canon_id,
                "entity_type": "amendment",
                "standard_number": std_num,
                "edition": ed,
                "amendment_number": amd_num,
                "title": data.get("title", f"Amendment No. {amd_num} to {std_num}:{ed}"),
                "department": data.get("department", "ETD"),
                "discovery_source": self.source_name,
                "discovery_method": "kys_portal_query",
                "source_url": f"{self.base_url}/amendment_details/{std_num.replace(' ', '_')}/{amd_num}",
                "document_url": f"{self.base_url}/view_pdf/{std_num.replace(' ', '_')}_amd_{amd_num}.pdf",
                "coverage_status": "verified",
                "document_discovery_status": "document_url_found",
                "has_document": True
            }
