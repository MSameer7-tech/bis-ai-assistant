"""
Phase 4 Batch A: Master BIS Source Registry & Coverage Matrix Management.
Defines authoritative source families, priority tiers, update strategies, and
multi-stage coverage tracking (Discovered -> Accessible -> Acquired -> Parsed -> Normalized -> Indexed).
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SOURCES_REGISTRY_PATH = ROOT_DIR / "data" / "registry" / "sources.jsonl"


class SourcePriority(str, Enum):
    TIER_1A = "TIER_1A"  # Normative Indian Standards
    TIER_1B = "TIER_1B"  # Gazette Notifications & QCOs
    TIER_1C = "TIER_1C"  # BIS Product Manuals & SITs
    TIER_1D = "TIER_1D"  # Recognized Laboratories & Licences
    TIER_2 = "TIER_2"    # Procedural Guidelines, Schemes & Consumer Portals
    TIER_3 = "TIER_3"    # Administrative & Training Services


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REACHABLE = "REACHABLE"
    RESTRICTED = "RESTRICTED"
    DEGRADED = "DEGRADED"
    PLANNED = "PLANNED"


class UpdateStrategy(str, Enum):
    DAILY_INCREMENTAL = "daily_incremental"
    WEEKLY_POLL = "weekly_poll"
    MONTHLY_RECONCILIATION = "monthly_reconciliation"
    ON_GAZETTE_EVENT = "on_gazette_event"
    EVENT_DRIVEN = "event_driven"


class SourceCoverageMetrics(BaseModel):
    """Multi-stage acquisition & indexing coverage metrics for an individual source."""
    discovered: int = Field(default=0, ge=0, description="Total entity records discovered on the portal")
    accessible: int = Field(default=0, ge=0, description="Records whose documents/endpoints are publicly accessible")
    acquired: int = Field(default=0, ge=0, description="Raw records/PDFs downloaded and cryptographically validated")
    parsed: int = Field(default=0, ge=0, description="Records successfully extracted into structured text/clauses")
    normalized: int = Field(default=0, ge=0, description="Records conforming to canonical BIS domain schemas")
    indexed: int = Field(default=0, ge=0, description="Records fully indexed into BM25 and Vector Search stores")
    last_checked: Optional[str] = Field(default=None, description="ISO timestamp of last health check/scrape attempt")
    last_success: Optional[str] = Field(default=None, description="ISO timestamp of last successful acquisition")
    status: SourceStatus = Field(default=SourceStatus.ACTIVE, description="Current operational status of endpoint")


class SourceRecord(BaseModel):
    """Authoritative representation of a registered BIS source portal / service."""
    source_id: str = Field(..., description="Unique immutable source identifier (e.g. 'BIS-KYS')")
    source_family: str = Field(..., description="Canonical source family category")
    name: str = Field(..., description="Human-readable portal/registry name")
    authority: str = Field(..., description="Issuing authority, department, or line ministry")
    source_type: str = Field(..., description="Type of source portal (official_portal, statutory_register, etc.)")
    base_url: str = Field(..., description="Verified official base URL")
    search_endpoint: Optional[str] = Field(default=None, description="Search or discovery API/URL endpoint")
    discovery_method: str = Field(..., description="Mechanism used to discover entities")
    priority: SourcePriority = Field(default=SourcePriority.TIER_1A, description="Normative authority tier")
    enabled: bool = Field(default=True, description="Whether this source is actively enabled for acquisition")
    update_strategy: UpdateStrategy = Field(default=UpdateStrategy.DAILY_INCREMENTAL, description="Polling schedule")
    description: str = Field(..., description="Detailed description of what this source provides")
    coverage: SourceCoverageMetrics = Field(default_factory=SourceCoverageMetrics, description="Live coverage metrics")

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^BIS-[A-Z0-9_\-]+$", clean):
            raise ValueError(f"source_id '{v}' must match pattern '^BIS-[A-Z0-9_\\-]+$'")
        return clean

    @field_validator("base_url", "search_endpoint")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not (clean.startswith("http://") or clean.startswith("https://")):
            raise ValueError(f"URL '{v}' must begin with http:// or https://")
        return clean


class SourceRegistry:
    """Manages all registered official BIS sources and tracks multi-stage coverage."""

    def __init__(self, registry_path: Path = SOURCES_REGISTRY_PATH):
        self.registry_path = Path(registry_path)
        self._sources: Dict[str, SourceRecord] = {}
        self.load()

    def load(self) -> None:
        """Loads source records from JSONL registry file."""
        self._sources.clear()
        if not self.registry_path.exists():
            logger.warning("Sources registry path %s does not exist. Initializing empty.", self.registry_path)
            return

        with open(self.registry_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = SourceRecord(**data)
                    self._sources[record.source_id] = record
                except Exception as e:
                    logger.error("Error parsing sources.jsonl line %d: %s", line_num, e)

    def save(self) -> None:
        """Persists all sources back to JSONL registry file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            for source in sorted(self._sources.values(), key=lambda s: (s.priority.value, s.source_id)):
                f.write(json.dumps(source.model_dump(), ensure_ascii=False) + "\n")

    def register_source(self, record: SourceRecord) -> None:
        """Adds or updates a source record in the registry."""
        self._sources[record.source_id] = record
        self.save()

    def get_source(self, source_id: str) -> Optional[SourceRecord]:
        """Retrieves a source record by its unique ID."""
        return self._sources.get(source_id.strip().upper())

    def list_sources(self, enabled_only: bool = False, family: Optional[str] = None) -> List[SourceRecord]:
        """Lists sources with optional filtering."""
        results = list(self._sources.values())
        if enabled_only:
            results = [s for s in results if s.enabled]
        if family:
            results = [s for s in results if s.source_family.lower() == family.strip().lower()]
        return sorted(results, key=lambda s: (s.priority.value, s.source_id))

    def update_coverage(
        self,
        source_id: str,
        discovered: Optional[int] = None,
        accessible: Optional[int] = None,
        acquired: Optional[int] = None,
        parsed: Optional[int] = None,
        normalized: Optional[int] = None,
        indexed: Optional[int] = None,
        status: Optional[SourceStatus] = None,
        success: bool = True
    ) -> SourceRecord:
        """Updates multi-stage coverage counts and timestamps for a specific source."""
        source = self.get_source(source_id)
        if not source:
            raise KeyError(f"Source with ID '{source_id}' not found in registry")

        now_iso = datetime.now(timezone.utc).isoformat()
        source.coverage.last_checked = now_iso
        if success:
            source.coverage.last_success = now_iso

        if discovered is not None:
            source.coverage.discovered = discovered
        if accessible is not None:
            source.coverage.accessible = accessible
        if acquired is not None:
            source.coverage.acquired = acquired
        if parsed is not None:
            source.coverage.parsed = parsed
        if normalized is not None:
            source.coverage.normalized = normalized
        if indexed is not None:
            source.coverage.indexed = indexed
        if status is not None:
            source.coverage.status = status

        self.save()
        return source

    def generate_coverage_matrix_table(self) -> str:
        """Generates a markdown table of the Source Coverage Matrix across all source families."""
        headers = ["Source ID", "Source Family", "Priority", "Discovered", "Accessible", "Acquired", "Parsed", "Normalized", "Indexed", "Status"]
        rows = []
        for s in sorted(self._sources.values(), key=lambda x: (x.priority.value, x.source_id)):
            c = s.coverage
            rows.append([
                s.source_id,
                s.source_family,
                s.priority.value,
                str(c.discovered),
                str(c.accessible),
                str(c.acquired),
                str(c.parsed),
                str(c.normalized),
                str(c.indexed),
                c.status.value
            ])

        col_widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        sep_line = "-|-".join("-" * col_widths[i] for i in range(len(headers)))
        data_lines = [" | ".join(r[i].ljust(col_widths[i]) for i in range(len(headers))) for r in rows]

        return f"| {header_line} |\n| {sep_line} |\n" + "\n".join(f"| {dl} |" for dl in data_lines)
