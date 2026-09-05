"""
Strict Canonical Document Identity & 4-Way Deduplication Resolver (Phase 3E).
Enforces zero-fallback identity generation, canonical field normalization, and persistent SHA-256 deduplication.
"""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PERSISTENT_REGISTRY_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "document_identity_registry.json"

logger = logging.getLogger(__name__)


def normalize_std_number(val: Optional[str]) -> Optional[str]:
    """Normalizes standard numbers (e.g. 'IS 1786 : 2008' -> '1786', '16046' -> '16046')."""
    if not val:
        return None
    s = str(val).strip()
    s = re.sub(r"^IS\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*:\s*\d{4}$", "", s)  # Strip trailing year if present in number
    s = s.strip()
    return s if s else None


def normalize_part(val: Optional[str]) -> Optional[str]:
    """Normalizes part designators (e.g. 'Part 2', 'P2', 'Part 2-1' -> '2', '2-1')."""
    if not val:
        return None
    s = str(val).strip()
    s = re.sub(r"^(?:Part|P)\s*", "", s, flags=re.IGNORECASE)
    return s.strip() if s.strip() else None


class DeduplicationDecision(BaseModel):
    """Structured decision record produced for every document undergoing deduplication review."""
    document_id: str
    document_family_id: str
    raw_sha256: str
    deduplication_status: str
    alias_of_document_ids: List[str] = Field(default_factory=list)
    identity_confidence: float = 1.0
    resolved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolution_rule: str


