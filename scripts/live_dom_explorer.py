"""
Live BIS DOM Explorer & Discovery Agent (Phase 3).
Directly navigates official BIS portals, analyzes live DOM hierarchies in real time,
isolates content regions from navigation boilerplate, and extracts live documents,
product manuals, laboratory registries, and statutory regulations.
"""
import json
import logging
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ai.acquisition.discovery.dom_analyzer import (
    DOMAnalyzer,
    DOMRecord,
    DOMDiscoveryEvidence,
    DOMAnalysisMetrics
)
from ai.acquisition.source_gate import AUTHORIZED_GOV_DOMAINS, is_domain_authorized

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LiveDOMExplorer")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Connection": "keep-alive",
}

EXPLORATION_TARGETS = [
    {
        "id": "BIS-HOME",
        "title": "BIS Official Homepage",
        "url": "https://www.bis.gov.in/",
        "category": "PORTAL_HOME"
    },
    {
        "id": "BIS-ACTS",
        "title": "BIS Act, Rules & Regulations",
        "url": "https://www.bis.gov.in/the-bis-act-rules-regulations/",
        "category": "STATUTORY"
    },
    {
        "id": "BIS-PROD-CERT",
        "title": "Product Certification Overview",
        "url": "https://www.bis.gov.in/product-certification/product-certification-overview/",
        "category": "CERTIFICATION"
    },
    {
        "id": "BIS-PROD-MANUALS",
        "title": "Product Specific Manuals & Guidelines",
        "url": "https://www.bis.gov.in/product-certification/product-specific-information-2/product-manuals/",
        "category": "MANUALS"
    },
    {
        "id": "BIS-SIT",
        "title": "Scheme of Inspection and Testing (SIT)",
        "url": "https://www.bis.gov.in/whats_new/scheme-of-inspection-and-testing-made-optional-for-micro-and-small-scale-manufacturers-of-consumer-footwear-and-footwear-components/",
        "category": "SIT_SCHEDULE"
    },
    {
        "id": "BIS-HALLMARKING",
        "title": "Hallmarking Overview & HUID Guidelines",
        "url": "https://www.bis.gov.in/hallmarking-overview/",
        "category": "HALLMARKING"
    },
    {
        "id": "BIS-LIMS-LABS",
        "title": "LIMS BIS Recognized Testing Laboratories",
        "url": "https://lims.bis.gov.in/home/labs/",
        "category": "LABORATORY_REGISTRY"
    },
    {
        "id": "BIS-LIMS-BIS-LABS",
        "title": "LIMS BIS-Owned Branch & Regional Laboratories",
        "url": "https://lims.bis.gov.in/home/bis_labs/",
        "category": "BIS_LABORATORIES"
    },
    {
        "id": "BIS-CONSUMER",
        "title": "Consumer Affairs & BIS Care Portal",
        "url": "https://www.bis.gov.in/consumer-overview/",
        "category": "CONSUMER_GUIDE"
    },
    {
        "id": "BIS-PUBLICATIONS",
        "title": "Publications, MSME Concessions & FAQs",
        "url": "https://www.bis.gov.in/publications/",
        "category": "PUBLICATIONS"
    },
]


