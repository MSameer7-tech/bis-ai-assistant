import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Standard headers for generic HTTP discovery
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def generate_sha256(content: bytes) -> str:
    """Generate SHA-256 hash of byte content."""
    return hashlib.sha256(content).hexdigest()

def is_bis_domain(url: str) -> bool:
    """Validate if URL belongs to authoritative BIS domains."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.endswith("bis.gov.in")
    except Exception:
        return False

def extract_tables_from_html(soup: BeautifulSoup) -> List[List[Dict[str, str]]]:
    """
    Generic HTML table extractor.
    Returns a list of tables. Each table is a list of rows.
    Each row is a dict of header_name -> cell_text.
    """
    tables_data = []
    
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
            
        # Try to find headers in the first row(s) or standard thead
        headers = []
        header_row_idx = 0
        
        # Look for th elements first
        for idx, row in enumerate(rows):
            th_cells = row.find_all(["th"])
            if th_cells:
                headers = [re.sub(r'\s+', ' ', th.get_text(separator=" ", strip=True)).strip() for th in th_cells]
                header_row_idx = idx
                break
                
        # If no th, assume the first row with td might be headers
        if not headers and rows:
            td_cells = rows[0].find_all(["td"])
            headers = [re.sub(r'\s+', ' ', td.get_text(separator=" ", strip=True)).strip() for td in td_cells]
            header_row_idx = 0
            
        # Fallback for empty/unnamed headers
        headers = [h if h else f"Column_{i}" for i, h in enumerate(headers)]
        
        # Make headers unique if there are duplicates (e.g. "Product", "Product")
        seen = {}
        unique_headers = []
        for h in headers:
            h_lower = h.lower()
            if h_lower in seen:
                seen[h_lower] += 1
                unique_headers.append(f"{h}_{seen[h_lower]}")
            else:
                seen[h_lower] = 1
                unique_headers.append(h)
        headers = unique_headers
        
        table_rows = []
        for idx, row in enumerate(rows):
            if idx <= header_row_idx:
                continue # Skip header row
                
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
                
            row_data = {}
            for i, cell in enumerate(cells):
                # Clean up text (replace newlines with spaces, strip whitespace)
                text = re.sub(r'\s+', ' ', cell.get_text(separator=" ", strip=True)).strip()
                if i < len(headers):
                    row_data[headers[i]] = text
                else:
                    row_data[f"Extra_Column_{i}"] = text
                    
            # Preserve raw HTML for provenance
            row_data["_raw_html"] = str(row).strip()
            table_rows.append(row_data)
            
        if table_rows:
            tables_data.append(table_rows)
            
    return tables_data


def detect_completeness(soup: BeautifulSoup, tables_count: int, rows_count: int) -> str:
    """
    Detect whether the page is a complete static HTML catalog or paginated/API-driven.
    """
    if tables_count == 0:
        return "EMPTY"
        
    text_content = soup.get_text().lower()
    
    # Check for pagination elements
    # Common pagination classes/ids
    pagination_elements = soup.find_all(class_=re.compile(r'paginat|nav-links|page-numbers', re.IGNORECASE))
    if pagination_elements:
        return "PAGINATED"
        
    # Check for DataTables/AJAX references inside scripts
    for script in soup.find_all("script"):
        if script.string and re.search(r'(datatables|ajax|fetch\()', script.string, re.IGNORECASE):
            return "DYNAMIC_API_REQUIRED"
            
    # Check for obvious Next/Prev links that aren't just generic
    next_links = soup.find_all("a", string=re.compile(r'^\s*(Next|>>|Older|Previous|<<)\s*$', re.IGNORECASE))
    if next_links:
        return "PAGINATED"
        
    # If there is a massive number of rows and no pagination, it's likely complete
    # "do not use row count as the sole completeness criterion" - done, we checked structural pagination markers above
    return "COMPLETE_STATIC_HTML"


class HTTPCatalogDiscovery:
    """Discovers schemes and product tables via standard HTTP requests."""
    
    def discover_schemes(self, landing_url: str) -> List[Dict[str, Any]]:
        """Phase 8.6A: Discover scheme links from the landing page."""
        logger.info(f"Fetching landing page: {landing_url}")
        
        try:
            resp = requests.get(landing_url, headers=HTTP_HEADERS, verify=False, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {landing_url}: {e}")
            return []
            
        if not is_bis_domain(resp.url):
            logger.error("Landing page redirected outside authorized BIS domain.")
            return []
            
        content_hash = generate_sha256(resp.content)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        discovered = []
        seen_urls = set()
        
        # Find semantic container (e.g. productsCC div or ul lists)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href == "#" or href.startswith("javascript:"):
                continue
                
            full_url = urljoin(resp.url, href)
            # Standardize URL to avoid duplicates with/without trailing slashes or lang params
            # Actually, keep the lang param if present.
            if full_url in seen_urls:
                continue
                
            if not is_bis_domain(full_url):
                continue
                
            text = a_tag.get_text(separator=" ", strip=True)
            
            # Semantic keyword matching for Scheme pages
            # E.g., Scheme-I, Scheme II, Registration Scheme, Scheme X
            if re.search(r'\b(scheme|registration|compulsory|mark)\b', text, re.IGNORECASE) or \
               re.search(r'/scheme-[a-z0-9-]+/', href, re.IGNORECASE):
                
                # Exclude purely PDF guidelines unless we specifically want PDFs (we want HTML catalogs here)
                if full_url.lower().endswith(".pdf"):
                    continue
                    
                seen_urls.add(full_url)
                scheme_name = text if text else href.split("/")[-2] if href.endswith("/") else href.split("/")[-1]
                
                discovered.append({
                    "parent_source_id": "SRC-005",
                    "scheme_name": scheme_name,
                    "discovered_url": full_url,
                    "anchor_text": text,
                    "discovery_evidence": f"Found via anchor tag inside {resp.url}",
                    "parent_hash": content_hash,
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                })
                
        return discovered

    def extract_structured_relationships(
        self, 
        scheme_info: Dict[str, Any], 
        tables: List[List[Dict[str, str]]]
    ) -> List[Dict[str, Any]]:
        """Phase 8.6D & E: Extract standardized Product->Standard relationships from generic tables."""
        relationships = []
        
        scheme_name = scheme_info.get("scheme_name", "Unknown Scheme")
        source_url = scheme_info.get("final_url", scheme_info.get("discovered_url", ""))
        source_hash = scheme_info.get("response_sha256", "")
        
        for t_idx, table_rows in enumerate(tables):
            for r_idx, row_dict in enumerate(table_rows):
                
                # Identify Product Name Column
                # Keys might be "Product", "Product Name", "Name of the Product", "Item"
                product_key = next((k for k in row_dict.keys() if k != "_raw_html" and re.search(r'product|item|name', k, re.IGNORECASE)), None)
                
                # Identify Standard Number Column
                # Keys might be "IS No.", "Indian Standard", "IS Number", "Standard"
                standard_key = next((k for k in row_dict.keys() if k != "_raw_html" and re.search(r'is\s*no|standard|is\s*number', k, re.IGNORECASE)), None)
                
                # Try fallback heuristics if header mapping isn't obvious
                if not product_key or not standard_key:
                    # Look at values: standard looks like "IS 1234 : 2000" or "15750"
                    for k, v in row_dict.items():
                        if k == "_raw_html": continue
                        if re.search(r'\bIS\s*\d+', v, re.IGNORECASE):
                            standard_key = k
                        elif len(v) > 3 and not re.search(r'\bIS\s*\d+', v, re.IGNORECASE) and not product_key:
                            product_key = k
                            
                if product_key and standard_key:
                    product_val = row_dict[product_key]
                    standard_val = row_dict[standard_key]
                    
                    if not product_val or not standard_val or product_val == "-" or standard_val == "-":
                        continue
                        
                    # Extract standard number generically (e.g. 'IS 15750 : 2006' -> 'IS 15750')
                    # Also handle multiple standards separated by commas or newlines
                    # But for now, preserve exactly what is in the table cell
                    
                    rel = {
                        "scheme": scheme_name,
                        "product_name": product_val,
                        "standard_number": standard_val,
                        "certification_scheme": scheme_name,
                        "table_index": t_idx,
                        "row_index": r_idx,
                        "source_url": source_url,
                        "source_sha256": source_hash,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "discovery_evidence": row_dict["_raw_html"]
                    }
                    
                    # Opportunistically map other common fields if present
                    title_key = next((k for k in row_dict.keys() if k != "_raw_html" and k != product_key and k != standard_key and re.search(r'title|description', k, re.IGNORECASE)), None)
                    if title_key:
                        rel["standard_title"] = row_dict[title_key]
                        
                    relationships.append(rel)
                    
        return relationships

    def fetch_and_parse_scheme(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 8.6B & C: Fetch scheme HTML, validate, check completeness, and parse tables."""
        url = scheme["discovered_url"]
        logger.info(f"Fetching scheme page: {url}")
        
        result = scheme.copy()
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch scheme {url}: {e}")
            result["status"] = "HTTP_FAILED"
            return result
            
        content_hash = generate_sha256(resp.content)
        result["final_url"] = resp.url
        result["http_status"] = resp.status_code
        result["content_type"] = resp.headers.get("content-type")
        result["response_sha256"] = content_hash
        
        if not is_bis_domain(resp.url):
            result["status"] = "INVALID_DOMAIN"
            return result
            
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = extract_tables_from_html(soup)
        
        total_rows = sum(len(t) for t in tables)
        result["table_count"] = len(tables)
        result["row_count"] = total_rows
        
        # Check completeness
        status = detect_completeness(soup, len(tables), total_rows)
        result["status"] = status
        
        if status == "COMPLETE_STATIC_HTML" or status == "PAGINATED":
            # Extract structured relationships
            relationships = self.extract_structured_relationships(result, tables)
            result["relationships"] = relationships
            
        return result