class IdentityResolver:
    """Canonical Identity Generator and Persistent 4-Way Deduplication Engine."""

    def __init__(self, registry_path: Path = PERSISTENT_REGISTRY_PATH):
        self.registry_path = registry_path
        self.known_id_to_hash: Dict[str, str] = {}
        self.known_hash_to_ids: Dict[str, Set[str]] = {}
        self._load_registry()

    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.known_id_to_hash = data.get("id_to_hash", {})
                    # Load 1-to-many hash to IDs
                    raw_hash_map = data.get("hash_to_ids", {})
                    self.known_hash_to_ids = {h: set(ids) for h, ids in raw_hash_map.items()}
            except Exception as e:
                logger.warning("Could not read persistent identity registry (%s), initializing empty", e)

    def persist_registry(self):
        """Persists identity and hash ledger to disk for incremental acquisition sessions."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "id_to_hash": self.known_id_to_hash,
            "hash_to_ids": {h: list(ids) for h, ids in self.known_hash_to_ids.items()}
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def generate_document_id(
        self,
        document_type: str,
        standard_number: Optional[str] = None,
        part: Optional[str] = None,
        edition_year: Optional[int] = None,
        amendment_number: Optional[int] = None,
        ministry_acronym: Optional[str] = None,
        notification_number: Optional[str] = None,
        year: Optional[int] = None,
        version_label: Optional[str] = None,
        custom_identifier: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generates canonical (document_id, document_family_id, error_reason).
        Enforces zero-fallback policy: returns None if required identity fields are missing.
        """
        dtype = document_type.upper()

        # 1. Indian Standard Specification
        if dtype in {"INDIAN_STANDARD", "STANDARD"}:
            clean_std = normalize_std_number(standard_number)
            if not clean_std:
                return None, None, "MANUAL_REVIEW: Missing or invalid standard_number"

            clean_part = normalize_part(part)
            part_suffix = f"-P{clean_part}" if clean_part else ""
            yr_suffix = f"-{edition_year}" if edition_year else ""

            doc_id = f"IS-{clean_std}{part_suffix}{yr_suffix}"
            family_id = f"IS-{clean_std}"
            return doc_id, family_id, None

        # 2. Standard Amendment Slip
        elif dtype == "AMENDMENT":
            clean_std = normalize_std_number(standard_number)
            if amendment_number is None and not custom_identifier:
                return None, None, "MANUAL_REVIEW: Missing amendment_number and custom_identifier for amendment"
            
            clean_part = normalize_part(part)
            part_suffix = f"-P{clean_part}" if clean_part else ""
            yr_suffix = f"-{edition_year}" if edition_year else ""
            
            # Use standard number if available, otherwise custom identifier or just amendment number
            if clean_std:
                doc_id = f"IS-{clean_std}{part_suffix}{yr_suffix}-A{amendment_number}"
                family_id = f"IS-{clean_std}"
            elif amendment_number is not None:
                doc_id = f"AMENDMENT-{amendment_number}{yr_suffix}"
                family_id = "AMENDMENT"
            else:
                cid = custom_identifier.strip().upper()
                doc_id = f"AMENDMENT-{cid}{yr_suffix}"
                family_id = f"AMENDMENT-{cid}"
            
            return doc_id, family_id, None

        # 3. Quality Control Order (QCO)
        elif dtype in {"QCO_NOTIFICATION", "QCO"}:
            if not notification_number and not custom_identifier:
                return None, None, "MANUAL_REVIEW: Missing gazette notification_number or custom_identifier"

            clean_min = ministry_acronym.strip().upper() if ministry_acronym else "UNKNOWN"
            
            if notification_number:
                clean_so = notification_number.strip().upper().replace(" ", "")
            else:
                clean_so = custom_identifier.strip().upper()
                
            eff_year = year or edition_year
            yr_suffix = f"-{eff_year}" if eff_year else ""

            doc_id = f"QCO-{clean_min}-{clean_so}{yr_suffix}"
            family_id = f"QCO-{clean_min}"
            return doc_id, family_id, None

        # 4. Product Manual
        elif dtype in {"PRODUCT_MANUAL", "GROUPING_GUIDELINE"}:
            clean_std = normalize_std_number(standard_number)
            yr_suffix = f"-{edition_year}" if edition_year else ""
            ver_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            
            if clean_std:
                clean_part = normalize_part(part)
                part_suffix = f"-P{clean_part}" if clean_part else ""
                doc_id = f"PM-IS-{clean_std}{part_suffix}{yr_suffix}{ver_suffix}"
                family_id = f"PM-IS-{clean_std}"
            elif custom_identifier:
                doc_id = f"PM-{custom_identifier.strip().upper()}{yr_suffix}{ver_suffix}"
                family_id = doc_id.split("-")[0]
            else:
                return None, None, "MANUAL_REVIEW: Missing standard_number and custom_identifier for product manual"
            return doc_id, family_id, None

        # 5. SIT Schedule
        elif dtype == "SIT_SCHEDULE":
            clean_std = normalize_std_number(standard_number)
            yr_suffix = f"-{edition_year}" if edition_year else ""
            rev_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            
            if clean_std:
                clean_part = normalize_part(part)
                part_suffix = f"-P{clean_part}" if clean_part else ""
                doc_id = f"SIT-IS-{clean_std}{part_suffix}{yr_suffix}{rev_suffix}"
                family_id = f"SIT-IS-{clean_std}"
            elif custom_identifier:
                doc_id = f"SIT-{custom_identifier.strip().upper()}{yr_suffix}{rev_suffix}"
                family_id = doc_id.split("-")[0]
            else:
                return None, None, "MANUAL_REVIEW: Missing standard_number and custom_identifier for SIT schedule"
            return doc_id, family_id, None

        # 6. Scheme Regulation
        elif dtype == "SCHEME_REGULATION":
            if not custom_identifier:
                return None, None, "MANUAL_REVIEW: Missing custom_identifier for scheme regulation"
            cid = custom_identifier.strip().upper()
            ver_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            doc_id = f"SCHEME-{cid}{ver_suffix}"
            family_id = f"SCHEME-{cid}"
            return doc_id, family_id, None

        # 7. Hallmarking Order
        elif dtype == "HALLMARKING_ORDER":
            if not notification_number and not custom_identifier:
                return None, None, "MANUAL_REVIEW: Missing notification_number or custom_identifier for hallmarking"
            base_id = notification_number.strip().upper().replace(" ", "") if notification_number else custom_identifier.strip().upper()
            eff_year = year or edition_year
            yr_suffix = f"-{eff_year}" if eff_year else ""
            doc_id = f"HM-{base_id}{yr_suffix}"
            family_id = f"HM-{base_id}"
            return doc_id, family_id, None

        # 8. Act / Rule / Regulation
        elif dtype in {"ACT", "RULE", "REGULATION"}:
            if not custom_identifier:
                return None, None, f"MANUAL_REVIEW: Missing custom_identifier (title) for {dtype}"
            cid = custom_identifier.strip().upper()
            eff_year = year or edition_year
            yr_suffix = f"-{eff_year}" if eff_year else ""
            ver_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            doc_id = f"{dtype}-{cid}{yr_suffix}{ver_suffix}"
            family_id = f"{dtype}-{cid}"
            return doc_id, family_id, None

        # 9. FAQ / Guide / Booklet / Consumer Document / Technical Guideline
        elif dtype in {"FAQ", "GUIDE", "BOOKLET", "CONSUMER_DOCUMENT", "TECHNICAL_GUIDELINE"}:
            if not custom_identifier:
                return None, None, f"MANUAL_REVIEW: Missing custom_identifier (title) for {dtype}"
            cid = custom_identifier.strip().upper()
            eff_year = year or edition_year
            yr_suffix = f"-{eff_year}" if eff_year else ""
            ver_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            doc_id = f"GUIDE-{cid}{yr_suffix}{ver_suffix}"
            family_id = f"GUIDE-{cid}"
            return doc_id, family_id, None

        # 10. Laboratory Scope
        elif dtype == "LABORATORY_SCOPE":
            if not custom_identifier:
                return None, None, "MANUAL_REVIEW: Missing lab code for laboratory scope"
            cid = custom_identifier.strip().upper()
            ver_suffix = f"-{version_label.strip().upper()}" if version_label else ""
            doc_id = f"LAB-{cid}{ver_suffix}"
            family_id = f"LAB-{cid}"
            return doc_id, family_id, None

        # 11. Custom or Specific Statutory Identifier
        elif custom_identifier and custom_identifier.strip():
            cid = custom_identifier.strip().upper()
            return cid, cid.split("-")[0], None

        return None, None, f"MANUAL_REVIEW: Unsupported document_type '{document_type}' and missing required fields"

    def resolve_deduplication(
        self,
        document_id: str,
        document_family_id: str,
        raw_sha256: str
    ) -> DeduplicationDecision:
        """
        Evaluates 4-way deduplication logic against persistent registry:
        1. Same ID + Same Hash -> UNCHANGED_DOCUMENT
        2. Same ID + Different Hash -> CONTENT_CHANGED_REQUIRES_VERSION_REVIEW
        3. Different ID + Same Hash -> DUPLICATE_REPRESENTATION_ALIAS
        4. New ID + New Hash -> DISTINCT_DOCUMENT
        """
        existing_hash = self.known_id_to_hash.get(document_id)
        existing_ids_for_hash = self.known_hash_to_ids.get(raw_sha256, set())

        # 1. Same ID + Same Hash
        if existing_hash and existing_hash == raw_sha256:
            return DeduplicationDecision(
                document_id=document_id,
                document_family_id=document_family_id,
                raw_sha256=raw_sha256,
                deduplication_status="UNCHANGED_DOCUMENT",
                resolution_rule="SAME_ID_SAME_SHA256"
            )

        # 2. Same ID + Different Hash
        elif existing_hash and existing_hash != raw_sha256:
            # Does NOT overwrite automatically; flags for review
            return DeduplicationDecision(
                document_id=document_id,
                document_family_id=document_family_id,
                raw_sha256=raw_sha256,
                deduplication_status="CONTENT_CHANGED_REQUIRES_VERSION_REVIEW",
                resolution_rule="SAME_ID_DIFFERENT_SHA256_VERSION_REVIEW"
            )

        # 3. Different ID + Same Hash
        elif len(existing_ids_for_hash) > 0 and document_id not in existing_ids_for_hash:
            # Add new ID to the 1-to-many alias set
            self.known_id_to_hash[document_id] = raw_sha256
            self.known_hash_to_ids[raw_sha256].add(document_id)
            self.persist_registry()
            return DeduplicationDecision(
                document_id=document_id,
                document_family_id=document_family_id,
                raw_sha256=raw_sha256,
                deduplication_status="DUPLICATE_REPRESENTATION_ALIAS",
                alias_of_document_ids=list(existing_ids_for_hash),
                resolution_rule="DIFFERENT_ID_SAME_SHA256_ALIAS"
            )

        # 4. New Distinct Document
        else:
            self.known_id_to_hash[document_id] = raw_sha256
            if raw_sha256 not in self.known_hash_to_ids:
                self.known_hash_to_ids[raw_sha256] = set()
            self.known_hash_to_ids[raw_sha256].add(document_id)
            self.persist_registry()
            return DeduplicationDecision(
                document_id=document_id,
                document_family_id=document_family_id,
                raw_sha256=raw_sha256,
                deduplication_status="DISTINCT_DOCUMENT",
                resolution_rule="NEW_CANONICAL_IDENTITY_AND_PAYLOAD"
            )
