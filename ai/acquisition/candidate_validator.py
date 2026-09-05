"""
Candidate Document Validation & Quarantine Gate (Phase 3B).
Enforces security, domain authorization, and schema validation before any download occurs.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "sources" / "source_registry.json"
QUARANTINE_PATH = ROOT_DIR / "data" / "acquisition" / "quarantine" / "quarantined_candidates.json"
FAILURES_PATH = ROOT_DIR / "data" / "acquisition" / "failures" / "validation_failures.json"

from ai.acquisition.source_gate import (
    AUTHORIZED_GOV_DOMAINS,
    is_domain_authorized,
    is_source_acquisition_eligible
)
from ai.acquisition.discovery_engine import CandidateDocument

logger = logging.getLogger(__name__)

SUPPORTED_DOCUMENT_TYPES = {
    "INDIAN_STANDARD",
    "AMENDMENT",
    "CORRIGENDUM",
    "REAFFIRMATION",
    "WITHDRAWAL_NOTICE",
    "STANDARD_CATALOG_ENTRY",
    "QCO_NOTIFICATION",
    "GAZETTE_NOTIFICATION",
    "PRODUCT_MANUAL",
    "GROUPING_GUIDELINE",
    "SIT_SCHEDULE",
    "SCHEME_REGULATION",
    "CONFORMITY_ASSESSMENT_GUIDELINE",
    "LAB_DIRECTORY",
    "LAB_SCOPE",
    "LAB_RECOGNITION_ORDER",
    "LICENCE_RECORD",
    "CRS_REGISTRATION",
    "HALLMARKING_ORDER",
    "AHC_RECORD",
    "JEWELLER_REGISTRATION",
    "CONSUMER_GUIDE",
    "FAQ",
    "BIS_CARE_GUIDANCE",
    "STATUTORY_ACT"
}


class CandidateValidator:
    """Validates candidate documents against official source rules and security gates."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.sources_by_id = self._load_registry(registry_path)

    def _load_registry(self, registry_path: Path) -> Dict[str, Dict[str, Any]]:
        if not registry_path.exists():
            return {}
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {s["source_id"]: s for s in data.get("sources", [])}

    def validate_candidate(self, candidate: CandidateDocument) -> Tuple[bool, Optional[str]]:
        """
        Validates a single candidate document.
        Returns (is_valid, rejection_reason).
        """
        # Gate 1: Check source registration
        source = self.sources_by_id.get(candidate.source_id)
        if not source:
            return False, f"Source ID '{candidate.source_id}' is not registered in source_registry.json"

        # Gate 2: Check source family match
        if source.get("source_family_id") != candidate.source_family_id:
            return False, (
                f"Source family mismatch: candidate has '{candidate.source_family_id}', "
                f"registered source has '{source.get('source_family_id')}'"
            )

        # Gate 3: Check source acquisition eligibility
        if not is_source_acquisition_eligible(source):
            return False, f"Source '{candidate.source_id}' is not currently acquisition eligible"

        # Gate 4: Domain whitelisting check
        if not is_domain_authorized(candidate.source_url):
            return False, f"Candidate URL domain is not whitelisted: {candidate.source_url}"

        # Gate 5: Discovery source URL domain whitelisting check
        if not is_domain_authorized(candidate.discovered_from_url):
            return False, f"Discovery parent URL domain is not whitelisted: {candidate.discovered_from_url}"

        # Gate 6: Document type validity
        if candidate.document_type not in SUPPORTED_DOCUMENT_TYPES:
            return False, f"Unsupported document type: {candidate.document_type}"

        # Gate 7: Title and Candidate ID integrity
        if not candidate.title or len(candidate.title.strip()) < 3:
            return False, "Candidate document title is missing or too short"
        if not candidate.candidate_id or len(candidate.candidate_id.strip()) < 5:
            return False, "Invalid candidate_id"

        return True, None

    def filter_and_quarantine(self, candidates: List[CandidateDocument]) -> Tuple[List[CandidateDocument], List[Dict[str, Any]]]:
        """Filters valid candidates and persists quarantined rejected records."""
        valid_candidates = []
        quarantined_records = []

        for cand in candidates:
            ok, reason = self.validate_candidate(cand)
            if ok:
                valid_candidates.append(cand)
            else:
                quarantined_records.append({
                    "candidate_id": cand.candidate_id,
                    "source_id": cand.source_id,
                    "source_url": cand.source_url,
                    "document_type": cand.document_type,
                    "title": cand.title,
                    "rejection_reason": reason,
                    "quarantined_at": cand.discovered_at
                })

        if quarantined_records:
            QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(QUARANTINE_PATH, "w", encoding="utf-8") as f:
                json.dump(quarantined_records, f, indent=2)

        return valid_candidates, quarantined_records
