"""
Evidence Repair Queue and Unresolved Evidence State Manager (Phase 4 Batch F).
Tracks missing or partially extracted primary sources for deterministic re-acquisition.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from ai.acquisition.provenance.models import EvidentiaryStrength, SourceFamily

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
REPAIR_QUEUE_PATH = REGISTRY_DIR / "evidence_repair_queue.jsonl"


class EvidenceRepairItem(BaseModel):
    """
    Queue item representing an entity, relationship, or claim with incomplete primary source backing.
    """
    item_id: str = Field(..., description="Unique repair queue ID e.g. REPAIR-STD-0544")
    entity_id: str = Field(..., description="Target entity or edge key")
    source_family: SourceFamily = Field(..., description="BIS Source Family")
    evidentiary_strength: EvidentiaryStrength = Field(..., description="Current weak strength state")
    missing_elements: List[str] = Field(default_factory=list, description="Missing elements e.g. ['RAW_PDF', 'TABLE_3_EXCERPT']")
    discovered_source_url: Optional[str] = Field(None, description="Known or scraped URL to acquire")
    priority: int = Field(default=1, description="1 (Critical Commodity), 2 (Standard), 3 (Bulk Catalog)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = Field(default=False)
    resolution_notes: Optional[str] = Field(None)


class EvidenceRepairQueue:
    """
    Manages the backlog of incomplete source documents and partial extractions.
    """
    def __init__(self, queue_file: Path = REPAIR_QUEUE_PATH):
        self.queue_file = queue_file
        self.items: Dict[str, EvidenceRepairItem] = {}
        self._load()

    def _load(self):
        if not self.queue_file.exists():
            return
        self.items.clear()
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        item = EvidenceRepairItem.model_validate_json(line_str)
                        self.items[item.item_id] = item
                    except Exception as e:
                        logger.error(f"Error parsing repair queue item: {e}")

    def enqueue(self, item: EvidenceRepairItem) -> None:
        self.items[item.item_id] = item

    def resolve(self, item_id: str, notes: str = "") -> None:
        if item_id in self.items:
            self.items[item_id].resolved = True
            self.items[item_id].resolution_notes = notes

    def complete(self, item_id: str, notes: str = "") -> None:
        """Alias for resolve."""
        self.resolve(item_id, notes)

    def get_pending(self, priority: Optional[int] = None) -> List[EvidenceRepairItem]:
        pending = [i for i in self.items.values() if not i.resolved]
        if priority is not None:
            pending = [i for i in pending if i.priority == priority]
        return sorted(pending, key=lambda x: (x.priority, x.created_at))

    def get_resolved(self) -> List[EvidenceRepairItem]:
        return [i for i in self.items.values() if i.resolved]

    def save_all(self) -> None:
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for item in sorted(self.items.values(), key=lambda x: x.item_id):
                f.write(item.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.items)} repair items to {self.queue_file}")
