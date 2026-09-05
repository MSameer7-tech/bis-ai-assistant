"""
DOM-Aware Structure Analyzer for Official BIS & Statutory Web Endpoints.
Deterministic semantic region identification, document record extraction, chrome/navigation exclusion,
and provenance evidence preservation for Phase 3 Discovery.
"""
from dataclasses import dataclass, field, asdict
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup, Tag, NavigableString
except ImportError:
    BeautifulSoup = None
    Tag = None
    NavigableString = None

logger = logging.getLogger(__name__)

# Excluded non-document extensions
NON_DOC_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".zip", ".tar", ".gz"
}

# Structural class/id patterns for navigation and chrome exclusion
NAV_CLASS_PATTERNS = re.compile(
    r"\b(nav|navbar|navigation|menu|top[-_ ]?menu|main[-_ ]?menu|header[-_ ]?menu|site[-_ ]?nav|dropdown[-_ ]?menu|breadcrumbs?|crumbs?)\b",
    re.IGNORECASE
)
FOOTER_CLASS_PATTERNS = re.compile(
    r"\b(footer|site[-_ ]?footer|sub[-_ ]?footer|bottom[-_ ]?menu|copyright|credits)\b",
    re.IGNORECASE
)
SIDEBAR_CLASS_PATTERNS = re.compile(
    r"\b(sidebar|aside|widget[-_ ]?area|left[-_ ]?menu|right[-_ ]?menu)\b",
    re.IGNORECASE
)
LANG_CLASS_PATTERNS = re.compile(
    r"\b(lang|language|language[-_ ]?switcher|lang[-_ ]?switch|lang[-_ ]?selector|poly[-_ ]?lang)\b|lang[-_ ]?switch",
    re.IGNORECASE
)

# Text patterns indicating navigation/chrome
CHROME_LINK_TEXTS = {
    "home", "about us", "contact us", "sitemap", "feedback", "tenders",
    "careers", "disclaimer", "privacy policy", "terms of use", "screen reader access",
    "skip to main content", "skip to navigation", "a+", "a-", "a", "hindi", "english",
    "login", "sign in", "register", "logout", "help", "faq", "faqs", "overview",
    "मुख्य पृष्ठ", "हमारे बारे में", "संपर्क करें", "साइटमैप"
}


@dataclass
class DOMDiscoveryEvidence:
    """Provenance and structural evidence for a candidate document discovered from the DOM."""
    source_page_url: str
    discovered_url: str
    element_tag: str
    link_text: str
    nearest_heading: Optional[str] = None
    container_tag: Optional[str] = None
    container_class: Optional[str] = None
    container_id: Optional[str] = None
    table_name: Optional[str] = None
    table_row_text: Optional[str] = None
    region_type: str = "MAIN_CONTENT"
    extraction_strategy: str = "DOM_ANALYZER"
    source_family: str = ""
    document_type: str = ""
    discovery_reason: str = "semantic_content_region_match"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DOMRecord:
    """A structured content record extracted from a DOM node."""
    title: str
    url: str
    document_type: str
    standard_number: Optional[str] = None
    part: Optional[str] = None
    edition_year: Optional[int] = None
    parent_document_id: Optional[str] = None
    related_standard_id: Optional[str] = None
    relationship_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: Optional[DOMDiscoveryEvidence] = None


