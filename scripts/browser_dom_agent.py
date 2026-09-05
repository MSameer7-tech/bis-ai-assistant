"""
Autonomous Browser DOM Agent for Official BIS Portals (Phase 3).
Launches Google Chrome via Playwright, navigates live government websites,
executes in-browser JavaScript DOM extraction across all 6 targets, captures screenshots,
and saves the raw URL inventory before classification into data/candidates/browser_live_inventory.json.
"""
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, Browser, Page

from ai.acquisition.discovery.dom_analyzer import DOMAnalyzer
from ai.acquisition.source_gate import AUTHORIZED_GOV_DOMAINS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BrowserDOMAgent")

SNAPSHOTS_DIR = Path("data/browser_snapshots")
RAW_INVENTORY_PATH = Path("data/candidates/browser_live_inventory.json")
REPORT_PATH = Path("data/candidates/browser_agent_dom_report.json")

NAVIGATION_TARGETS = [
    {
        "id": "SRC-008",
        "name": "BIS Product Certification Schemes Overview",
        "url": "https://www.bis.gov.in/product-certification/product-certification-overview/",
        "alt_urls": [
            "https://www.bis.gov.in/product-certification/product-certification-overview/?lang=en",
            "https://www.bis.gov.in/product-certification/product-certification-overview/?lang=hi"
        ],
        "category": "SCHEMES",
        "family_id": "SRCF-006",
        "description": "Standard Mark (ISI) licensing, simplified procedure, and certification guidelines"
    },
    {
        "id": "SRC-014",
        "name": "Hallmarking of Precious Metals & HUID Overview",
        "url": "https://www.bis.gov.in/hallmarking-overview/",
        "alt_urls": [
            "https://www.bis.gov.in/hallmarking-overview/?lang=en",
            "https://www.bis.gov.in/hallmarking-overview/?lang=hi"
        ],
        "category": "HALLMARKING",
        "family_id": "SRCF-009",
        "description": "Mandatory gold and silver hallmarking orders, 6-digit HUID guidelines, and assaying centres"
    },
    {
        "id": "SRC-013",
        "name": "BIS Recognized Testing Laboratories (LIMS)",
        "url": "https://lims.bis.gov.in/home/labs/",
        "alt_urls": [],
        "category": "LABORATORY_REGISTRY",
        "family_id": "SRCF-008",
        "description": "Multi-column directory of BIS-recognized commercial and national testing laboratories"
    },
    {
        "id": "SRC-012",
        "name": "BIS-Owned Regional & Branch Laboratories (LIMS)",
        "url": "https://lims.bis.gov.in/home/bis_labs/",
        "alt_urls": [],
        "category": "BIS_LABORATORIES",
        "family_id": "SRCF-008",
        "description": "Directory of central, regional, and branch laboratories owned directly by BIS"
    },
    {
        "id": "SRC-018",
        "name": "The BIS Act, Rules & Regulations Portal",
        "url": "https://www.bis.gov.in/the-bis-act-rules-regulations/",
        "alt_urls": [
            "https://www.bis.gov.in/the-bis-act-rules-regulations/?lang=en",
            "https://www.bis.gov.in/the-bis-act-rules-regulations/?lang=hi"
        ],
        "category": "STATUTORY",
        "family_id": "SRCF-012",
        "description": "Official legal and statutory framework governing Indian Standards and conformity assessment"
    },
    {
        "id": "SRC-016",
        "name": "BIS Care & Consumer Engagement",
        "url": "https://www.bis.gov.in/consumer-overview/",
        "alt_urls": [
            "https://www.bis.gov.in/consumer-overview/?lang=en",
            "https://www.bis.gov.in/consumer-overview/?lang=hi"
        ],
        "category": "CONSUMER_GUIDE",
        "family_id": "SRCF-010",
        "description": "Consumer verification guidelines, mobile app manual, and grievance portals"
    }
]


