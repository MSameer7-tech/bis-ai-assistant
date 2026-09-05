"""
Laboratory Registry and Knowledge Management for BIS Testing Network (Phase 4 Batch D).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ai.acquisition.laboratories.models import LaboratoryRecord, LabType, LabStatus

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
LABS_PATH = REGISTRY_DIR / "laboratories.jsonl"


class LaboratoryRegistry:
    """
    Master registry managing all BIS-owned, recognized partner, and NABL-accredited laboratories.
    """
    def __init__(self, registry_file: Path = LABS_PATH):
        self.registry_file = registry_file
        self.laboratories: Dict[str, LaboratoryRecord] = {}
        self.standards_to_labs: Dict[str, List[str]] = {}
        self.products_to_labs: Dict[str, List[str]] = {}
        self.cities_to_labs: Dict[str, List[str]] = {}
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            self._seed_default_registry()
            return

        self.laboratories.clear()
        self.standards_to_labs.clear()
        self.products_to_labs.clear()
        self.cities_to_labs.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = LaboratoryRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing laboratory record: {e}")

        logger.info(f"Loaded {len(self.laboratories)} laboratories from {self.registry_file}")

    def _index_record(self, record: LaboratoryRecord):
        self.laboratories[record.lab_id] = record
        
        for std in record.standards_tested:
            std_clean = std.upper().strip()
            self.standards_to_labs.setdefault(std_clean, []).append(record.lab_id)
            # Index base number (e.g. IS 16046 from IS 16046 (Part 2) : 2018)
            base_std = std_clean.split(":")[0].split("(")[0].strip()
            if base_std != std_clean:
                self.standards_to_labs.setdefault(base_std, []).append(record.lab_id)

        for prod in record.product_categories:
            prod_clean = prod.lower().strip()
            self.products_to_labs.setdefault(prod_clean, []).append(record.lab_id)

        city_clean = record.city.lower().strip()
        self.cities_to_labs.setdefault(city_clean, []).append(record.lab_id)

    def get_by_id(self, lab_id: str) -> Optional[LaboratoryRecord]:
        return self.laboratories.get(lab_id)

    def get_labs_for_standard(self, is_number: str) -> List[LaboratoryRecord]:
        """Returns all laboratories equipped and accredited to test a given standard."""
        std_clean = is_number.upper().strip()
        base_std = std_clean.split(":")[0].split("(")[0].strip()
        
        lab_ids = set()
        if std_clean in self.standards_to_labs:
            lab_ids.update(self.standards_to_labs[std_clean])
        if base_std in self.standards_to_labs:
            lab_ids.update(self.standards_to_labs[base_std])

        return [self.laboratories[lid] for lid in lab_ids if lid in self.laboratories]

    def get_labs_by_type(self, lab_type: LabType) -> List[LaboratoryRecord]:
        return [l for l in self.laboratories.values() if l.lab_type == lab_type]

    def get_labs_by_city(self, city: str) -> List[LaboratoryRecord]:
        city_clean = city.lower().strip()
        lab_ids = self.cities_to_labs.get(city_clean, [])
        return [self.laboratories[lid] for lid in lab_ids if lid in self.laboratories]

    def count(self) -> int:
        return len(self.laboratories)

    def count_evidence_backed(self) -> int:
        return sum(1 for l in self.laboratories.values() if l.evidence_backed)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.laboratories.values(), key=lambda x: x.lab_id):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.laboratories)} laboratories to {self.registry_file}")

    def _seed_default_registry(self):
        """Seeds the authoritative 840-node laboratory universe with 50+ detailed accredited test houses."""
        from ai.acquisition.laboratories.seed_data import SEED_LABORATORIES, generate_discovery_lab_universe
        
        all_labs = list(SEED_LABORATORIES)
        discovery_labs = generate_discovery_lab_universe(len(all_labs))
        all_labs.extend(discovery_labs)

        for lab in all_labs:
            self._index_record(lab)

        self.save_all()
