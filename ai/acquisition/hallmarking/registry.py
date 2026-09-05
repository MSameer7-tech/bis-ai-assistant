"""
Hallmarking Registry and Knowledge Management for BIS Precious Metals System (Phase 4 Batch E).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ai.acquisition.hallmarking.models import HallmarkRecord, AHCStatus, GoldPurityFineness
from ai.acquisition.hallmarking.seed_data import GOLD_PURITY_GRADES, SILVER_PURITY_GRADES

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
HALLMARKING_PATH = REGISTRY_DIR / "hallmarking.jsonl"


class HallmarkRegistry:
    """
    Master registry managing BIS Assaying & Hallmarking Centres (AHC), HUID validation, and purity grades.
    """
    def __init__(self, registry_file: Path = HALLMARKING_PATH):
        self.registry_file = registry_file
        self.ahc_records: Dict[str, HallmarkRecord] = {}
        self.districts_to_ahc: Dict[str, List[str]] = {}
        self.cities_to_ahc: Dict[str, List[str]] = {}
        self.gold_purity_grades: List[GoldPurityFineness] = GOLD_PURITY_GRADES
        self.silver_purity_grades: List[Dict[str, Any]] = SILVER_PURITY_GRADES
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            self._seed_default_registry()
            return

        self.ahc_records.clear()
        self.districts_to_ahc.clear()
        self.cities_to_ahc.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = HallmarkRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing hallmarking record: {e}")

        logger.info(f"Loaded {len(self.ahc_records)} AHC records from {self.registry_file}")

    def _index_record(self, record: HallmarkRecord):
        self.ahc_records[record.ahc_id] = record
        
        district_clean = record.district.lower().strip()
        self.districts_to_ahc.setdefault(district_clean, []).append(record.ahc_id)

        city_clean = record.city.lower().strip()
        self.cities_to_ahc.setdefault(city_clean, []).append(record.ahc_id)

    def get_by_ahc_id(self, ahc_id: str) -> Optional[HallmarkRecord]:
        return self.ahc_records.get(ahc_id)

    def get_ahcs_by_district(self, district: str) -> List[HallmarkRecord]:
        d_clean = district.lower().strip()
        ids = self.districts_to_ahc.get(d_clean, [])
        return [self.ahc_records[i] for i in ids if i in self.ahc_records]

    def get_ahcs_by_city(self, city: str) -> List[HallmarkRecord]:
        c_clean = city.lower().strip()
        ids = self.cities_to_ahc.get(c_clean, [])
        return [self.ahc_records[i] for i in ids if i in self.ahc_records]

    def validate_huid(self, huid: str) -> bool:
        """Validates 6-digit alphanumeric HUID code."""
        return HallmarkRecord.validate_huid(huid)

    def get_gold_purity_by_karat(self, karat: str) -> Optional[GoldPurityFineness]:
        k_clean = karat.upper().replace(" ", "").strip()
        for g in self.gold_purity_grades:
            if g.karat.upper() == k_clean:
                return g
        return None

    def get_gold_purity_by_fineness(self, fineness: int) -> Optional[GoldPurityFineness]:
        for g in self.gold_purity_grades:
            if g.fineness_ppt == fineness:
                return g
        return None

    def count(self) -> int:
        return len(self.ahc_records)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.ahc_records.values(), key=lambda x: x.ahc_id):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.ahc_records)} AHC records to {self.registry_file}")

    def _seed_default_registry(self):
        from ai.acquisition.hallmarking.seed_data import SEED_AHCS, generate_discovery_hallmarking_universe
        all_records = list(SEED_AHCS)
        discovery_records = generate_discovery_hallmarking_universe(len(all_records))
        all_records.extend(discovery_records)

        for r in all_records:
            self._index_record(r)

        self.save_all()
