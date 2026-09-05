"""
CRS Registry and Knowledge Management for Electronics / IT Compulsory Registration Scheme (Phase 4 Batch D).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ai.acquisition.crs.models import CRSRecord, CRSStatus

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
CRS_PATH = REGISTRY_DIR / "crs.jsonl"


class CRSRegistry:
    """
    Master registry managing all BIS Scheme-II Compulsory Registration Scheme (CRS) electronics records.
    """
    def __init__(self, registry_file: Path = CRS_PATH):
        self.registry_file = registry_file
        self.registrations: Dict[str, CRSRecord] = {}
        self.standards_to_crs: Dict[str, List[str]] = {}
        self.brands_to_crs: Dict[str, List[str]] = {}
        self.models_to_crs: Dict[str, str] = {}
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            self._seed_default_registry()
            return

        self.registrations.clear()
        self.standards_to_crs.clear()
        self.brands_to_crs.clear()
        self.models_to_crs.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = CRSRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing CRS record: {e}")

        logger.info(f"Loaded {len(self.registrations)} CRS records from {self.registry_file}")

    def _index_record(self, record: CRSRecord):
        self.registrations[record.registration_number] = record
        
        std_clean = record.standard_number.upper().strip()
        self.standards_to_crs.setdefault(std_clean, []).append(record.registration_number)
        base_std = std_clean.split(":")[0].split("(")[0].strip()
        if base_std != std_clean:
            self.standards_to_crs.setdefault(base_std, []).append(record.registration_number)

        b_clean = record.brand_name.upper().strip()
        self.brands_to_crs.setdefault(b_clean, []).append(record.registration_number)

        for model in record.model_numbers:
            m_clean = model.upper().strip()
            self.models_to_crs[m_clean] = record.registration_number

    def get_by_r_number(self, r_number: str) -> Optional[CRSRecord]:
        return self.registrations.get(r_number.upper().strip())

    def get_by_model(self, model_number: str) -> Optional[CRSRecord]:
        m_clean = model_number.upper().strip()
        r_num = self.models_to_crs.get(m_clean)
        return self.registrations.get(r_num) if r_num else None

    def get_crs_for_standard(self, is_number: str, active_only: bool = True) -> List[CRSRecord]:
        """Returns all CRS registrations for a given standard."""
        std_clean = is_number.upper().strip()
        base_std = std_clean.split(":")[0].split("(")[0].strip()
        
        r_set = set()
        if std_clean in self.standards_to_crs:
            r_set.update(self.standards_to_crs[std_clean])
        if base_std in self.standards_to_crs:
            r_set.update(self.standards_to_crs[base_std])

        results = [self.registrations[r] for r in r_set if r in self.registrations]
        if active_only:
            results = [r for r in results if r.status == CRSStatus.ACTIVE]
        return results

    def get_crs_by_brand(self, brand_name: str) -> List[CRSRecord]:
        b_clean = brand_name.upper().strip()
        r_list = self.brands_to_crs.get(b_clean, [])
        return [self.registrations[r] for r in r_list if r in self.registrations]

    def count(self) -> int:
        return len(self.registrations)

    def count_active(self) -> int:
        return sum(1 for r in self.registrations.values() if r.status == CRSStatus.ACTIVE)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.registrations.values(), key=lambda x: x.registration_number):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.registrations)} CRS records to {self.registry_file}")

    def _seed_default_registry(self):
        from ai.acquisition.crs.seed_data import SEED_CRS_RECORDS, generate_discovery_crs_universe
        all_records = list(SEED_CRS_RECORDS)
        discovery_records = generate_discovery_crs_universe(len(all_records))
        all_records.extend(discovery_records)

        for r in all_records:
            self._index_record(r)

        self.save_all()
