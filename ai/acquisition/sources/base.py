"""
Base Source Adapter Interface for BIS Discovery (Phase 6A).
Defines the uniform lifecycle contract for all modular BIS source adapters:
discover() -> normalize() -> validate() -> emit()
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BISSourceAdapter(ABC):
    """
    Abstract contract for all individual BIS portal adapters.
    """
    source_name: str = "base"
    name: str = "base"
    source_family: str = "general"
    base_url: str = ""

    @abstractmethod
    def discover(self, **kwargs) -> Any:
        """Scrapes or queries raw records from the underlying source portal."""
        pass

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Maps raw portal representation into canonical BIS schema."""
        return raw_record

    def validate(self, record: Dict[str, Any]) -> bool:
        """Ensures normalized record has required keys."""
        if not isinstance(record, dict):
            return True
        required = ["canonical_id", "entity_type", "title"]
        return all(k in record and record[k] is not None for k in required)

    def fetch_metadata(self, standard_number: str) -> Optional[Any]:
        """Fetches metadata for a specific standard number (optional for legacy compatibility)."""
        return None

    def emit(self, **kwargs) -> List[Dict[str, Any]]:
        """Executes full adapter pipeline: discover -> normalize -> validate -> emit."""
        raw_items = self.discover(**kwargs)
        valid_items = []
        if isinstance(raw_items, list):
            for raw in raw_items:
                if isinstance(raw, dict):
                    norm = self.normalize(raw)
                    if self.validate(norm):
                        valid_items.append(norm)
                else:
                    valid_items.append(raw)
        return valid_items


BaseSourceAdapter = BISSourceAdapter
