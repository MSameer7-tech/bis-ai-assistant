#!/usr/bin/env python3
"""
Multi-Source Discovery Engine Orchestrator (Phase 3A-Cleanup).
Dispatches queries across all 18 registered official BIS endpoints to modular dynamic strategies.
Produces dry-run reports, per-source metrics, candidate catalogs, and discovery run reports without downloading.
Preserves cross-document relationships (Standard <-> Amendment, Standard <-> QCO, Standard <-> Manual, etc.).
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

REGISTRY_PATH = ROOT_DIR / "data" / "sources" / "source_registry.json"
CANDIDATES_PATH = ROOT_DIR / "data" / "candidates" / "candidate_documents.json"
REPORT_PATH = ROOT_DIR / "data" / "candidates" / "discovery_run_report.json"

from ai.acquisition.discovery.base import BaseDiscoveryStrategy, DiscoveryMetrics
from ai.acquisition.discovery.html_search import HTMLSearchStrategy
from ai.acquisition.discovery.html_catalog import HTMLCatalogStrategy
from ai.acquisition.discovery.pdf_links import PDFLinkDiscoveryStrategy
from ai.acquisition.discovery.gazette_search import GazetteSearchStrategy
from ai.acquisition.discovery.registry_query import RegistryQueryStrategy
from ai.acquisition.discovery.direct_html import DirectHTMLStrategy
from ai.acquisition.discovery.query_driven import QueryDrivenStrategy
from ai.acquisition.discovery.api_interceptor import APIInterceptorStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscoveryEngine")


class CandidateDocument(BaseModel):
    """Normalized data contract for a candidate document discovered from an official source endpoint."""
    candidate_id: str = Field(..., description="Unique candidate identifier, e.g. CAND-IS-1786-2008")
    source_id: str = Field(..., description="Source endpoint ID where discovered (e.g. SRC-001)")
    source_family_id: str = Field(..., description="Governing source family ID (e.g. SRCF-001)")
    source_url: str = Field(..., description="Target download/extraction raw machine-readable URL")
    discovered_from_url: str = Field(..., description="Parent catalog or search page URL where discovered")
    document_type: str = Field(..., description="Classification (e.g. INDIAN_STANDARD, QCO_NOTIFICATION, ACT, RULE, REGULATION)")
    title: str = Field(..., description="Discovered formal document title")
    standard_number: Optional[str] = Field(None, description="Extracted standard number (e.g. '1786', '16046')")
    part: Optional[str] = Field(None, description="Extracted part identifier (e.g. '1', '2')")
    edition_year: Optional[int] = Field(None, description="Edition publication year")
    discovery_method: str = Field(..., description="Discovery protocol used (e.g. HTML_CATALOG, SEARCH_ENDPOINT)")
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    associated_product_keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Relationship metadata (Phase 3 Cleanup)
    related_standard_id: Optional[str] = Field(None, description="Related Indian Standard document family ID (e.g. IS-1786)")
    parent_document_id: Optional[str] = Field(None, description="Parent document ID for amendments, manuals, SIT schedules")
    relationship_type: Optional[str] = Field(None, description="Relationship to parent (AMENDS, CERTIFICATION_GUIDELINE_FOR, TESTING_SCHEDULE_FOR, MANDATES_CERTIFICATION_FOR, etc.)")
    related_qco_ids: List[str] = Field(default_factory=list, description="Related QCO notification IDs")
    related_licence_ids: List[str] = Field(default_factory=list, description="Related licence record IDs")
    related_lab_ids: List[str] = Field(default_factory=list, description="Related laboratory IDs")
    discovery_evidence: Optional[Dict[str, Any]] = Field(None, description="DOM structural discovery evidence")


class DiscoveryEngine:
    """Orchestrates dynamic discovery strategies across all registered source endpoints."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path
        self.sources_by_id = self._load_registry()
        self.strategies: Dict[str, BaseDiscoveryStrategy] = {
            "HTML_SEARCH": HTMLSearchStrategy(timeout=30.0),
            "HTML_CATALOG": HTMLCatalogStrategy(timeout=30.0),
            "PDF_LINK_DISCOVERY": PDFLinkDiscoveryStrategy(timeout=30.0),
            "SEARCH_ENDPOINT": GazetteSearchStrategy(timeout=15.0),
            "REGISTRY_QUERY": RegistryQueryStrategy(timeout=15.0),
            "DIRECT_HTML": DirectHTMLStrategy(timeout=30.0),
            "QUERY_DRIVEN": QueryDrivenStrategy(timeout=30.0),
            "API_INTERCEPTOR": APIInterceptorStrategy(timeout=30.0)
        }

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if not self.registry_path.exists():
            return {}
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {s["source_id"]: s for s in data.get("sources", [])}

    def discover_from_endpoint(self, source_id: str) -> Tuple[List[CandidateDocument], DiscoveryMetrics]:
        """Dispatches discovery for a specific registered source endpoint to its matching strategy."""
        source = self.sources_by_id.get(source_id)
        if not source:
            logger.warning("Source ID %s not found in registry", source_id)
            return [], DiscoveryMetrics(source_id=source_id, access_method="UNKNOWN")

        # Handle session-gated or explicitly unavailable sources
        status = source.get("status", "ACTIVE")
        if status in ("SESSION_REQUIRED", "ENDPOINT_UNAVAILABLE", "MANUAL_DISCOVERY_REQUIRED"):
            logger.info("Handling %s with status=%s", source_id, status)
            metrics = DiscoveryMetrics(
                source_id=source_id,
                source_family_id=source.get("source_family_id", ""),
                access_method=source.get("access_method", "UNKNOWN")
            )
            metrics.source_errors.append(f"Status is {status}: Direct unauthenticated crawling restricted by portal.")
            metrics.end_time = datetime.now(timezone.utc).isoformat()
            return [], metrics

        access_method = source.get("access_method", "DIRECT_HTML")
        strategy = self.strategies.get(access_method, DirectHTMLStrategy())
        return strategy.discover(source)

    def discover_all_candidates(self, save_catalog: bool = False) -> List[CandidateDocument]:
        """Runs discovery across all registered endpoints, collects metrics, and optionally saves outputs."""
        all_candidates: List[CandidateDocument] = []
        metrics_list: List[DiscoveryMetrics] = []
        seen_candidate_ids = set()

        for src_id, src in self.sources_by_id.items():
            candidates, metrics = self.discover_from_endpoint(src_id)

            filtered_candidates = []
            for cand in candidates:
                if cand.candidate_id in seen_candidate_ids or "employees[" in cand.candidate_id:
                    metrics.duplicates_removed += 1
                    continue
                seen_candidate_ids.add(cand.candidate_id)
                filtered_candidates.append(cand)

            all_candidates.extend(filtered_candidates)
            metrics_list.append(metrics)

        # Persist candidate catalog only if explicitly requested
        if save_catalog:
            CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in all_candidates], f, indent=2)

        # Persist discovery run report
        report = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_endpoints_queried": len(self.sources_by_id),
            "total_unique_candidates": len(all_candidates),
            "endpoint_metrics": [m.model_dump() for m in metrics_list]
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info("Discovered %d candidate documents across %d endpoints", len(all_candidates), len(self.sources_by_id))
        return all_candidates

    def generate_dry_run_report(self) -> Dict[str, Any]:
        """Executes dry-run discovery and returns structured coverage report."""
        candidates = self.discover_all_candidates()
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        # Group by Document Type
        type_distribution: Dict[str, int] = {}
        for c in candidates:
            type_distribution[c.document_type] = type_distribution.get(c.document_type, 0) + 1

        report_data["document_type_distribution"] = type_distribution

        # Group by source status and endpoint
        source_details = {}
        for src_id, src in self.sources_by_id.items():
            source_details[src_id] = {
                "source_name": src.get("source_name", ""),
                "canonical_url": src.get("canonical_url", ""),
                "status": src.get("status", "ACTIVE"),
                "access_method": src.get("access_method", "")
            }
        report_data["source_details"] = source_details

        return report_data


