"""
Navigation and noise URL filter for BIS discovery (Phase 3A-Cleanup).
Separates genuine document/record links from navigation, footer, sidebar, login, language-switcher URLs.
Provides exclusion metrics for discovery audit.
"""
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

# Path patterns that indicate navigation/site-chrome, NOT documents
NAVIGATION_PATH_PATTERNS = [
    r"^/$",
    r"^/\?",
    r"^\s*#",
    r"/wp-login",
    r"/wp-admin",
    r"/feed/?$",
    r"/xmlrpc\.php",
    r"/wp-json/",
    r"/cart/?$",
    r"/checkout/?$",
    r"/my-account/?$",
    r"/login/?$",
    r"/logout/?$",
    r"/register/?$",
    r"/contact-us/?$",
    r"/about-us/?$",
    r"/the-bureau/?$",
    r"/privacy-policy/?$",
    r"/terms-and-conditions/?$",
    r"/disclaimer/?$",
    r"/sitemap/?$",
    r"/accessibility/?$",
    r"/web-information-manager/?$",
    r"/help/?$",
    r"/search/?$",
    r"/header",
    r"/footer",
    r"^javascript:",
    r"^mailto:",
    r"^tel:",
]

NAVIGATION_PATH_RE = re.compile("|".join(NAVIGATION_PATH_PATTERNS), re.IGNORECASE)

# Query params that indicate language switchers or session redirects
NOISE_QUERY_PATTERNS = [
    r"lang=(hi|en|ta|bn|gu|kn|ml|mr|or|pa|te|ur)",
    r"sessionExpire",
    r"logout",
    r"redirect",
]

NOISE_QUERY_RE = re.compile("|".join(NOISE_QUERY_PATTERNS), re.IGNORECASE)

# Titles/link text that indicate nav elements
NAV_TITLE_KEYWORDS = {
    "home", "menu", "footer", "header", "skip to content", "skip to main",
    "search", "login", "register", "logout", "contact us", "about us",
    "privacy policy", "terms", "disclaimer", "sitemap", "accessibility",
    "web information manager", "go to top", "back to top", "skip navigation",
    "हिन्दी", "english", "hin", "eng", "overview", "governing council",
    "executive committee", "bis history", "upcoming training programmes",
    "draft test request and test report formats", "arohatech it services"
}

# File extensions that are NOT documents
NON_DOCUMENT_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map",
}

# Document-indicative path patterns per source family
DOCUMENT_PATH_PATTERNS = {
    "SRCF-001": [r"/standards/", r"/know-your-standard/", r"\.pdf$", r"/IS-", r"bsbedge\.com"],
    "SRCF-002": [r"/amendments/", r"\.pdf$", r"-A\d+\.pdf", r"Amendment"],
    "SRCF-003": [r"/gazette/", r"/qco/", r"\.pdf$", r"/compulsory", r"/notification", r"Simplified-Procedure"],
    "SRCF-004": [r"/product-manuals/", r"/product-manual", r"\.pdf$", r"/PM-"],
    "SRCF-005": [r"/sit/", r"/scheme-of-inspection", r"\.pdf$", r"/SIT-"],
    "SRCF-006": [r"/schemes/", r"/certification", r"/product-certification/", r"/crs", r"\.pdf$", r"\.html$", r"SCHEME-", r"/BIS/"],
    "SRCF-007": [r"/records/", r"/MANAK/", r"/app-status", r"\.json$", r"\.do$"],
    "SRCF-008": [r"/laboratories/", r"/labs/", r"/lims", r"/home/bis_labs", r"/home/labs", r"\.pdf$", r"\.html$"],
    "SRCF-009": [r"/hallmarking/", r"/HUID", r"\.pdf$", r"\.html$", r"HM-"],
    "SRCF-010": [r"/consumer/", r"/bis-care", r"\.pdf$", r"\.html$", r"CONSUMER-"],
    "SRCF-011": [r"/publications/", r"/booklet", r"/faq", r"\.pdf$", r"\.html$", r"BOOKLET-", r"FAQ-"],
    "SRCF-012": [r"/acts/", r"/rules/", r"/regulations/", r"/the-bis-act", r"\.pdf$", r"uploads/\d{4}/\d{2}/"],
}


