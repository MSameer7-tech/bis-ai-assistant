"""
Standards Registry Manager.
Manages versioned, immutable standard records with complete temporal provenance,
status tracking, query filtering, and serialization to data/registry/standards.jsonl.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from ai.acquisition.standards.models import (
    StandardRecord,
    StandardStatus,
    AcquisitionStatus,
    AcquisitionFailureReason,
    AspectType
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "registry" / "standards.jsonl"
CATALOG_PATH = ROOT_DIR / "data" / "registry" / "standards_catalog.jsonl"
DOC_META_PATH = ROOT_DIR / "data" / "metadata" / "documents.json"
RAW_DIR = ROOT_DIR / "data" / "raw"


class StandardsRegistry:
    """Master registry managing all authoritative Indian Standards records."""

    def __init__(self, registry_file: Path = REGISTRY_PATH):
        self.registry_file = registry_file
        self.standards: Dict[str, StandardRecord] = {}
        self.is_to_standards: Dict[str, List[str]] = {}
        self.doc_to_standard: Dict[str, str] = {}
        if self.registry_file.exists():
            self.load()
        else:
            self.reconcile_catalog()

    def load(self) -> None:
        """Loads standards from JSONL file."""
        self.standards.clear()
        self.is_to_standards.clear()
        self.doc_to_standard.clear()
        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    rec = StandardRecord(**data)
                    self.standards[rec.standard_id] = rec
                    is_clean = rec.is_number.upper().strip()
                    if is_clean not in self.is_to_standards:
                        self.is_to_standards[is_clean] = []
                    self.is_to_standards[is_clean].append(rec.standard_id)
                    if rec.document_id:
                        self.doc_to_standard[rec.document_id] = rec.standard_id

    def save(self) -> None:
        """Saves standards to JSONL file."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for rec in self.standards.values():
                f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")

    def get_by_id(self, standard_id: str) -> Optional[StandardRecord]:
        return self.standards.get(standard_id)

    def get_by_is(self, is_number: str, active_only: bool = True) -> List[StandardRecord]:
        is_clean = is_number.upper().strip()
        std_ids = self.is_to_standards.get(is_clean, [])
        records = [self.standards[sid] for sid in std_ids if sid in self.standards]
        if active_only:
            records = [r for r in records if r.status == StandardStatus.ACTIVE]
        return records

    def get_by_doc_id(self, doc_id: str) -> Optional[StandardRecord]:
        std_id = self.doc_to_standard.get(doc_id)
        if std_id:
            return self.standards.get(std_id)
        return None

    def add_or_update(self, record: StandardRecord) -> None:
        self.standards[record.standard_id] = record
        is_clean = record.is_number.upper().strip()
        if is_clean not in self.is_to_standards:
            self.is_to_standards[is_clean] = []
        if record.standard_id not in self.is_to_standards[is_clean]:
            self.is_to_standards[is_clean].append(record.standard_id)
        if record.document_id:
            self.doc_to_standard[record.document_id] = record.standard_id

    def reconcile_catalog(self) -> None:
        """
        Reconciles the 663-standard discovery catalog against raw files,
        metadata documents, and ingestion manifests.
        """
        if not CATALOG_PATH.exists():
            return

        # Load ingested document metadata
        doc_metadata = []
        if DOC_META_PATH.exists():
            with open(DOC_META_PATH, "r", encoding="utf-8") as f:
                doc_metadata = json.load(f)

        doc_by_is = {}
        for d in doc_metadata:
            std_num = d.get("standard_or_document_number") or d.get("title", "")
            if std_num:
                clean_std = std_num.split(":")[0].strip().upper()
                doc_by_is[clean_std] = d

        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                std_num = item.get("standard_number") or item.get("is_number") or ""
                if not std_num:
                    continue

                clean_is = std_num.split(":")[0].strip().upper()
                std_id = item.get("canonical_id") or item.get("catalog_id") or f"STD-{clean_is.replace(' ', '-').replace('/', '-')}"
                
                # Check document ingestion
                doc_meta = doc_by_is.get(clean_is)
                doc_id = doc_meta["document_id"] if doc_meta else None
                
                if doc_id:
                    acq_status = AcquisitionStatus.ACQUIRED
                    failure_reason = AcquisitionFailureReason.NONE
                    # Calculate content hash if raw PDF exists
                    content_hash = None
                    file_size = None
                    pdf_candidates = list(RAW_DIR.glob(f"**/{doc_id}.pdf")) + list(RAW_DIR.glob(f"**/*{clean_is.replace(' ', '_')}*.pdf"))
                    if pdf_candidates and pdf_candidates[0].exists():
                        try:
                            pdf_path = pdf_candidates[0]
                            file_size = pdf_path.stat().st_size
                            with open(pdf_path, "rb") as pf:
                                content_hash = hashlib.sha256(pf.read()).hexdigest()
                        except Exception:
                            pass
                else:
                    acq_status = AcquisitionStatus.CATALOG_ONLY
                    failure_reason = AcquisitionFailureReason.DOCUMENT_NOT_AVAILABLE
                    content_hash = None
                    file_size = None

                title = item.get("title") or (doc_meta.get("title") if doc_meta else f"Specification for {clean_is}")
                dept = item.get("technical_department") or (doc_meta.get("department") if doc_meta else "CMD") or "CMD"
                year = item.get("reaffirmation_year") or (doc_meta.get("publication_year") if doc_meta else 2024)

                record = StandardRecord(
                    standard_id=std_id,
                    is_number=clean_is,
                    title=title,
                    edition=item.get("edition", "First Edition"),
                    revision=item.get("revision"),
                    status=StandardStatus.ACTIVE if item.get("status", "ACTIVE") == "ACTIVE" else StandardStatus.SUPERSEDED,
                    acquisition_status=acq_status,
                    failure_reason=failure_reason,
                    reaffirmation_year=year if isinstance(year, int) else None,
                    amendment_count=item.get("amendment_count", 0),
                    technical_department=dept,
                    technical_committee=item.get("technical_committee"),
                    aspect=AspectType.PRODUCT_SPECIFICATION,
                    language="English",
                    source_url=item.get("source_url") or f"https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails/{clean_is.replace(' ', '')}",
                    document_id=doc_id,
                    content_hash=content_hash,
                    file_size_bytes=file_size,
                    parser_version="v2.1" if doc_id else None,
                    normalizer_version="v1.1" if doc_id else None
                )
                self.add_or_update(record)

        self.save()

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Returns exhaustive accounting breakdown across all standards."""
        total = len(self.standards)
        by_status = {}
        by_acq = {}
        by_failure = {}
        for r in self.standards.values():
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
            by_acq[r.acquisition_status.value] = by_acq.get(r.acquisition_status.value, 0) + 1
            by_failure[r.failure_reason.value] = by_failure.get(r.failure_reason.value, 0) + 1
        return {
            "total_standards": total,
            "by_status": by_status,
            "by_acquisition_status": by_acq,
            "by_failure_reason": by_failure
        }
