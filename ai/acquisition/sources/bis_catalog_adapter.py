"""
BIS Catalog & Multi-Family Information Source Adapter.
Handles discovery across:
1. Standards (Published, Under Review, Drafts, Amendments)
2. Product Certification (Compulsory Schemes, Product Manuals, SITs)
3. Regulatory Material (QCOs, Gazette Notifications, Schemes)
4. Supporting Information (Technical Committees, Recognized Laboratories, Booklets)
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# BIS Official Portal Endpoints & Source Families
BIS_SOURCE_FAMILIES = {
    "STANDARDS_CATALOGUE": {
        "family": "standards",
        "name": "Catalogue of Indian Standards",
        "authority": "Bureau of Indian Standards",
        "base_url": "https://standardsbis.bsbedge.com",
        "search_endpoint": "https://standardsbis.bsbedge.com/bis_search/standards",
        "document_type": "standard",
        "description": "Authoritative portal for searching published and under-review Indian Standards across all technical departments."
    },
    "KNOW_YOUR_STANDARD": {
        "family": "standards",
        "name": "Know Your Standard (KYS)",
        "authority": "Bureau of Indian Standards",
        "base_url": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails",
        "search_endpoint": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/search",
        "document_type": "standard",
        "description": "One-stop portal linking standard PDFs, amendments, gazette notifications, SITs, licenses, and labs."
    },
    "COMPENDIUM_OF_STANDARDS": {
        "family": "standards",
        "name": "Compendium of Indian Standards",
        "authority": "Bureau of Indian Standards",
        "base_url": "https://bis.gov.in/standards/technical-department/compendium-of-indian-standards/",
        "search_endpoint": "https://bis.gov.in/wp-json/bis/v1/compendium",
        "document_type": "compendium",
        "description": "Sector-wise and title-wise compendium of Indian Standards across national industrial domains."
    },
    "PRODUCT_CERTIFICATION_COMPULSORY": {
        "family": "product_certification",
        "name": "Products under Compulsory Certification",
        "authority": "Bureau of Indian Standards",
        "base_url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/compulsory_products",
        "document_type": "regulatory_listing",
        "description": "Official listings of products covered under mandatory ISI mark certification and CRS registration."
    },
    "PRODUCT_MANUALS": {
        "family": "product_certification",
        "name": "Product Specific Manuals (PMs)",
        "authority": "Bureau of Indian Standards (CMD)",
        "base_url": "https://www.bis.gov.in/product-certification/product-manuals/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/product_manuals",
        "document_type": "product_manual",
        "description": "Technical manuals specifying scope, grouping guidelines, sample sizes, and testing requirements."
    },
    "SCHEME_OF_INSPECTION_AND_TESTING": {
        "family": "product_certification",
        "name": "Scheme of Inspection and Testing (SIT)",
        "authority": "Bureau of Indian Standards (CMD)",
        "base_url": "https://www.bis.gov.in/product-certification/scheme-of-inspection-and-testing/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/sit_documents",
        "document_type": "sit",
        "description": "Quality assurance and testing frequency schedules for licensees."
    },
    "QUALITY_CONTROL_ORDERS": {
        "family": "regulatory",
        "name": "Quality Control Orders (QCOs) & Gazette Notifications",
        "authority": "Line Ministries & BIS (Steel, MeitY, DPIIT, Heavy Industries, Chemicals, Consumer Affairs)",
        "base_url": "https://www.bis.gov.in/product-certification/qco-gazette-notifications/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/qcos",
        "document_type": "qco",
        "description": "Statutory orders enforcing mandatory BIS certification for specific product categories."
    },
    "LABORATORIES_DIRECTORY": {
        "family": "supporting_info",
        "name": "BIS & Recognized Laboratory Network",
        "authority": "Bureau of Indian Standards (LPPD)",
        "base_url": "https://www.bis.gov.in/laboratory-services/laboratory-network/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/laboratories",
        "document_type": "laboratory_directory",
        "description": "Central, regional, branch, and recognized private laboratories with test capabilities."
    },
    "TECHNICAL_COMMITTEES": {
        "family": "supporting_info",
        "name": "BIS Technical Departments & Sectional Committees",
        "authority": "Bureau of Indian Standards",
        "base_url": "https://www.bis.gov.in/standards/technical-department/",
        "search_endpoint": "https://www.bis.gov.in/wp-json/bis/v1/committees",
        "document_type": "committee_directory",
        "description": "Division Councils (Civil, Mechanical, Electrotechnical, Electronics & IT, Chemical, Food, Medical, Textile)."
    }
}

# Technical Departments mapping
TECHNICAL_DEPARTMENTS = {
    "CED": "Civil Engineering Department",
    "ETD": "Electrotechnical Department",
    "LITD": "Electronics and Information Technology Department",
    "CHD": "Chemical Department",
    "FAD": "Food and Agriculture Department",
    "MED": "Mechanical Engineering Department",
    "TXD": "Textiles Department",
    "MHD": "Medical Equipment and Hospital Planning Department",
    "MTD": "Metallurgical Engineering Department",
    "PRD": "Production and General Engineering Department",
    "SSD": "Service Sector Department",
    "WSD": "Water Resources Department"
}


class BISCatalogAdapter:
    """
    Adapter interfacing with official BIS source families to discover and enumerate
    the full universe of standards, amendments, manuals, QCOs, and SITs.
    """

    def __init__(self):
        self.discovered_sources: List[Dict[str, Any]] = []
        self.catalog_entities: List[Dict[str, Any]] = []

    def get_source_families(self) -> Dict[str, Dict[str, Any]]:
        """Returns the dictionary of all authoritative BIS source families."""
        return BIS_SOURCE_FAMILIES

    def get_technical_departments(self) -> Dict[str, str]:
        """Returns the mapping of BIS technical departments."""
        return TECHNICAL_DEPARTMENTS
