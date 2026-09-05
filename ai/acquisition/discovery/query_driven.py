"""
Query-Driven Discovery Strategy for Interactive BIS Search Portals.
Executes programmatic search queries based on known vocabulary (e.g. product catalogs)
against interactive portals like SRC-001 (Know Your Standard).
"""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from playwright.sync_api import sync_playwright

from ai.acquisition.discovery.base import BaseDiscoveryStrategy, DiscoveryMetrics
from ai.acquisition.discovery.dom_analyzer import DOMDiscoveryEvidence

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PRODUCT_CATALOG_PATH = ROOT_DIR / "data/product_catalog.json"

class QueryDrivenStrategy(BaseDiscoveryStrategy):
    """Executes query-driven discovery against BIS search portals."""

    def __init__(self, timeout: float = 30.0, max_pages: int = 5):
        super().__init__(timeout, max_pages)

    def load_query_vocabulary(self) -> List[str]:
        """Loads product/domain names to be used as search queries."""
        queries = []
        if PRODUCT_CATALOG_PATH.exists():
            with open(PRODUCT_CATALOG_PATH, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for item in data:
                        if "name" in item:
                            queries.append(item["name"])
                        if "aliases" in item:
                            queries.extend(item["aliases"])
                except Exception as e:
                    logger.error(f"Error parsing product catalog: {e}")
        
        # Deduplicate and normalize
        return list(set(q.strip() for q in queries if q.strip()))

    def discover(self, source: Dict[str, Any]) -> Tuple[List[Any], DiscoveryMetrics]:
        from ai.acquisition.discovery_engine import CandidateDocument
        
        metrics = DiscoveryMetrics(
            source_id=source["source_id"],
            source_family_id=source.get("source_family_id", ""),
            access_method="QUERY_DRIVEN"
        )
        
        start_url = source.get("canonical_url", "")
        preferred_lang = source.get("preferred_language")
        
        # Safely append ?lang=en if needed
        if preferred_lang == "en":
            parsed = urlparse(start_url)
            query_dict = parse_qs(parsed.query)
            query_dict["lang"] = [preferred_lang]
            new_query = urlencode(query_dict, doseq=True)
            start_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

        queries = self.load_query_vocabulary()
        if not queries:
            metrics.source_errors.append("No queries found in vocabulary")
            return [], metrics

        candidates = []
        relationships = []
        
        # We will record these outside the loop to represent the page load state
        page_load_metrics = {
            "requested_url": start_url,
            "redirect_chain": [],
            "final_url": "",
            "final_language": "",
            "http_status": None,
            "search_control_found": False,
            "search_locator_strategy": "",
            "search_control_tag": "",
            "search_control_attributes": {}
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context(user_agent=self.headers["User-Agent"])
            page = context.new_page()

            for query in queries:
                try:
                    # Navigate to portal
                    response = page.goto(start_url, wait_until="commit", timeout=int(self.timeout * 1000))
                    
                    if response:
                        page_load_metrics["http_status"] = response.status
                        
                        # Trace redirects
                        req = response.request
                        redirects = []
                        while req.redirected_from:
                            req = req.redirected_from
                            redirects.append(req.url)
                        redirects.reverse() # Start to end
                        page_load_metrics["redirect_chain"] = redirects
                        
                    # Give scripts a moment to attach
                    page.wait_for_timeout(8000)
                    metrics.pages_visited += 1
                    
                    page_load_metrics["final_url"] = page.url
                    page_load_metrics["final_language"] = page.evaluate("document.documentElement.lang || ''")

                    # Identify search control (semantic fallback priority)
                    search_input = None
                    strategy_used = ""
                    
                    semantic_selectors = [
                        ('input[type="search"]', 'type="search"'),
                        ('input[role="searchbox"]', 'role="searchbox"'),
                        ('[role="search"] input', 'inside [role="search"]'),
                        ('input[aria-label*="search"]', 'aria-label containing search'),
                        ('input[aria-label*="Search"]', 'aria-label containing Search'),
                        ('input[placeholder*="search"]', 'placeholder containing search'),
                        ('input[placeholder*="Search"]', 'placeholder containing Search'),
                        ('input[aria-label*="खोजें"]', 'hindi aria-label "खोजें"'),
                        ('input[placeholder*="खोजें"]', 'hindi placeholder "खोजें"'),
                        ('input#edit-keywords', 'id edit-keywords'),
                        ('input.form-autocomplete', 'autocomplete input'),
                        ('form input[type="text"]', 'fallback primary form text input')
                    ]
                    
                    for sel, strat in semantic_selectors:
                        try:
                            loc = page.locator(sel)
                            if loc.count() > 0:
                                for i in range(loc.count()):
                                    if loc.nth(i).is_visible():
                                        search_input = loc.nth(i)
                                        strategy_used = strat
                                        break
                                if search_input:
                                    break
                        except Exception:
                            continue
                    
                    if search_input:
                        page_load_metrics["search_control_found"] = True
                        page_load_metrics["search_locator_strategy"] = strategy_used
                        page_load_metrics["search_control_tag"] = search_input.evaluate("el => el.tagName")
                        
                        # Get a few useful attributes to log
                        attrs = search_input.evaluate("el => Array.from(el.attributes).map(a => [a.name, a.value])")
                        page_load_metrics["search_control_attributes"] = {k: v for k, v in attrs if k in ['id', 'name', 'type', 'placeholder', 'class']}
                    
                    if not search_input:
                        metrics.source_errors.append("DISCOVERY_CONFIGURATION_REQUIRED: Search control not found")
                        continue

                    # Execute search
                    search_input.fill(query)
                    
                    # Try to find a submit button or press Enter
                    submit_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Search")').first
                    if submit_button.count() > 0 and submit_button.is_visible():
                        submit_button.click()
                    else:
                        search_input.press("Enter")
                        
                    # Wait for results or timeout
                    try:
                        page.wait_for_selector('table, .results, .no-records', timeout=10000)
                    except Exception:
                        pass # Ignore timeout, try parsing whatever loaded
                        
                    # Check for WAF/Session block
                    page_text = page.content().lower()
                    if "access denied" in page_text or "waf" in page_text or "session expired" in page_text:
                        metrics.source_errors.append("SESSION_REQUIRED")
                        break
                        
                    # Extract records
                    std_num_pattern = re.compile(
                        r"IS\s*([0-9]+)(?:\s*[:\(]\s*(?:Part|Pt\.?)\s*([0-9]+)\s*[\):])?(?:\s*[:\-–]\s*([0-9]{4}))?",
                        re.IGNORECASE
                    )
                    
                    rows = page.locator('tr').all()
                    if rows:
                        for row in rows:
                            row_text = row.inner_text()
                            links = row.locator('a[href]').all()
                            
                            std_match = std_num_pattern.search(row_text)
                            if std_match:
                                std_no = std_match.group(1)
                                part = std_match.group(2)
                                year = int(std_match.group(3)) if std_match.group(3) else None
                                
                                std_str = f"IS {std_no}"
                                if part: std_str += f" (Part {part})"
                                if year: std_str += f":{year}"
                                
                                # Find document URL if any
                                doc_url = ""
                                title = std_str
                                for link in links:
                                    href = link.get_attribute("href")
                                    link_text = link.inner_text()
                                    if href and "javascript" not in href:
                                        # Basic URL join logic since urljoin is removed from imports above
                                        if href.startswith("http"):
                                            doc_url = href
                                        elif href.startswith("/"):
                                            p = urlparse(start_url)
                                            doc_url = f"{p.scheme}://{p.netloc}{href}"
                                        else:
                                            doc_url = f"{start_url.rstrip('/')}/{href}"
                                            
                                        if len(link_text) > 10 and not std_num_pattern.search(link_text):
                                            title = link_text.strip()
                                
                                # Record relationship explicitly
                                relationships.append({
                                    "product_name": query,
                                    "standard_number": std_no,
                                    "standard_title": title,
                                    "source_id": source["source_id"],
                                    "source_url": start_url,
                                    "relationship_type": "PRODUCT_TO_STANDARD",
                                    "document_url": doc_url,
                                    "discovery_method": "QUERY_DRIVEN",
                                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                                })
                                metrics.records_discovered += 1
                                
                                # Create candidate if document URL exists
                                if doc_url:
                                    evidence = DOMDiscoveryEvidence(
                                        source_page_url=start_url,
                                        discovered_url=doc_url,
                                        element_tag="a",
                                        extraction_strategy="QUERY_DRIVEN_DOM",
                                        discovery_reason=f"query_match_for_{query}"
                                    )
                                    
                                    cand = CandidateDocument(
                                        candidate_id=f"CAND-IS-{std_no}-{year or '0000'}",
                                        source_id=source["source_id"],
                                        source_family_id=source.get("source_family_id", ""),
                                        source_url=doc_url,
                                        discovered_from_url=start_url,
                                        document_type="INDIAN_STANDARD",
                                        title=title,
                                        standard_number=std_no,
                                        part=part,
                                        edition_year=year,
                                        discovery_method="QUERY_DRIVEN",
                                        associated_product_keywords=[query],
                                        discovery_evidence=evidence.to_dict()
                                    )
                                    candidates.append(cand)
                                    metrics.documents_discovered += 1

                except Exception as e:
                    logger.error(f"Error querying {query} on {start_url}: {e}")

            browser.close()

        metrics.end_time = datetime.now(timezone.utc).isoformat()
        
        # We attach relationships to metrics so the engine can persist them separately
        metrics.dom_metrics = {
            "relationships": relationships,
            "page_load_metrics": page_load_metrics
        }
        
        return candidates, metrics
