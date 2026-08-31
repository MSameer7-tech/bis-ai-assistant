"""
Base Source Adapter for BIS Discovery Crawler.
Defines the standard abstract interface for discovering BIS standards and regulatory notifications.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ai.acquisition.crawler_models import DiscoveredStandard


class BaseSourceAdapter(ABC):
    """Abstract base adapter for discovering and acquiring documents from BIS sources."""

    name: str = "base"

    @abstractmethod
    def discover(
        self,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[DiscoveredStandard]:
        """
        Discovers standards from the target source matching domain and limit constraints.
        """
        pass

    @abstractmethod
    def fetch_metadata(
        self,
        standard_number: str,
    ) -> Optional[DiscoveredStandard]:
        """
        Fetches detailed metadata for a specific standard number.
        """
        pass