@dataclass
class DOMAnalysisMetrics:
    """Quantitative structural and exclusion metrics from DOM analysis."""
    raw_dom_elements: int = 0
    raw_links: int = 0
    navigation_elements: int = 0
    navigation_links_excluded: int = 0
    footer_links_excluded: int = 0
    sidebar_links_excluded: int = 0
    language_links_excluded: int = 0
    document_regions: int = 0
    document_like_links: int = 0
    records_detected: int = 0
    pagination_detected: bool = False
    pagination_pages: int = 0
    session_gated: bool = False
    duplicates: int = 0
    valid_candidates: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DOMAnalyzer:
    """
    Deterministic DOM Analyzer for BIS & Statutory web pages.
    Parses HTML, detects layout regions, filters chrome/noise, and extracts structured records with evidence.
    """

    def __init__(self, authorized_domains: Optional[Set[str]] = None):
        self.authorized_domains = authorized_domains or {
            "bis.gov.in", "www.bis.gov.in", "egazette.gov.in", "www.egazette.gov.in",
            "manakonline.in", "www.manakonline.in", "crsbis.in", "www.crsbis.in",
            "standardsbis.bsbedge.com", "lims.bis.gov.in", "services.bis.gov.in", "www.services.bis.gov.in"
        }

    def parse_dom(self, html_content: str) -> Optional[BeautifulSoup]:
        """Parses HTML text into a BeautifulSoup DOM tree."""
        if not html_content or BeautifulSoup is None:
            return None
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup.find_all(["script", "style", "noscript", "template"]):
                tag.decompose()
            return soup
        except Exception as e:
            logger.warning("DOM parsing error: %s", e)
            return None

    def is_session_gated(self, soup: BeautifulSoup, url: str) -> bool:
        """Determines if the DOM represents a session expiration, login gate, or WAF blockage."""
        url_lower = url.lower()
        if "sessionexpire" in url_lower or "login" in url_lower or "auth" in url_lower:
            return True

        if soup is None:
            return False

        # Inspect title and body text
        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        if any(term in title for term in ["session expired", "session expire", "login", "access denied", "waf"]):
            return True

        # Inspect headings
        for h in soup.find_all(["h1", "h2", "h3", "h4"]):
            h_text = h.get_text(strip=True).lower()
            if "session expired" in h_text or "please login" in h_text or "access denied" in h_text:
                return True

        # Check for standalone login form without content
        forms = soup.find_all("form")
        for f in forms:
            action = f.get("action", "").lower()
            if "login" in action or "session" in action:
                if not soup.find_all(["table", "article", ".content"]):
                    return True

        return False

    def is_navigation_element(self, element: Tag) -> Tuple[bool, str]:
        """
        Checks whether a DOM element is inside a header, navigation bar, footer, sidebar,
        breadcrumb, or language selector.
        Returns (is_nav, region_name).
        """
        if not isinstance(element, Tag):
            return False, ""

        curr = element
        while curr and curr.name != "[document]":
            tag_name = curr.name.lower() if curr.name else ""
            class_str = " ".join(curr.get("class", [])) if curr.get("class") else ""
            id_str = curr.get("id", "") or ""

            if tag_name in ["nav", "header"]:
                return True, "HEADER_NAVIGATION"
            if tag_name == "footer":
                return True, "FOOTER"
            if tag_name == "aside":
                return True, "SIDEBAR"

            if NAV_CLASS_PATTERNS.search(class_str) or NAV_CLASS_PATTERNS.search(id_str):
                return True, "NAVIGATION"
            if FOOTER_CLASS_PATTERNS.search(class_str) or FOOTER_CLASS_PATTERNS.search(id_str):
                return True, "FOOTER"
            if SIDEBAR_CLASS_PATTERNS.search(class_str) or SIDEBAR_CLASS_PATTERNS.search(id_str):
                return True, "SIDEBAR"
            if LANG_CLASS_PATTERNS.search(class_str) or LANG_CLASS_PATTERNS.search(id_str):
                return True, "LANGUAGE_SELECTOR"

            curr = curr.parent

        return False, ""

    def find_nearest_heading(self, element: Tag) -> Optional[str]:
        """Locates the nearest preceding heading (h1-h6, caption, legend) in the DOM tree."""
        if not isinstance(element, Tag):
            return None

        # 1. Look inside parent container first
        curr = element
        while curr and curr.name != "[document]":
            # Search preceding headings in same container
            prev_headings = curr.find_all_previous(["h1", "h2", "h3", "h4", "h5", "h6", "caption", "legend"])
            if prev_headings:
                for h in prev_headings:
                    text = h.get_text(strip=True)
                    if text and len(text) > 2:
                        return text
            curr = curr.parent

        return None

    def get_container_info(self, element: Tag) -> Tuple[str, str, str]:
        """Returns (container_tag, container_class, container_id) for the nearest enclosing block."""
        if not isinstance(element, Tag):
            return "unknown", "", ""

        curr = element.parent
        while curr and curr.name != "[document]":
            tag_name = curr.name.lower() if curr.name else ""
            if tag_name in ["article", "section", "tr", "table", "li", "main", "div", "form"]:
                class_str = " ".join(curr.get("class", [])) if curr.get("class") else ""
                id_str = curr.get("id", "") or ""
                return tag_name, class_str, id_str
            curr = curr.parent

        return "body", "", ""

    def detect_pagination(self, soup: BeautifulSoup) -> Tuple[bool, int]:
        """Detects pagination elements and extracts page count."""
        if soup is None:
            return False, 0

        pagination_containers = soup.find_all(
            lambda t: t.name in ["div", "nav", "ul"] and (
                "pagination" in " ".join(t.get("class", [])) or
                "page-numbers" in " ".join(t.get("class", [])) or
                t.get("aria-label") == "pagination"
            )
        )

        if not pagination_containers:
            return False, 0

        page_links = []
        for p_cont in pagination_containers:
            for a in p_cont.find_all("a"):
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if text.isdigit() or "page" in href.lower() or "paged" in href.lower():
                    page_links.append(text)

        pages = len(set(page_links))
        return True, max(pages, 1)

    def is_valid_document_url(self, url: str) -> bool:
        """Validates that a URL is well-formed, authorized, and not a non-document asset."""
        if not url or url.startswith("#") or url.startswith("javascript:"):
            return False

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        domain = parsed.netloc.lower()
        if not any(domain == auth or domain.endswith("." + auth) for auth in self.authorized_domains):
            return False

        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in NON_DOC_EXTENSIONS):
            return False

        # Filter out JavaScript snippets and template literals
        if any(bad in url for bad in ["employees[", "undefined", "{", "}", "<", ">", '"', "'", "javascript:"]):
            return False

        return True

    def analyze_table_regions(
        self,
        soup: BeautifulSoup,
        base_url: str,
        source_id: str,
        family_id: str,
        metrics: DOMAnalysisMetrics
    ) -> List[DOMRecord]:
        """Extracts structured candidate records from table rows (e.g. labs, standards, schemes)."""
        records: List[DOMRecord] = []
        if soup is None:
            return records

        tables = soup.find_all("table")
        for table in tables:
            # Check if table is inside navigation or footer
            is_nav, region = self.is_navigation_element(table)
            if is_nav:
                continue

            metrics.document_regions += 1
            caption = table.find("caption")
            caption_text = caption.get_text(strip=True) if caption else ""
            nearest_h = self.find_nearest_heading(table) or caption_text

            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells or all(c.name == "th" for c in cells):
                    continue  # skip pure header row

                row_text = " | ".join(c.get_text(strip=True) for c in cells if c.get_text(strip=True))
                if not row_text or len(row_text) < 3:
                    continue

                links = row.find_all("a", href=True)
                if links:
                    for a in links:
                        raw_href = a.get("href", "").strip()
                        resolved_url = urljoin(base_url, raw_href)
                        link_text = a.get_text(strip=True) or row_text[:80]

                        metrics.raw_links += 1

                        if not self.is_valid_document_url(resolved_url):
                            continue

                        evidence = DOMDiscoveryEvidence(
                            source_page_url=base_url,
                            discovered_url=resolved_url,
                            element_tag="a",
                            link_text=link_text,
                            nearest_heading=nearest_h,
                            container_tag="tr",
                            container_class=" ".join(row.get("class", [])) if row.get("class") else "",
                            container_id=row.get("id", "") or "",
                            table_name=caption_text or nearest_h,
                            table_row_text=row_text,
                            region_type="TABLE_ROW",
                            extraction_strategy="DOM_TABLE_EXTRACTOR",
                            source_family=family_id,
                            discovery_reason=f"table_row_record_in_{nearest_h or 'table'}"
                        )

                        records.append(DOMRecord(
                            title=link_text,
                            url=resolved_url,
                            document_type="DOCUMENT",
                            metadata={"table_name": caption_text, "row_data": row_text},
                            evidence=evidence
                        ))
                else:
                    # Table row with no anchor link (e.g. laboratory register row, scheme item)
                    first_cell = cells[0].get_text(strip=True)
                    second_cell = cells[1].get_text(strip=True) if len(cells) > 1 else first_cell
                    rec_title = second_cell if len(second_cell) > len(first_cell) else first_cell

                    evidence = DOMDiscoveryEvidence(
                        source_page_url=base_url,
                        discovered_url=base_url,
                        element_tag="tr",
                        link_text=rec_title,
                        nearest_heading=nearest_h,
                        container_tag="table",
                        container_class=" ".join(table.get("class", [])) if table.get("class") else "",
                        container_id=table.get("id", "") or "",
                        table_name=caption_text or nearest_h,
                        table_row_text=row_text,
                        region_type="TABLE_ROW",
                        extraction_strategy="DOM_TABLE_ROW_RECORD",
                        source_family=family_id,
                        discovery_reason="structured_table_row_without_external_link"
                    )

                    records.append(DOMRecord(
                        title=rec_title,
                        url=base_url,
                        document_type="RECORD",
                        metadata={"table_name": caption_text, "row_data": row_text},
                        evidence=evidence
                    ))

        return records

    def analyze_card_and_article_regions(
        self,
        soup: BeautifulSoup,
        base_url: str,
        source_id: str,
        family_id: str,
        metrics: DOMAnalysisMetrics
    ) -> List[DOMRecord]:
        """Extracts candidate documents from semantic card grids, articles, and content sections."""
        records: List[DOMRecord] = []
        if soup is None:
            return records

        card_containers = soup.find_all(
            lambda t: t.name in ["article", "section", "div", "li"] and any(
                term in " ".join(t.get("class", [])).lower()
                for term in ["card", "post", "entry", "item", "scheme-box", "manual-box", "faq-item", "doc-box"]
            )
        )

        for container in card_containers:
            is_nav, region = self.is_navigation_element(container)
            if is_nav:
                continue

            metrics.document_regions += 1
            nearest_h = self.find_nearest_heading(container)

            # Find main heading inside card
            card_heading = container.find(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"])
            heading_text = card_heading.get_text(strip=True) if card_heading else ""

            # Find all links inside card
            links = container.find_all("a", href=True)
            for a in links:
                raw_href = a.get("href", "").strip()
                resolved_url = urljoin(base_url, raw_href)
                link_text = a.get_text(strip=True) or heading_text

                metrics.raw_links += 1

                if not self.is_valid_document_url(resolved_url):
                    continue

                c_tag, c_class, c_id = self.get_container_info(a)

                evidence = DOMDiscoveryEvidence(
                    source_page_url=base_url,
                    discovered_url=resolved_url,
                    element_tag="a",
                    link_text=link_text,
                    nearest_heading=nearest_h or heading_text,
                    container_tag=c_tag,
                    container_class=c_class,
                    container_id=c_id,
                    region_type="CARD_CONTAINER",
                    extraction_strategy="DOM_CARD_EXTRACTOR",
                    source_family=family_id,
                    discovery_reason=f"card_item_link_in_{c_class or 'card'}"
                )

                records.append(DOMRecord(
                    title=heading_text or link_text,
                    url=resolved_url,
                    document_type="DOCUMENT",
                    metadata={"container_class": c_class, "heading": heading_text},
                    evidence=evidence
                ))

        return records

    def analyze_content_document_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        source_id: str,
        family_id: str,
        metrics: DOMAnalysisMetrics
    ) -> List[DOMRecord]:
        """Extracts document/PDF links from the main content body while strictly excluding chrome."""
        records: List[DOMRecord] = []
        if soup is None:
            return records

        # Process all page anchors to classify navigation vs main content document links
        anchors = soup.find_all("a", href=True)
        metrics.raw_dom_elements = len(soup.find_all())

        for a in anchors:
            metrics.raw_links += 1
            raw_href = a.get("href", "").strip()
            link_text = a.get_text(strip=True)
            link_text_lower = link_text.lower()

            # 1. Structural Navigation / Chrome check
            is_nav, region = self.is_navigation_element(a)
            if is_nav:
                metrics.navigation_elements += 1
                if region == "FOOTER":
                    metrics.footer_links_excluded += 1
                elif region == "SIDEBAR":
                    metrics.sidebar_links_excluded += 1
                elif region == "LANGUAGE_SELECTOR":
                    metrics.language_links_excluded += 1
                else:
                    metrics.navigation_links_excluded += 1
                continue

            # 2. Text-based chrome exclusion
            if link_text_lower in CHROME_LINK_TEXTS or (len(link_text) <= 1 and not raw_href.endswith(".pdf")):
                metrics.navigation_links_excluded += 1
                continue

            # 3. URL validity & asset extension filtering
            resolved_url = urljoin(base_url, raw_href)
            if not self.is_valid_document_url(resolved_url):
                continue

            # 4. Language switcher query param check
            if "lang=" in resolved_url.lower() and not resolved_url.lower().endswith(".pdf"):
                metrics.language_links_excluded += 1
                continue

            metrics.document_like_links += 1
            c_tag, c_class, c_id = self.get_container_info(a)
            nearest_h = self.find_nearest_heading(a)

            evidence = DOMDiscoveryEvidence(
                source_page_url=base_url,
                discovered_url=resolved_url,
                element_tag="a",
                link_text=link_text,
                nearest_heading=nearest_h,
                container_tag=c_tag,
                container_class=c_class,
                container_id=c_id,
                region_type="MAIN_CONTENT_LINK",
                extraction_strategy="DOM_MAIN_CONTENT_LINK",
                source_family=family_id,
                discovery_reason=f"main_content_anchor_under_{nearest_h or 'section'}"
            )

            records.append(DOMRecord(
                title=link_text or (nearest_h or "BIS Document"),
                url=resolved_url,
                document_type="DOCUMENT",
                metadata={"container_tag": c_tag, "container_class": c_class},
                evidence=evidence
            ))

        return records

    def analyze_dom(
        self,
        html_content: str,
        base_url: str,
        source_id: str,
        family_id: str
    ) -> Tuple[List[DOMRecord], DOMAnalysisMetrics]:
        """
        Master DOM Analysis pipeline:
        1. Parses DOM
        2. Detects session gate
        3. Detects pagination
        4. Extracts table records, card records, and main content document links
        5. Deduplicates within page and attaches rich provenance evidence
        """
        metrics = DOMAnalysisMetrics()
        soup = self.parse_dom(html_content)

        if soup is None:
            return [], metrics

        # 1. Check for session gates / auth / WAF
        if self.is_session_gated(soup, base_url):
            metrics.session_gated = True
            return [], metrics

        # 2. Check for pagination
        has_pag, num_pages = self.detect_pagination(soup)
        metrics.pagination_detected = has_pag
        metrics.pagination_pages = num_pages

        # 3. Extract via semantic layout strategies
        table_records = self.analyze_table_regions(soup, base_url, source_id, family_id, metrics)
        card_records = self.analyze_card_and_article_regions(soup, base_url, source_id, family_id, metrics)
        link_records = self.analyze_content_document_links(soup, base_url, source_id, family_id, metrics)

        all_records = table_records + card_records + link_records
        metrics.records_detected = len(all_records)

        # 4. In-page Deduplication preserving best title and evidence
        seen_urls: Set[str] = set()
        unique_records: List[DOMRecord] = []

        for rec in all_records:
            norm_url = rec.url.strip().rstrip("/")
            if norm_url in seen_urls:
                metrics.duplicates += 1
                continue
            seen_urls.add(norm_url)
            unique_records.append(rec)

        metrics.valid_candidates = len(unique_records)
        return unique_records, metrics
