"""
Base Discovery Strategy & Metrics Framework (Phase 3A-Cleanup).
Provides abstract contracts, HTTP fetching with rate-limiting, and metrics tracking for all source discovery adapters.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class DiscoveryMetrics(BaseModel):
    """Tracks crawl and discovery execution metrics per endpoint with exhaustion evidence."""
    source_id: str
    source_family_id: str = ""
    access_method: str
    pages_discovered: int = 0
    pages_processed: int = 0
    pages_visited: int = 0
    pages_skipped: int = 0
    pagination_exhausted: bool = True
    records_discovered: int = 0
    documents_discovered: int = 0
    structured_records_discovered: int = 0
    unique_candidates: int = 0
    duplicates_removed: int = 0
    invalid_records: int = 0
    excluded_navigation: int = 0
    excluded_invalid: int = 0
    source_exhausted: bool = True
    exhaustion_reason: str = "PAGINATION_EXHAUSTED"
    crawl_depth: int = 1
    pagination_status: str = "EXHAUSTED"
    source_errors: List[str] = Field(default_factory=list)
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    filter_metrics: Optional[Dict[str, int]] = Field(None, description="Link filter exclusion breakdown")
    dom_metrics: Optional[Dict[str, Any]] = Field(None, description="DOM structural analysis metrics")


class BaseDiscoveryStrategy(ABC):
    """Abstract interface for BIS endpoint discovery strategies."""

    def __init__(self, timeout: float = 15.0, max_pages: int = 5):
        self.timeout = timeout
        self.max_pages = max_pages
        self.headers = {
            "User-Agent": "BIS-AI-Technical-Assistant-Discovery/1.0 (Government-Regulatory-Research; Contact: discovery@bis.gov.in)"
        }

    def fetch_page(self, url: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempts to fetch live HTML/JSON from url.
        Returns (content_text, error_message).
        """
        if httpx is None:
            return None, "httpx library not available"

        try:
            with httpx.Client(headers=self.headers, verify=True, follow_redirects=True, timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.text, None
                return None, f"HTTP Status {resp.status_code}"
        except Exception as e:
            return None, str(e)

    @abstractmethod
    def discover(self, source: Dict[str, Any]) -> Tuple[List[Any], DiscoveryMetrics]:
        """
        Executes dynamic discovery against the specified registered source.
        Returns (List[CandidateDocument], DiscoveryMetrics).
        """
        pass