class LiveDOMDiscoverySession:
    """Orchestrates live DOM exploration across official BIS portal endpoints."""

    def __init__(self):
        self.analyzer = DOMAnalyzer(AUTHORIZED_GOV_DOMAINS)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.report_dir = Path("data/candidates")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.report_file = self.report_dir / "live_dom_exploration_report.json"

    def fetch_live_page(self, url: str) -> Tuple[Optional[str], Optional[str], int, str]:
        """Fetches page with redirect following and robust error handling."""
        try:
            resp = self.session.get(url, timeout=12, allow_redirects=True, verify=True)
            final_url = resp.url
            status_code = resp.status_code
            if status_code == 200:
                return resp.text, final_url, status_code, ""
            return None, final_url, status_code, f"HTTP_{status_code}"
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None, url, 0, str(e)

    def explore_all(self) -> Dict[str, Any]:
        """Runs autonomous live DOM exploration across all target BIS portals."""
        print("\n" + "=" * 140)
        print("                         AUTONOMOUS LIVE BIS DOM EXPLORATION & DISCOVERY SESSION")
        print("=" * 140)

        results = []
        total_dom_elements = 0
        total_raw_links = 0
        total_nav_excluded = 0
        total_documents_found = 0
        total_structured_records = 0

        for target in EXPLORATION_TARGETS:
            tid = target["id"]
            title = target["title"]
            req_url = target["url"]
            cat = target["category"]

            print(f"\n[+] Navigating to: {title} ({req_url})")
            html, final_url, status, err = self.fetch_live_page(req_url)

            if not html:
                print(f"    [-] Request failed or redirected with error: {err} (HTTP {status})")
                results.append({
                    "target_id": tid,
                    "target_title": title,
                    "requested_url": req_url,
                    "final_url": final_url,
                    "status_code": status,
                    "error": err,
                    "metrics": None,
                    "discovered_records": []
                })
                continue

            records, metrics = self.analyzer.analyze_dom(html, final_url, tid, cat)

            # Analyze structural layout features
            soup = BeautifulSoup(html, "html.parser")
            h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)][:5]
            tables = soup.find_all("table")
            forms = soup.find_all("form")
            articles = soup.find_all(["article", "section", ".card", ".content"])

            total_dom_elements += metrics.raw_dom_elements
            total_raw_links += metrics.raw_links
            total_nav_excluded += (metrics.navigation_links_excluded + metrics.footer_links_excluded + metrics.sidebar_links_excluded + metrics.language_links_excluded)
            
            doc_count = sum(1 for r in records if r.url.endswith(".pdf") or "DOCUMENT" in r.document_type)
            struct_count = sum(1 for r in records if r.evidence and r.evidence.region_type == "TABLE_ROW")
            total_documents_found += doc_count
            total_structured_records += struct_count

            print(f"    [✓] HTTP {status} | Final URL: {final_url}")
            print(f"    [✓] DOM Elements: {metrics.raw_dom_elements} | Raw Links: {metrics.raw_links}")
            print(f"    [✓] Structural Content: Headings H1={len(h1_tags)}, H2={len(h2_tags)}, Tables={len(tables)}, Forms={len(forms)}")
            print(f"    [✓] Noise Filtered: Nav={metrics.navigation_links_excluded}, Footer={metrics.footer_links_excluded}, Lang={metrics.language_links_excluded}")
            print(f"    [✓] Valid Discovered Records: {len(records)} (Docs: {doc_count}, Structured Tables: {struct_count})")

            # Sample top records
            for idx, r in enumerate(records[:3]):
                h_info = f" [Heading: {r.evidence.nearest_heading[:40]}]" if r.evidence and r.evidence.nearest_heading else ""
                print(f"        • [{r.evidence.region_type if r.evidence else 'DOC'}] {r.title[:65]} -> {r.url[:70]}{h_info}")

            results.append({
                "target_id": tid,
                "target_title": title,
                "requested_url": req_url,
                "final_url": final_url,
                "status_code": status,
                "page_headings": {"h1": h1_tags, "h2": h2_tags},
                "metrics": metrics.to_dict(),
                "discovered_records": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "document_type": r.document_type,
                        "metadata": r.metadata,
                        "evidence": r.evidence.to_dict() if r.evidence else None
                    }
                    for r in records
                ]
            })

            time.sleep(0.5)

        summary = {
            "exploration_timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoints_explored": len(EXPLORATION_TARGETS),
            "successful_endpoints": sum(1 for r in results if r["status_code"] == 200),
            "total_dom_elements_inspected": total_dom_elements,
            "total_raw_links_parsed": total_raw_links,
            "total_boilerplate_excluded": total_nav_excluded,
            "total_documents_discovered": total_documents_found,
            "total_structured_records_discovered": total_structured_records,
            "results": results
        }

        with open(self.report_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 140)
        print("                                LIVE DOM DISCOVERY SUMMARY")
        print("=" * 140)
        print(f"  • Endpoints Visited:              {len(EXPLORATION_TARGETS)} ({summary['successful_endpoints']} live 200 OK)")
        print(f"  • Total DOM Nodes Inspected:       {total_dom_elements:,}")
        print(f"  • Total Anchor Links Analyzed:     {total_raw_links:,}")
        print(f"  • Boilerplate Chrome Excluded:     {total_nav_excluded:,}")
        print(f"  • Discovered Documents & Assets:   {total_documents_found}")
        print(f"  • Structured Laboratory Records:   {total_structured_records}")
        print(f"  • Live Report Saved To:           {self.report_file}\n")
        print("=" * 140)

        return summary


def main():
    session = LiveDOMDiscoverySession()
    session.explore_all()


if __name__ == "__main__":
    main()
