#!/usr/bin/env python3
"""
Phase 6A: BIS Site-Wide Catalog Discovery & Universe Enumeration.
Orchestrates modular source adapters across all 9 source families and 12 Technical Departments:
- StandardsCatalogAdapter (standardsbis.bsbedge.com)
- KnowYourStandardAdapter (services.bis.gov.in)
- ProductManualsAdapter (CMD manuals)
- SITAdapter (Inspection & Testing Schemes)
- QCOAdapter (Gazette Notifications & Orders)
- LaboratoriesAdapter (Testing Lab Network)
- CommitteesAdapter (Division Councils & Committees)

Outputs:
- data/registry/bis_sources.jsonl
- data/registry/standards_catalog.jsonl (with canonical IDs, metadata completeness, and coverage status)
- data/registry/document_manifest.jsonl
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"

from ai.acquisition.sources.bis_catalog_adapter import BIS_SOURCE_FAMILIES
from ai.acquisition.sources.standards_catalog import StandardsCatalogAdapter
from ai.acquisition.sources.know_your_standard import KnowYourStandardAdapter
from ai.acquisition.sources.product_manuals import ProductManualsAdapter
from ai.acquisition.sources.sit import SITAdapter
from ai.acquisition.sources.qco import QCOAdapter
from ai.acquisition.sources.laboratories import LaboratoriesAdapter
from ai.acquisition.sources.committees import CommitteesAdapter
from ai.acquisition.deduplicator import CrossSourceDeduplicator


def discover_universe(dry_run: bool = False) -> Dict[str, Any]:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting Modular BIS Universe Discovery across 9 Source Families...")

    # 1. Emit Source Registry
    sources_file = REGISTRY_DIR / "bis_sources.jsonl"
    with open(sources_file, "w", encoding="utf-8") as sf:
        for k, v in BIS_SOURCE_FAMILIES.items():
            sf.write(json.dumps(v, ensure_ascii=False) + "\n")

    # 2. Run Modular Adapters
    adapters = [
        StandardsCatalogAdapter(),
        KnowYourStandardAdapter(),
        ProductManualsAdapter(),
        SITAdapter(),
        QCOAdapter(),
        LaboratoriesAdapter(),
        CommitteesAdapter()
    ]

    deduplicator = CrossSourceDeduplicator()

    for adp in adapters:
        logger.info(f"  • Running adapter: {adp.source_name}...")
        records = adp.emit()
        logger.info(f"      Emitted {len(records)} candidate records.")
        for r in records:
            deduplicator.add_record(r)

    catalog_entities = list(deduplicator.entities.values())
    logger.info(f"✅ Total Deduplicated Universe Entities: {len(catalog_entities)}")

    # 3. Build Document Manifest (Candidate documents)
    doc_candidates = []
    doc_counter = 1
    for item in catalog_entities:
        if item.get("has_document") and item.get("document_url"):
            doc_candidates.append({
                "document_id": f"DOC-CAND-{doc_counter:04d}",
                "canonical_id": item.get("canonical_id"),
                "catalog_id": item.get("catalog_id"),
                "entity_type": item.get("entity_type"),
                "standard_number": item.get("standard_number"),
                "edition": item.get("edition"),
                "title": item.get("title"),
                "download_url": item.get("document_url"),
                "source_name": item.get("discovery_source"),
                "discovered_at": datetime.now().isoformat(),
                "priority_rank": 1 if item.get("entity_type") == "standard" else 2
            })
            doc_counter += 1

    if not dry_run:
        # Write standards_catalog.jsonl
        catalog_file = REGISTRY_DIR / "standards_catalog.jsonl"
        with open(catalog_file, "w", encoding="utf-8") as cf:
            for ent in catalog_entities:
                cf.write(json.dumps(ent, ensure_ascii=False) + "\n")
        logger.info(f"Saved catalog to: {catalog_file}")

        # Write document_manifest.jsonl
        manifest_file = REGISTRY_DIR / "document_manifest.jsonl"
        with open(manifest_file, "w", encoding="utf-8") as mf:
            for doc in doc_candidates:
                mf.write(json.dumps(doc, ensure_ascii=False) + "\n")
        logger.info(f"Saved document manifest to: {manifest_file}")

    print("\n" + "=" * 80)
    print(f"🌐 BIS UNIVERSE DISCOVERY SUMMARY {'(DRY RUN)' if dry_run else ''}")
    print("=" * 80)
    print(f"Total Deduplicated Entities:  {len(catalog_entities):>6d}")
    print(f"Downloadable Candidate URLs:  {len(doc_candidates):>6d}")
    print("=" * 80 + "\n")

    return {
        "total_entities": len(catalog_entities),
        "document_candidates": len(doc_candidates)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover BIS Catalog Universe")
    parser.add_argument("--dry-run", action="store_true", help="Perform discovery without writing files")
    args = parser.parse_args()
    discover_universe(dry_run=args.dry_run)