def print_dry_run_table(report: Dict[str, Any]):
    """Renders comprehensive formatted console output for the DOM-aware exhaustive dry-run discovery audit."""
    print("\n" + "=" * 160)
    print("                    BIS CORPUS EXHAUSTIVE DOM-AWARE DISCOVERY REPORT (DRY-RUN) — Phase 3")
    print("=" * 160)
    header = (
        f"{'Source':<8} | {'Status':<16} | {'Method':<16} | "
        f"{'Visited':<7} | {'DOM Elm':<7} | {'Raw Lnk':<7} | {'Doc Reg':<7} | {'Docs':<5} | {'Struct':<6} | {'NavExcl':<7} | {'Dups':<5} | {'Valid':<5} | "
        f"{'Exhaustion Reason'}"
    )
    print(header)
    print("-" * 160)

    total_visited = 0
    total_dom_elm = 0
    total_raw_lnk = 0
    total_doc_reg = 0
    total_docs = 0
    total_struct = 0
    total_navexcl = 0
    total_dups = 0
    total_valid = 0

    source_details = report.get("source_details", {})

    for m in report.get("endpoint_metrics", []):
        sid = m.get("source_id", "")
        sinfo = source_details.get(sid, {})
        status = sinfo.get("status", "ACTIVE")
        method = m.get("access_method", sinfo.get("access_method", ""))

        dom_m = m.get("dom_metrics") or {}
        fm = m.get("filter_metrics") or {}

        visited = m.get("pages_visited", m.get("pages_processed", 1))
        dom_elm = dom_m.get("raw_dom_elements", 0)
        raw_lnk = dom_m.get("raw_links", fm.get("raw_links", m.get("records_discovered", 0)))
        doc_reg = dom_m.get("document_regions", 1 if m.get("records_discovered", 0) > 0 else 0)
        docs = m.get("documents_discovered", m.get("records_discovered", 0))
        struct = m.get("structured_records_discovered", 0)
        navexcl = dom_m.get("navigation_links_excluded", fm.get("excluded_navigation", 0))
        dups = m.get("duplicates_removed", 0)
        valid = max(0, m.get("records_discovered", 0) - dups)
        exhaust_reason = m.get("exhaustion_reason", "PAGINATION_EXHAUSTED")

        total_visited += visited
        total_dom_elm += dom_elm
        total_raw_lnk += raw_lnk
        total_doc_reg += doc_reg
        total_docs += docs
        total_struct += struct
        total_navexcl += navexcl
        total_dups += dups
        total_valid += valid

        print(
            f"{sid:<8} | "
            f"{status:<16} | "
            f"{method:<16} | "
            f"{visited:<7} | "
            f"{dom_elm:<7} | "
            f"{raw_lnk:<7} | "
            f"{doc_reg:<7} | "
            f"{docs:<5} | "
            f"{struct:<6} | "
            f"{navexcl:<7} | "
            f"{dups:<5} | "
            f"{valid:<5} | "
            f"{exhaust_reason}"
        )

    print("=" * 160)
    print(
        f"{'TOTALS':<44} | "
        f"{total_visited:<7} | "
        f"{total_dom_elm:<7} | "
        f"{total_raw_lnk:<7} | "
        f"{total_doc_reg:<7} | "
        f"{total_docs:<5} | "
        f"{total_struct:<6} | "
        f"{total_navexcl:<7} | "
        f"{total_dups:<5} | "
        f"{total_valid:<5} |"
    )
    print("=" * 160)

    print("\nDOCUMENT & RECORD TYPE DISTRIBUTION:")
    for dtype, count in sorted(report.get("document_type_distribution", {}).items()):
        print(f"  {dtype:<35} : {count}")

    print(f"\nTOTAL UNIQUE CANDIDATES DISCOVERED: {report.get('total_unique_candidates', 0)}")
    print(f"REPORT SAVED TO: {REPORT_PATH}\n")


def main():
    parser = argparse.ArgumentParser(description="BIS Corpus Discovery Engine")
    parser.add_argument("--dry-run", action="store_true", help="Run discovery in dry-run mode and output metrics report")
    args = parser.parse_args()

    engine = DiscoveryEngine()
    report = engine.generate_dry_run_report()

    if args.dry_run:
        print_dry_run_table(report)


if __name__ == "__main__":
    main()
