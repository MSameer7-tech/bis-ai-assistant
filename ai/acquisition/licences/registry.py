"""
Licence Registry and Knowledge Management for BIS CM/L Manufacturer Licences (Phase 4 Batch D).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ai.acquisition.licences.models import LicenceRecord, LicenceStatus

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
LICENCES_PATH = REGISTRY_DIR / "licences.jsonl"


class LicenceRegistry:
    """
    Master registry managing all BIS CM/L ISI Mark and Conformity Assessment Manufacturer Licences.
    """
    def __init__(self, registry_file: Path = LICENCES_PATH):
        self.registry_file = registry_file
        self.licences: Dict[str, LicenceRecord] = {}
        self.standards_to_licences: Dict[str, List[str]] = {}
        self.brands_to_licences: Dict[str, List[str]] = {}
        self.licensees_to_licences: Dict[str, List[str]] = {}
        self.states_to_licences: Dict[str, List[str]] = {}
        self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            self._seed_default_registry()
            return

        self.licences.clear()
        self.standards_to_licences.clear()
        self.brands_to_licences.clear()
        self.licensees_to_licences.clear()
        self.states_to_licences.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = LicenceRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing licence record: {e}")

        logger.info(f"Loaded {len(self.licences)} licences from {self.registry_file}")

    def _index_record(self, record: LicenceRecord):
        self.licences[record.cml_number] = record
        
        std_clean = record.standard_number.upper().strip()
        self.standards_to_licences.setdefault(std_clean, []).append(record.cml_number)
        base_std = std_clean.split(":")[0].split("(")[0].strip()
        if base_std != std_clean:
            self.standards_to_licences.setdefault(base_std, []).append(record.cml_number)

        for b in record.brand_names:
            b_clean = b.upper().strip()
            self.brands_to_licences.setdefault(b_clean, []).append(record.cml_number)

        licensee_clean = record.licensee_name.lower().strip()
        self.licensees_to_licences.setdefault(licensee_clean, []).append(record.cml_number)

        state_clean = record.state.lower().strip()
        self.states_to_licences.setdefault(state_clean, []).append(record.cml_number)

    def get_by_cml(self, cml_number: str) -> Optional[LicenceRecord]:
        return self.licences.get(cml_number)

    def get_licences_for_standard(self, is_number: str, operative_only: bool = True) -> List[LicenceRecord]:
        """Returns all licences granted under a given standard."""
        std_clean = is_number.upper().strip()
        base_std = std_clean.split(":")[0].split("(")[0].strip()
        
        cml_set = set()
        if std_clean in self.standards_to_licences:
            cml_set.update(self.standards_to_licences[std_clean])
        if base_std in self.standards_to_licences:
            cml_set.update(self.standards_to_licences[base_std])

        results = [self.licences[cml] for cml in cml_set if cml in self.licences]
        if operative_only:
            results = [l for l in results if l.status == LicenceStatus.OPERATIVE]
        return results

    def get_licences_by_brand(self, brand_name: str) -> List[LicenceRecord]:
        b_clean = brand_name.upper().strip()
        cml_list = self.brands_to_licences.get(b_clean, [])
        return [self.licences[cml] for cml in cml_list if cml in self.licences]

    def count(self) -> int:
        return len(self.licences)

    def count_operative(self) -> int:
        return sum(1 for l in self.licences.values() if l.status == LicenceStatus.OPERATIVE)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.licences.values(), key=lambda x: x.cml_number):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.licences)} licences to {self.registry_file}")

    def _seed_default_registry(self):
        from ai.acquisition.licences.seed_data import SEED_LICENCES, generate_discovery_licence_universe
        all_licences = list(SEED_LICENCES)
        discovery_licences = generate_discovery_licence_universe(len(all_licences))
        all_licences.extend(discovery_licences)

        for l in all_licences:
            self._index_record(l)

        self.save_all()
