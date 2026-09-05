"""
Regulatory Timeline & Temporal Reasoning Engine (Phase 5 Sub-Phase 5E).
Tracks historical editions, gazette notifications, QCO effective dates, amendments,
and resolves legally active regulatory requirements as of any historical timestamp.
"""
import re
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from ai.acquisition.standards.registry import StandardsRegistry
from ai.acquisition.qco.registry import QCORegistry
from ai.acquisition.amendments.registry import AmendmentsRegistry
from ai.acquisition.gazette.registry import GazetteRegistry
from ai.acquisition.provenance.registry import EvidenceRegistry

logger = logging.getLogger(__name__)


class TimelineEvent(BaseModel):
    """A discrete regulatory or publication milestone."""
    date: str  # YYYY-MM-DD
    event_type: str  # FIRST_PUBLICATION, REVISION, AMENDMENT, QCO_ISSUED, QCO_ENFORCED, REAFFIRMED, SUPERSEDED
    title: str
    description: str
    citation: Optional[str] = None
    is_active_as_of: bool = True
    document_id: Optional[str] = None


class TimelineResult(BaseModel):
    """Complete temporal history and point-in-time regulatory status."""
    standard_or_product: str
    target_date: str
    active_standard_edition: str
    active_standard_title: str
    is_currently_active: bool
    active_qco: Optional[str] = None
    qco_enforced_as_of_target: bool = False
    events: List[TimelineEvent] = Field(default_factory=list)
    superseded_by: Optional[str] = None
    temporal_warning: Optional[str] = None


class RegulatoryTimelineEngine:
    """
    Constructs chronological regulatory timelines and determines active legal state.
    """
    def __init__(self):
        self.std_reg = StandardsRegistry()
        self.qco_reg = QCORegistry()
        self.amend_reg = AmendmentsRegistry()
        self.gazette_reg = GazetteRegistry()
        self.evidence_reg = EvidenceRegistry()

    def resolve_timeline(self, standard_or_product: str, as_of_date: Optional[str] = None) -> TimelineResult:
        """
        Builds chronological timeline and evaluates legal applicability as of `as_of_date`.
        """
        target_dt_str = as_of_date or date.today().isoformat()
        try:
            target_dt = datetime.fromisoformat(target_dt_str.split("T")[0])
        except Exception:
            target_dt = datetime.now()

        clean_query = standard_or_product.upper().strip()
        clean_num = clean_query.split(":")[0].strip()

        # 1. Gather all standard records / editions
        matching_stds = [s for s in self.std_reg.standards.values() if clean_num in s.is_number.upper()]
        matching_stds.sort(key=lambda x: str(x.edition or "1900"))

        events: List[TimelineEvent] = []

        active_edition = None
        active_title = None
        superseded_by = None
        is_active = True

        for std in matching_stds:
            year_match = re.search(r"\b(19\d\d|20[0-2]\d)\b", f"{std.edition} {std.title}")
            year_val = year_match.group(1) if year_match else "2019"
            pub_date = f"{year_val}-01-01"
            is_withdrawn = std.status.value.upper() in ("WITHDRAWN", "SUPERSEDED")

            event_type = "REVISION" if std.revision else "FIRST_PUBLICATION"
            events.append(TimelineEvent(
                date=pub_date,
                event_type=event_type,
                title=f"{std.is_number}:{year_val} Publication",
                description=f"Standard published as: {std.title} ({std.status.value})",
                citation=f"Indian Standard {std.is_number} : {year_val}",
                is_active_as_of=(pub_date <= target_dt_str and not is_withdrawn),
                document_id=std.document_id
            ))

            if pub_date <= target_dt_str:
                active_edition = f"{std.is_number}:{year_val}"
                active_title = std.title
                if is_withdrawn:
                    is_active = False

        if not matching_stds:
            active_edition = clean_query
            active_title = f"Standard {clean_query}"

        # 2. Gather Amendments
        amendments = self.amend_reg.get_by_standard(clean_num)
        for amend in amendments:
            a_date = amend.effective_date or amend.gazette_date or "2020-01-01"
            events.append(TimelineEvent(
                date=a_date,
                event_type="AMENDMENT",
                title=f"Amendment No. {amend.amendment_number} ({amend.is_number})",
                description=f"Amendment modification: {amend.summary or 'Normative clause update'}",
                citation=amend.gazette_notification_number or f"Amendment {amend.amendment_number}",
                is_active_as_of=(a_date <= target_dt_str),
                document_id=amend.amendment_id
            ))

        # 3. Gather Quality Control Orders (QCOs)
        qcos = self.qco_reg.get_by_standard(clean_num)
        active_qco_title = None
        qco_enforced = False

        for qco in qcos:
            pub_d = qco.publication_date or "2020-01-01"
            eff_d = qco.effective_date or pub_d
            
            events.append(TimelineEvent(
                date=pub_d,
                event_type="QCO_ISSUED",
                title=f"QCO Gazette Publication: {qco.title}",
                description=f"Notified by {qco.issuing_authority} under {qco.notification_number}",
                citation=f"{qco.issuing_authority}, Notification {qco.notification_number}",
                is_active_as_of=(pub_d <= target_dt_str),
                document_id=qco.document_id
            ))

            if eff_d != pub_d:
                events.append(TimelineEvent(
                    date=eff_d,
                    event_type="QCO_ENFORCED",
                    title=f"QCO Legal Enforcement Date: {qco.title}",
                    description=f"Mandatory BIS certification became enforceable for all manufacturers/importers",
                    citation=f"Notification {qco.notification_number} Effective Date",
                    is_active_as_of=(eff_d <= target_dt_str),
                    document_id=qco.document_id
                ))

            if eff_d <= target_dt_str:
                active_qco_title = qco.title
                qco_enforced = True

        # Sort all events chronologically
        events.sort(key=lambda x: x.date)

        # 4. Temporal Warning & Supersession Resolution
        temporal_warning = None
        if not is_active:
            temporal_warning = f"⚠️ [SUPERSEDED] The edition requested ({active_edition}) is superseded. Refer to current standard edition."
        elif target_dt.year < 2024 and qco_enforced:
            temporal_warning = f"ℹ️ [HISTORICAL STATE] Viewing requirements as of {target_dt.strftime('%d %b %Y')}."

        return TimelineResult(
            standard_or_product=clean_query,
            target_date=target_dt_str,
            active_standard_edition=active_edition or clean_query,
            active_standard_title=active_title or clean_query,
            is_currently_active=is_active,
            active_qco=active_qco_title,
            qco_enforced_as_of_target=qco_enforced,
            events=events,
            superseded_by=superseded_by,
            temporal_warning=temporal_warning
        )
