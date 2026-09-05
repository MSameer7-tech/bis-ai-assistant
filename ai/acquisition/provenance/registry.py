"""
Evidence Registry for indexing, querying, and persisting citation-level provenance records (Phase 4 Batch F).
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import Counter
from ai.acquisition.provenance.models import (
    EvidenceRecord, EvidentiaryStrength, SourceFamily, SourceAuthority, LocatorType
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
EVIDENCE_PATH = REGISTRY_DIR / "evidence.jsonl"


class EvidenceRegistry:
    """
    Master registry managing all citation-level EvidenceRecord objects across the 15 BIS dimensions.
    """
    def __init__(self, registry_file: Path = EVIDENCE_PATH):
        self.registry_file = registry_file
        self.evidence_records: Dict[str, EvidenceRecord] = {}
        self.entity_to_evidence: Dict[str, List[str]] = {}
        self.strength_to_evidence: Dict[str, List[str]] = {}
        self.family_to_evidence: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        if not self.registry_file.exists():
            return

        self.evidence_records.clear()
        self.entity_to_evidence.clear()
        self.strength_to_evidence.clear()
        self.family_to_evidence.clear()

        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = EvidenceRecord.model_validate_json(line_str)
                        self._index_record(record)
                    except Exception as e:
                        logger.error(f"Error parsing evidence record: {e}")

        logger.info(f"Loaded {len(self.evidence_records)} evidence records from {self.registry_file}")

    def _index_record(self, record: EvidenceRecord):
        self.evidence_records[record.evidence_id] = record
        
        ent_key = record.entity_id.upper().strip()
        self.entity_to_evidence.setdefault(ent_key, []).append(record.evidence_id)

        str_key = record.evidentiary_strength.value
        self.strength_to_evidence.setdefault(str_key, []).append(record.evidence_id)

        fam_key = record.source_family.value
        self.family_to_evidence.setdefault(fam_key, []).append(record.evidence_id)

    def register_evidence(self, record: EvidenceRecord) -> None:
        self._index_record(record)

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceRecord]:
        return self.evidence_records.get(evidence_id)

    def get_by_entity(self, entity_id: str) -> List[EvidenceRecord]:
        ent_key = entity_id.upper().strip()
        ids = self.entity_to_evidence.get(ent_key, [])
        return [self.evidence_records[i] for i in ids if i in self.evidence_records]

    def get_by_edge(self, source: str, relation: str, target: str) -> List[EvidenceRecord]:
        edge_key = f"{source.upper().strip()}|{relation.upper().strip()}|{target.upper().strip()}"
        return self.get_by_entity(edge_key)

    def get_by_strength(self, strength: EvidentiaryStrength) -> List[EvidenceRecord]:
        ids = self.strength_to_evidence.get(strength.value, [])
        return [self.evidence_records[i] for i in ids if i in self.evidence_records]

    def get_by_family(self, family: SourceFamily) -> List[EvidenceRecord]:
        ids = self.family_to_evidence.get(family.value, [])
        return [self.evidence_records[i] for i in ids if i in self.evidence_records]

    def count(self) -> int:
        return len(self.evidence_records)

    def count_verified(self) -> int:
        return len(self.strength_to_evidence.get(EvidentiaryStrength.EVIDENCE_VERIFIED.value, []))

    def count_partial(self) -> int:
        return len(self.strength_to_evidence.get(EvidentiaryStrength.EVIDENCE_PARTIAL.value, []))

    def get_strength_distribution(self) -> Dict[str, int]:
        dist = Counter()
        for rec in self.evidence_records.values():
            dist[rec.evidentiary_strength.value] += 1
        return dict(dist)

    def save_all(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for record in sorted(self.evidence_records.values(), key=lambda x: x.evidence_id):
                f.write(record.model_dump_json() + "\n")
        logger.info(f"Saved {len(self.evidence_records)} evidence records to {self.registry_file}")
