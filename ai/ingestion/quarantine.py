"""
Phase 5C: Document Acquisition, Quarantine, and Multi-Tier Validation Gate.
Enforces a strict quarantine boundary:
download -> quarantine -> validate -> promote to candidate staging (or isolate in rejected).
Never writes directly into production corpus.
"""
import os
import sys
import json
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ACQUISITION_DIR = DATA_DIR / "acquisition"
QUARANTINE_DIR = ACQUISITION_DIR / "quarantine"
VALIDATED_STAGING_DIR = ACQUISITION_DIR / "validated_staging"
REJECTED_DIR = QUARANTINE_DIR / "rejected"

from ai.ingestion.pdf_validator import PDFValidator, PDFValidationStatus


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class QuarantineManager:
    """
    Manages document quarantine, integrity verification, and promotion gates.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or ACQUISITION_DIR
        self.quarantine_dir = self.base_dir / "quarantine"
        self.staging_dir = self.base_dir / "validated_staging"
        self.rejected_dir = self.quarantine_dir / "rejected"
        self._ensure_directories()

    def _ensure_directories(self):
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    def process_quarantined_file(self, quarantined_file: Path, candidate_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates a quarantined file. If valid, promotes to validated staging.
        If invalid, moves to quarantine/rejected and records failure details.
        """
        doc_id = candidate_meta.get("document_id") or candidate_meta.get("candidate_id", "DOC-UNKNOWN")
        std_num = candidate_meta.get("standard_number", "UNKNOWN")
        
        result = {
            "document_id": doc_id,
            "standard_number": std_num,
            "quarantined_path": str(quarantined_file),
            "sha256": None,
            "validation_status": None,
            "promoted": False,
            "promoted_path": None,
            "error_details": None,
            "processed_at": datetime.now().isoformat()
        }

        if not quarantined_file.exists():
            result["validation_status"] = "FILE_MISSING"
            result["error_details"] = "Quarantined file not found on disk"
            return result

        # Compute SHA-256
        file_hash = compute_sha256(quarantined_file)
        result["sha256"] = file_hash

        # Run multi-tier PDF validation
        val_report = PDFValidator.validate_file(quarantined_file)
        status = val_report.get("status")
        result["validation_status"] = status

        if status in [PDFValidationStatus.TEXT_PDF.value, PDFValidationStatus.SCANNED_PDF.value, PDFValidationStatus.VALID_PDF.value]:
            # PROMOTE TO STAGING
            dest_name = f"{doc_id}_{std_num.replace(' ', '_').replace('/', '_')}.pdf"
            dest_path = self.staging_dir / dest_name
            shutil.copy2(quarantined_file, dest_path)
            
            result["promoted"] = True
            result["promoted_path"] = str(dest_path)
            logger.info(f"✅ Promoted {doc_id} ({std_num}) to validated staging: {dest_path}")
        else:
            # REJECT & ISOLATE IN QUARANTINE
            dest_name = f"{doc_id}_REJECTED_{quarantined_file.name}"
            dest_path = self.rejected_dir / dest_name
            shutil.move(str(quarantined_file), str(dest_path))
            
            result["promoted"] = False
            result["error_details"] = val_report.get("error_details") or f"Failed validation: {status}"
            logger.warning(f"❌ Rejected {doc_id} ({std_num}) in quarantine: {result['error_details']}")

        return result