class BrowserDOMAgent:
    """Automates real browser navigation, DOM inspection, and structured inventory extraction."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        RAW_INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.analyzer = DOMAnalyzer(AUTHORIZED_GOV_DOMAINS)

    def extract_live_dom_inventory(self, page: Page, base_url: str) -> Dict[str, Any]:
        """Extracts complete raw element inventory directly from the rendered Chrome DOM context."""
        return page.evaluate("""() => {
            const findNearestHeading = (el) => {
                let curr = el;
                while (curr && curr !== document.body) {
                    let prev = curr.previousElementSibling;
                    while (prev) {
                        if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'CAPTION', 'LEGEND'].includes(prev.tagName)) {
                            return prev.innerText.trim();
                        }
                        const hInside = prev.querySelector('h1, h2, h3, h4, h5, h6, caption, legend');
                        if (hInside) return hInside.innerText.trim();
                        prev = prev.previousElementSibling;
                    }
                    curr = curr.parentElement;
                }
                const firstH = document.querySelector('h1, h2, h3');
                return firstH ? firstH.innerText.trim() : '';
            };

            const isInsideNavOrChrome = (el) => {
                let curr = el;
                while (curr && curr !== document.body) {
                    const tag = curr.tagName.toLowerCase();
                    const cls = (curr.className || '').toString().toLowerCase();
                    const id = (curr.id || '').toString().toLowerCase();

                    if (['header', 'nav', 'footer', 'aside'].includes(tag)) return { is_nav: true, region: tag.toUpperCase() };
                    if (/(\\b|_)(nav|navbar|menu|topmenu|mainmenu|headermenu|footer|site-footer|sidebar|aside|language|lang)(\\b|_)/.test(cls)) {
                        return { is_nav: true, region: 'NAV_CLASS_' + cls.substring(0, 20) };
                    }
                    if (/(\\b|_)(nav|navbar|menu|footer|sidebar|lang)/.test(id)) {
                        return { is_nav: true, region: 'NAV_ID_' + id.substring(0, 20) };
                    }
                    curr = curr.parentElement;
                }
                return { is_nav: false, region: 'MAIN_CONTENT' };
            };

            // 1. Enumerate all <a> elements
            const allAnchors = Array.from(document.querySelectorAll('a[href]'));
            const linksInventory = allAnchors.map((a, idx) => {
                const href = a.getAttribute('href') || '';
                const fullUrl = a.href || '';
                const text = (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ');
                const isPdf = fullUrl.toLowerCase().split('?')[0].endsWith('.pdf') || href.toLowerCase().split('?')[0].endsWith('.pdf');
                const isDoc = /\\.(docx?|xlsx?|pptx?|odt|csv|json)$/i.test(fullUrl.split('?')[0]);
                const navCheck = isInsideNavOrChrome(a);
                const heading = findNearestHeading(a);
                const parent = a.parentElement ? a.parentElement.tagName.toLowerCase() : 'unknown';
                const parentCls = a.parentElement ? (a.parentElement.className || '').toString() : '';
                const parentId = a.parentElement ? (a.parentElement.id || '').toString() : '';

                return {
                    link_index: idx,
                    raw_href: href,
                    full_url: fullUrl,
                    link_text: text,
                    is_pdf: isPdf,
                    is_document: isDoc,
                    is_nav_or_chrome: navCheck.is_nav,
                    detected_region: navCheck.region,
                    nearest_heading: heading,
                    container_tag: parent,
                    container_class: parentCls,
                    container_id: parentId
                };
            });

            // 2. Enumerate all <table> elements
            const allTables = Array.from(document.querySelectorAll('table'));
            const tablesInventory = allTables.map((t, idx) => {
                const caption = t.querySelector('caption') ? t.querySelector('caption').innerText.trim() : null;
                const headers = Array.from(t.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = Array.from(t.querySelectorAll('tbody tr, tr')).map(tr => {
                    return Array.from(tr.querySelectorAll('td, th')).map(td => {
                        const link = td.querySelector('a');
                        return {
                            text: td.innerText.trim().replace(/\\s+/g, ' '),
                            link_href: link ? link.href : null,
                            link_text: link ? link.innerText.trim() : null
                        };
                    });
                });
                return {
                    table_index: idx,
                    caption: caption,
                    headers: headers,
                    row_count: rows.length,
                    rows: rows
                };
            });

            // 3. Page Structure
            const h1s = Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim()).filter(Boolean);
            const h2s = Array.from(document.querySelectorAll('h2')).map(h => h.innerText.trim()).filter(Boolean);
            const forms = Array.from(document.querySelectorAll('form')).map(f => ({ action: f.action, method: f.method, id: f.id }));

            return {
                title: document.title,
                url: window.location.href,
                dom_elements_count: document.querySelectorAll('*').length,
                headings: { h1: h1s, h2: h2s },
                forms_count: forms.length,
                links_total: linksInventory.length,
                pdf_links_count: linksInventory.filter(l => l.is_pdf).length,
                doc_links_count: linksInventory.filter(l => l.is_document).length,
                nav_links_count: linksInventory.filter(l => l.is_nav_or_chrome).length,
                tables_count: tablesInventory.length,
                links_inventory: linksInventory,
                tables_inventory: tablesInventory
            };
        }""")

    def navigate_with_retry(self, page: Page, target: Dict[str, Any]) -> Tuple[bool, int, str, str]:
        """Tries primary and alternative URLs with robust load settling."""
        urls_to_try = [target["url"]] + target.get("alt_urls", [])

        for idx, u in enumerate(urls_to_try):
            try:
                print(f"    [*] Attempt {idx + 1}: Navigating to {u}")
                try:
                    resp = page.goto(u, wait_until="domcontentloaded", timeout=35000)
                except Exception:
                    resp = page.goto(u, wait_until="commit", timeout=35000)
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=25000)
                    except Exception:
                        pass

                page.wait_for_timeout(4000)
                status = resp.status if resp else 200
                final_url = page.url
                title = page.title()

                # Verify DOM rendered beyond basic shell
                node_count = page.evaluate("() => document.querySelectorAll('*').length")
                if node_count > 100:
                    return True, status, final_url, title
                else:
                    logger.warning(f"Page {u} rendered only {node_count} nodes, retrying alternate URL...")
            except Exception as e:
                logger.warning(f"Attempt failed for {u}: {e}")
                time.sleep(1)

        return False, 0, target["url"], "FAILED"

    def run_exploration(self) -> Dict[str, Any]:
        """Runs live Chrome browser session across all 6 targets and generates raw inventory."""
        print("\n" + "=" * 140)
        print("            LIVE PLAYWRIGHT CHROME BROWSER EXPLORATION & INVENTORY EXTRACTION")
        print("=" * 140)

        results = []
        raw_inventory_by_source = {}
        start_time = datetime.now(timezone.utc).isoformat()

        with sync_playwright() as p:
            print("[*] Launching Google Chrome browser engine (macOS ARM64)...")
            browser = p.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                locale="en-US"
            )
            page = context.new_page()

            for target in NAVIGATION_TARGETS:
                sid = target["id"]
                name = target["name"]
                cat = target["category"]
                fam = target["family_id"]

                print(f"\n[+] Processing Target: {sid} — {name}")

                success, status, final_url, title = self.navigate_with_retry(page, target)

                if not success:
                    print(f"    [-] Navigation failed across all attempts for {sid}")
                    results.append({
                        "source_id": sid,
                        "family_id": fam,
                        "name": name,
                        "target_url": target["url"],
                        "status": "FAILED",
                        "error": "Timeout / Network Unreachable"
                    })
                    continue

                # In-browser DOM extraction via JavaScript
                dom_data = self.extract_live_dom_inventory(page, final_url)

                # Capture Snapshot
                clean_id = sid.lower().replace("-", "_")
                screenshot_file = SNAPSHOTS_DIR / f"{clean_id}_screenshot.png"
                try:
                    page.screenshot(path=str(screenshot_file), full_page=False)
                    has_screenshot = True
                except Exception as ss_err:
                    logger.warning(f"Could not save snapshot: {ss_err}")
                    has_screenshot = False

                print(f"    [✓] HTTP {status} | Final URL: {final_url}")
                print(f"    [✓] Page Title: '{title}'")
                print(f"    [✓] Rendered DOM: {dom_data['dom_elements_count']} nodes | Headings: H1={len(dom_data['headings']['h1'])}, H2={len(dom_data['headings']['h2'])}")
                print(f"    [✓] Links In Inventory: {dom_data['links_total']} (PDFs: {dom_data['pdf_links_count']}, Docs: {dom_data['doc_links_count']}, Chrome/Nav: {dom_data['nav_links_count']})")
                print(f"    [✓] Tables Found: {dom_data['tables_count']}")
                if has_screenshot:
                    print(f"    [✓] Visual Snapshot: {screenshot_file}")

                raw_inventory_by_source[sid] = {
                    "source_id": sid,
                    "family_id": fam,
                    "source_name": name,
                    "category": cat,
                    "target_url": target["url"],
                    "final_url": final_url,
                    "page_title": title,
                    "status_code": status,
                    "screenshot_path": str(screenshot_file) if has_screenshot else None,
                    "dom_stats": {
                        "dom_elements_count": dom_data["dom_elements_count"],
                        "links_total": dom_data["links_total"],
                        "pdf_links_count": dom_data["pdf_links_count"],
                        "doc_links_count": dom_data["doc_links_count"],
                        "nav_links_count": dom_data["nav_links_count"],
                        "tables_count": dom_data["tables_count"]
                    },
                    "headings": dom_data["headings"],
                    "links_inventory": dom_data["links_inventory"],
                    "tables_inventory": dom_data["tables_inventory"]
                }

                results.append(raw_inventory_by_source[sid])

            browser.close()

        # Save auditable raw inventory artifact
        with open(RAW_INVENTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(raw_inventory_by_source, f, indent=2)

        summary = {
            "agent": "PLAYWRIGHT_CHROME_BROWSER_DOM_AGENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "targets_navigated": len(NAVIGATION_TARGETS),
            "successful_targets": sum(1 for r in results if r.get("status_code") in [200, 302, 301, 304]),
            "raw_inventory_file": str(RAW_INVENTORY_PATH),
            "results": results
        }

        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 140)
        print("                  BROWSER DOM EXTRACTION COMPLETE")
        print("=" * 140)
        print(f"  • Successful Browser Targets: {summary['successful_targets']} / {len(NAVIGATION_TARGETS)}")
        print(f"  • Raw Inventory Saved:        {RAW_INVENTORY_PATH}")
        print(f"  • Snapshots Saved:            {SNAPSHOTS_DIR}\n")

        return raw_inventory_by_source


def main():
    agent = BrowserDOMAgent(headless=True)
    agent.run_exploration()


if __name__ == "__main__":
    main()
