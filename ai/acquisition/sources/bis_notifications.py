"""
BIS Regulatory Notifications & QCO Adapter.
Discovers Quality Control Orders (QCOs), Gazette notifications, and mandatory implementation orders.
"""

import logging
from typing import Any, Dict, List, Optional

from ai.acquisition.crawler_models import DiscoveredStandard, DiscoveryDocumentType, normalize_standard_number
from ai.acquisition.sources.base import BaseSourceAdapter
from ai.taxonomy.validator import get_taxonomy_validator

logger = logging.getLogger(__name__)

# Authoritative BIS QCO & Gazette Notifications Catalog
BIS_NOTIFICATIONS_CATALOG: List[Dict[str, Any]] = [
    {
        "standard_number": "QCO-DPIIT-2023-FANS",
        "title": "Ceiling Fans (Quality Control) Order, 2023",
        "edition": "2023",
        "document_type": "qco",
        "domain": "electrical",
        "category": "fans",
        "product_type": "electric_ceiling_fans",
        "pub_date": "2023-08-09",
        "valid_from": "2024-01-01",
        "valid_until": None,
        "source_url": "https://bis.gov.in/qco/ceiling_fans_2023.pdf",
        "pdf_url": "https://bis.gov.in/qco/ceiling_fans_2023.pdf",
        "authority": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "content_summary": "Mandates compulsory BIS Standard Mark (ISI mark) under IS 374:2019 for all electric ceiling fans manufactured or sold in India.",
    },
    {
        "standard_number": "QCO-STEEL-2024-REBARS",
        "title": "Steel and Steel Products (Quality Control) Order, 2024",
        "edition": "2024",
        "document_type": "qco",
        "domain": "construction_civil",
        "category": "steel_metals",
        "product_type": "high_strength_deformed_steel_bars",
        "pub_date": "2024-06-15",
        "valid_from": "2024-09-01",
        "valid_until": None,
        "source_url": "https://steel.gov.in/qco/steel_products_2024.pdf",
        "pdf_url": "https://steel.gov.in/qco/steel_products_2024.pdf",
        "authority": "Ministry of Steel",
        "content_summary": "Enforces mandatory certification under IS 1786 : 2024 for high-strength deformed steel bars and wires for concrete reinforcement.",
    },
    {
        "standard_number": "QCO-FSSAI-2024-WATER",
        "title": "Food Safety and Standards (Packaging and Labelling of Drinking Water) Notification, 2024",
        "edition": "2024",
        "document_type": "gazette_notification",
        "domain": "food_agriculture",
        "category": "food_beverages",
        "product_type": "packaged_drinking_water",
        "pub_date": "2024-01-10",
        "valid_from": "2024-07-01",
        "valid_until": None,
        "source_url": "https://egazette.gov.in/water_packaging_2024.pdf",
        "pdf_url": "https://egazette.gov.in/water_packaging_2024.pdf",
        "authority": "Food Safety and Standards Authority of India (FSSAI) & BIS",
        "content_summary": "Mandatory dual ISI and FSSAI certification for all packaged drinking water under IS 14543.",
    },
]


class BISNotificationsAdapter(BaseSourceAdapter):
    """
    Adapter for discovering and fetching BIS regulatory orders, gazettes, and QCOs.
    """

    name: str = "bis_notifications"

    def __init__(self):
        self.validator = get_taxonomy_validator()
        self.valid_domains = set(self.validator.get_valid_domains())

    def _map_taxonomy_domain(self, domain_raw: Optional[str]) -> str:
        if not domain_raw:
            return "unknown"
        dom_clean = str(domain_raw).strip().lower()
        return dom_clean if dom_clean in self.valid_domains else "unknown"

    def discover(
        self,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[DiscoveredStandard]:
        target_domain = domain.strip().lower() if domain else None
        results: List[DiscoveredStandard] = []

        for record in BIS_NOTIFICATIONS_CATALOG:
            mapped_domain = self._map_taxonomy_domain(record.get("domain"))
            if target_domain and mapped_domain != target_domain:
                continue

            doc_type_str = record.get("document_type", "qco")
            doc_type = DiscoveryDocumentType.QCO if doc_type_str == "qco" else DiscoveryDocumentType.GAZETTE_NOTIFICATION

            try:
                item = DiscoveredStandard(
                    standard_number=record["standard_number"],
                    title=record["title"],
                    edition=record.get("edition"),
                    document_type=doc_type,
                    domain=mapped_domain,
                    category=record.get("category"),
                    product_type=record.get("product_type"),
                    source_url=record["source_url"],
                    pdf_url=record.get("pdf_url"),
                    authority=record.get("authority", "Government of India / BIS"),
                    pub_date=record.get("pub_date"),
                    valid_from=record.get("valid_from"),
                    valid_until=record.get("valid_until"),
                    content_summary=record.get("content_summary"),
                )
                results.append(item)
            except Exception as e:
                logger.warning("Skipping invalid notification record %s: %s", record.get("standard_number"), e)

            if limit and len(results) >= limit:
                break

        return results

    def fetch_metadata(self, standard_number: str) -> Optional[DiscoveredStandard]:
        norm_code = standard_number.strip().lower().replace(" ", "")
        for record in BIS_NOTIFICATIONS_CATALOG:
            rec_code = record["standard_number"].strip().lower().replace(" ", "")
            if norm_code in rec_code or rec_code in norm_code:
                mapped_domain = self._map_taxonomy_domain(record.get("domain"))
                doc_type_str = record.get("document_type", "qco")
                doc_type = DiscoveryDocumentType.QCO if doc_type_str == "qco" else DiscoveryDocumentType.GAZETTE_NOTIFICATION
                return DiscoveredStandard(
                    standard_number=record["standard_number"],
                    title=record["title"],
                    edition=record.get("edition"),
                    document_type=doc_type,
                    domain=mapped_domain,
                    category=record.get("category"),
                    product_type=record.get("product_type"),
                    source_url=record["source_url"],
                    pdf_url=record.get("pdf_url"),
                    authority=record.get("authority", "Government of India / BIS"),
                    pub_date=record.get("pub_date"),
                    valid_from=record.get("valid_from"),
                    valid_until=record.get("valid_until"),
                    content_summary=record.get("content_summary"),
                )
        return None