class LinkFilterMetrics:
    """Tracks exclusion metrics for discovery audit."""

    def __init__(self):
        self.raw_links = 0
        self.document_like_links = 0
        self.excluded_navigation = 0
        self.excluded_invalid_path = 0
        self.excluded_duplicate = 0
        self.excluded_invalid_metadata = 0
        self.excluded_lang_switcher = 0
        self.excluded_non_document_ext = 0
        self.valid_candidates = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "raw_links": self.raw_links,
            "document_like_links": self.document_like_links,
            "excluded_navigation": self.excluded_navigation,
            "excluded_invalid_path": self.excluded_invalid_path,
            "excluded_duplicate": self.excluded_duplicate,
            "excluded_invalid_metadata": self.excluded_invalid_metadata,
            "excluded_lang_switcher": self.excluded_lang_switcher,
            "excluded_non_document_ext": self.excluded_non_document_ext,
            "valid_candidates": self.valid_candidates,
        }


def is_navigation_url(url: str) -> bool:
    """Returns True if the URL is a navigation/chrome link, not a document."""
    if not url:
        return True

    # Root URLs, empty paths, javascript, mailto, tel
    if url in ("#", "/", "") or url.startswith("javascript:") or url.startswith("mailto:") or url.startswith("tel:"):
        return True

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path == "":
        return True

    # Check path patterns
    if NAVIGATION_PATH_RE.search(parsed.path) or NAVIGATION_PATH_RE.search(path):
        return True

    # Check query string and path for sessionExpire/noise
    if NOISE_QUERY_RE.search(parsed.query) or NOISE_QUERY_RE.search(parsed.path) or "sessionexpire" in url.lower():
        return True

    # Check file extension
    for ext in NON_DOCUMENT_EXTENSIONS:
        if parsed.path.lower().endswith(ext):
            return True

    return False


def is_navigation_title(title: str) -> bool:
    """Returns True if the link text is navigational, not document content."""
    clean = title.strip().lower()
    if len(clean) < 3:
        return True

    for kw in NAV_TITLE_KEYWORDS:
        if clean == kw or clean.startswith(kw + " ") or clean.endswith(" " + kw):
            return True

    return False


def matches_document_pattern(url: str, source_family_id: str) -> bool:
    """Checks if URL matches expected document path patterns for a source family."""
    patterns = DOCUMENT_PATH_PATTERNS.get(source_family_id, [])
    if not patterns:
        return True  # No patterns defined, allow

    path = urlparse(url).path
    for pat in patterns:
        if re.search(pat, path, re.IGNORECASE) or re.search(pat, url, re.IGNORECASE):
            return True

    return False


def filter_document_links(
    raw_links: List[Dict[str, str]],
    source_family_id: str,
    authorized_domains: set,
) -> Tuple[List[Dict[str, str]], LinkFilterMetrics]:
    """
    Filters raw extracted links into valid document candidates.
    Each link dict should have 'url' and 'title' keys.
    Returns (filtered_links, metrics).
    """
    metrics = LinkFilterMetrics()
    metrics.raw_links = len(raw_links)

    seen_urls = set()
    valid = []

    for link in raw_links:
        url = link.get("url", "")
        title = link.get("title", "")

        # Domain check
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if domain not in authorized_domains:
            metrics.excluded_invalid_path += 1
            continue

        # Navigation check
        if is_navigation_url(url):
            metrics.excluded_navigation += 1
            continue

        # Language switcher check
        if parsed.query and re.search(r"lang=", parsed.query, re.IGNORECASE):
            metrics.excluded_lang_switcher += 1
            continue

        # Non-document extension check
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in NON_DOCUMENT_EXTENSIONS):
            metrics.excluded_non_document_ext += 1
            continue

        metrics.document_like_links += 1

        # Title check
        if title and is_navigation_title(title):
            metrics.excluded_invalid_metadata += 1
            continue

        # Document pattern check
        if not matches_document_pattern(url, source_family_id):
            metrics.excluded_invalid_path += 1
            continue

        # Dedup
        norm_url = url.split("?")[0].rstrip("/").lower()
        if norm_url in seen_urls:
            metrics.excluded_duplicate += 1
            continue
        seen_urls.add(norm_url)

        valid.append(link)
        metrics.valid_candidates += 1

    return valid, metrics
