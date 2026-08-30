"""
Source Monitor Module for BIS Standards Acquisition.
Periodically polls or scans registered BIS portals and repository endpoints for revisions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from ai.acquisition.downloader import DocumentDownloader
from ai.ingestion.change_detector import ChangeDetector

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "metadata" / "source_registry.json"


class SourceMonitor:
    """Monitors standard and regulation sources for new revisions or amendments."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path
        self.change_detector = ChangeDetector(registry_path=registry_path)
        self.downloader = DocumentDownloader()

    def check_for_updates(self) -> Dict[str, Any]:
        """Scans local and remote records for changes."""
        return self.change_detector.scan_all_sources()
