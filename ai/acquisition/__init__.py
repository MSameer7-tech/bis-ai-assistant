"""
Acquisition Subpackage for BIS AI Assistant.
Provides document downloaders, source monitors, and change detection gates.
"""

from ai.acquisition.downloader import DocumentDownloader
from ai.acquisition.source_monitor import SourceMonitor
from ai.acquisition.url_normalizer import normalize_url
from ai.ingestion.change_detector import ChangeDetector, check_source_freshness, compute_sha256

__all__ = [
    "DocumentDownloader",
    "SourceMonitor",
    "ChangeDetector",
    "check_source_freshness",
    "compute_sha256",
    "normalize_url",
]
