"""
API Interceptor Discovery Strategy for Interactive BIS Search Portals.
Uses Playwright network interception to observe XHR/fetch requests
(e.g., DataTables) and extracts structured data without fabricating DOM evidence.
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

logger = logging.getLogger(__name__)

class APIInterceptorStrategy(BaseDiscoveryStrategy):
    """Executes network interception to discover data from XHR/JSON APIs."""

    def __init__(self, timeout: float = 30.0, max_pages: int = 5):
        super().__init__(timeout, max_pages)

    def discover(self, source: Dict[str, Any]) -> Tuple[List[Any], DiscoveryMetrics]:
        from ai.acquisition.discovery_engine import CandidateDocument
        
        metrics = DiscoveryMetrics(
            source_id=source["source_id"],
            source_family_id=source.get("source_family_id", ""),
            access_method="API_INTERCEPTOR"
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

        candidates = []
        relationships = []

        total_records_reported = 0
        records_collected = 0
        pagination_complete = True
        api_endpoints_observed = set()
        
        # Enhanced tracking
        network_logs = []
        failed_requests = []
        js_errors = []
        page_load_metrics = {
            "requested_url": start_url,
            "redirect_chain": [],
            "final_url": "",
            "final_language": "",
            "http_status": None,
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context(user_agent=self.headers["User-Agent"])
            page = context.new_page()
            
            def handle_response(response):
                nonlocal total_records_reported, records_collected, pagination_complete
                
                # Check if JSON
                if "application/json" in response.headers.get("content-type", ""):
                    try:
                        url = response.url
                        
                        # Only process meaningful endpoints
                        if "metrics" in url or "tracking" in url:
                            return
                            
                        body = response.json()
                        api_endpoints_observed.add(url)
                        
                        network_logs.append({
                            "url": url,
                            "method": response.request.method,
                            "status": response.status,
                            "content_type": response.headers.get("content-type"),
                            "response_size": len(response.body()) if response.body() else 0,
                            "is_api": True
                        })
                        
                        # Detect total records
                        if isinstance(body, dict):
                            if "recordsTotal" in body: # DataTables format
                                total_records_reported = max(total_records_reported, body["recordsTotal"])
                            elif "totalElements" in body:
                                total_records_reported = max(total_records_reported, body["totalElements"])
                                
                            data_arr = []
                            if "data" in body and isinstance(body["data"], list):
                                data_arr = body["data"]
                            elif "content" in body and isinstance(body["content"], list):
                                data_arr = body["content"]
                            elif "list" in body and isinstance(body["list"], list):
                                data_arr = body["list"]
                            else:
                                # Maybe the body itself is a list
                                pass
                                
                            records_to_process = data_arr if data_arr else []
                            if isinstance(body, list):
                                records_to_process = body
                                
                            std_num_pattern = re.compile(
                                r"IS\s*([0-9]+)(?:\s*[:\(]\s*(?:Part|Pt\.?)\s*([0-9]+)\s*[\):])?(?:\s*[:\-–]\s*([0-9]{4}))?",
                                re.IGNORECASE
                            )
                            
                            for item in records_to_process:
                                item_str = json.dumps(item)
                                std_match = std_num_pattern.search(item_str)
                                
                                # Try to extract product name from common fields
                                prod_name = item.get("product_name", item.get("productName", item.get("name", "")))
                                if not prod_name and isinstance(item, list) and len(item) > 1:
                                    # DataTables array of arrays
                                    prod_name = str(item[1])
                                
                                if std_match:
                                    std_no = std_match.group(1)
                                    part = std_match.group(2)
                                    year = int(std_match.group(3)) if std_match.group(3) else None
                                    
                                    # Clean up product name from HTML
                                    prod_name = re.sub(r"<[^>]+>", " ", str(prod_name)).strip()
                                    
                                    records_collected += 1
                                    
                                    relationships.append({
                                        "product_name": prod_name,
                                        "standard_number": std_no,
                                        "source_id": source["source_id"],
                                        "source_url": url,
                                        "relationship_type": "PRODUCT_TO_CERTIFICATION" if source["source_id"] == "SRC-005" else "PRODUCT_TO_STANDARD",
                                        "discovery_method": "NETWORK_INTERCEPTION",
                                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                                        "evidence": {
                                            "extraction_strategy": "NETWORK_INTERCEPTION",
                                            "source_api_url": url,
                                            "http_status": response.status
                                        }
                                    })
                                    metrics.records_discovered += 1

                    except Exception as e:
                        logger.debug(f"Failed to parse JSON response from {response.url}: {e}")

            page.on("response", handle_response)
            page.on("requestfailed", lambda req: failed_requests.append(req.url))
            page.on("pageerror", lambda err: js_errors.append(err.message))
            
            try:
                response = page.goto(start_url, wait_until="commit", timeout=int(self.timeout * 1000))
                metrics.pages_visited += 1
                
                if response:
                    page_load_metrics["http_status"] = response.status
                    req = response.request
                    redirects = []
                    while req.redirected_from:
                        req = req.redirected_from
                        redirects.append(req.url)
                    redirects.reverse()
                    page_load_metrics["redirect_chain"] = redirects

                page_load_metrics["final_url"] = page.url
                page_load_metrics["final_language"] = page.evaluate("document.documentElement.lang || ''")

                # Check for WAF/Session block
                page_text = page.content().lower()
                if "access denied" in page_text or "waf" in page_text or "session expired" in page_text:
                    metrics.source_errors.append("SESSION_REQUIRED")
                else:
                    # Give it a bit more time to make background requests
                    page.wait_for_timeout(10000)
                    
                    # Determine zero-record safety
                    if len(api_endpoints_observed) == 0:
                        metrics.source_errors.append("DISCOVERY_FAILED: No API/XHR request observed")
                        pagination_complete = False
                        
                    # Try to click "Next" in DataTables if exists
                    next_btn = page.locator('.paginate_button.next:not(.disabled), button.next:not([disabled])')
                    pages_clicked = 0
                    while next_btn.count() > 0 and next_btn.first.is_visible() and pages_clicked < self.max_pages:
                        try:
                            next_btn.first.click()
                            page.wait_for_timeout(2000) # Wait for network
                            pages_clicked += 1
                            next_btn = page.locator('.paginate_button.next:not(.disabled), button.next:not([disabled])')
                        except Exception:
                            break
                            
                    if total_records_reported > 0 and records_collected < total_records_reported:
                        pagination_complete = False
                        metrics.pagination_exhausted = False
                        metrics.pagination_status = "INCOMPLETE"

            except Exception as e:
                logger.error(f"Error intercepting {start_url}: {e}")

            browser.close()

        metrics.end_time = datetime.now(timezone.utc).isoformat()
        
        # Attach relationships and metadata
        metrics.dom_metrics = {
            "relationships": relationships,
            "api_endpoints_observed": list(api_endpoints_observed),
            "total_records_reported": total_records_reported,
            "records_collected": records_collected,
            "pagination_complete": pagination_complete,
            "network_logs": network_logs,
            "failed_requests": failed_requests,
            "js_errors": js_errors,
            "page_load_metrics": page_load_metrics
        }
        
        return candidates, metrics
