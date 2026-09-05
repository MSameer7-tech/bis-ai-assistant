"""
Consumer Services Registry and Knowledge Management for BIS Care and Grievance Redressal (Phase 4 Batch E).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ai.acquisition.consumer.models import (
    ConsumerServiceRecord, ConsumerServiceCategory, ServiceChannel
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
CONSUMER_PATH = REGISTRY_DIR / "consumer.jsonl"


class ConsumerRegistry:
    """
    Master registry managing BIS Care, consumer verification workflows, and grievance redressal mechanisms.
    """
    def __init__(self, registry_file: Path = CONSUMER_PATH):
        self.registry_file = registry_file
        self.services: Dict[str, ConsumerServiceRecord] = {}
        self.categories_to_services: Dict[str, List[str]] = {}
        self.channels_to_services: Dict[str, List[str]] = {}
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            self._seed_default_registry()
            return

        self.services.clear()
        self.categories_to_services.clear()
        self.channels_to_services.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = ConsumerServiceRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing consumer service record: {e}")

        logger.info(f"Loaded {len(self.services)} consumer services from {self.registry_file}")

    def _index_record(self, record: ConsumerServiceRecord):
        self.services[record.service_id] = record
        
        cat_key = record.category.value
        self.categories_to_services.setdefault(cat_key, []).append(record.service_id)

        chan_key = record.channel.value
        self.channels_to_services.setdefault(chan_key, []).append(record.service_id)

    def get_by_id(self, service_id: str) -> Optional[ConsumerServiceRecord]:
        return self.services.get(service_id)

    def get_by_category(self, category: ConsumerServiceCategory) -> List[ConsumerServiceRecord]:
        ids = self.categories_to_services.get(category.value, [])
        return [self.services[i] for i in ids if i in self.services]

    def get_by_channel(self, channel: ServiceChannel) -> List[ConsumerServiceRecord]:
        ids = self.channels_to_services.get(channel.value, [])
        return [self.services[i] for i in ids if i in self.services]

    def count(self) -> int:
        return len(self.services)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.services.values(), key=lambda x: x.service_id):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.services)} consumer services to {self.registry_file}")

    def _seed_default_registry(self):
        from ai.acquisition.consumer.seed_data import SEED_CONSUMER_SERVICES, generate_discovery_consumer_universe
        all_records = list(SEED_CONSUMER_SERVICES)
        discovery_records = generate_discovery_consumer_universe(len(all_records))
        all_records.extend(discovery_records)

        for r in all_records:
            self._index_record(r)

        self.save_all()
