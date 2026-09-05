#!/usr/bin/env python3
"""
EvidenceUnit Duplicate & Short Unit Auditor.
Analyzes exact duplicates and short units to determine whether they are extraction artifacts or legitimate content.
"""
import json
import logging
import sys
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DuplicateAuditor")

EVIDENCE_UNITS_ROOT = ROOT_DIR / "data" / "processed" / "evidence_units"
AUDIT_JSON_PATH = ROOT_DIR / "data" / "processed" / "evidence_duplicate_audit.json"
AUDIT_MD_PATH = ROOT_DIR / "docs" / "phase5" / "evidence_duplicate_audit.md"
SOURCE_FAMILIES_PATH = ROOT_DIR / "data" / "sources" / "source_families.json"

def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def normalize_text(text: str) -> str:
    import re
    return re.sub(r'\s+', ' ', text).strip().lower()

def run_duplicate_audit():
    logger.info("🔍 Starting Duplicate and Short Unit Audit...")

    exact_groups = defaultdict(list)
    near_groups = defaultdict(list)
    short_units = []

    total_units = 0

    for doc_dir in EVIDENCE_UNITS_ROOT.iterdir():
        if not doc_dir.is_dir():
            continue
            
        unit_file = doc_dir / "evidence_units.json"
        if not unit_file.exists():
            continue
            
        with open(unit_file, "r", encoding="utf-8") as f:
            units = json.load(f)
            
        for unit in units:
            total_units += 1
            text = unit.get("content_text", "")
            
            # Short unit detection
            if len(text.strip()) < 10:
                short_units.append(unit)
                
            # Exact duplicate grouping
            e_hash = compute_hash(text)
            exact_groups[e_hash].append(unit)
            
            # Near duplicate grouping
            n_text = normalize_text(text)
            if n_text:
                n_hash = compute_hash(n_text)
                near_groups[n_hash].append(unit)

    # Filter out non-duplicates (groups of size 1)
    exact_dups = {k: v for k, v in exact_groups.items() if len(v) > 1}
    near_dups = {k: v for k, v in near_groups.items() if len(v) > 1}

    logger.info(f"Found {len(exact_dups)} exact duplicate groups and {len(short_units)} short units.")

    audit_data = {
        "EXACT_DUPLICATE_GROUPS": [],
        "NEAR_DUPLICATE_STATS": {
            "total_groups": len(near_dups),
            "total_units_involved": sum(len(v) for v in near_dups.values())
        },
        "SHORT_UNITS": []
    }

    # Load authoritative source family mappings from acquisition manifest
    ACQ_MANIFEST_PATH = ROOT_DIR / "data" / "acquisition" / "manifests" / "acquisition_manifest.json"
    doc_to_srcf = {}
    if ACQ_MANIFEST_PATH.exists():
        with open(ACQ_MANIFEST_PATH, "r", encoding="utf-8") as f:
            acq_data = json.load(f)
            for acq_doc in acq_data.get("documents", []):
                doc_id = acq_doc.get("document", {}).get("document_id")
                srcf = acq_doc.get("source", {}).get("source_family_id")
                if doc_id and srcf:
                    doc_to_srcf[doc_id] = srcf

    # Analyze exact duplicate groups
    for idx, (h, group) in enumerate(exact_dups.items()):
        doc_ids = set()
        doc_types = set()
        fam_ids = set()
        parent_shas = set()
        source_urls = set()
        locations = []
        
        for u in group:
            d_id = u["document_id"]
            doc_ids.add(d_id)
            doc_types.add(u["document_type"])
            fam_ids.add(doc_to_srcf.get(d_id, "UNRESOLVED_SOURCE_FAMILY"))
            parent_shas.add(u["parent_raw_sha256"])
            source_urls.add(u.get("source_url", "UNKNOWN"))
            locations.append(f"{d_id} (P{u.get('page_number', '1')} CL {u['section_or_clause']})")
            
        is_same_doc = len(doc_ids) == 1
        
        # Classification heuristic
        classification = "UNKNOWN_REQUIRES_REVIEW"
        text = group[0]["content_text"]
        
        if is_same_doc:
            if "Table" in text or "TABLE" in group[0]["content_type"]:
                classification = "LIKELY_EXTRACTION_ARTIFACT"
            elif len(text) < 50 and ("page" in text.lower() or "bureau" in text.lower() or "standard" in text.lower()):
                classification = "REPEATED_BOILERPLATE"
            else:
                classification = "SAME_DOCUMENT_EXTRACTION_DUPLICATE"
        else:
            if "page" in text.lower() or "bureau" in text.lower() or "standard" in text.lower() and len(text) < 50:
                classification = "REPEATED_BOILERPLATE"
            elif len(doc_ids) > 10:
                classification = "REPEATED_BOILERPLATE"
            else:
                classification = "CROSS_DOCUMENT_DUPLICATE"

        audit_data["EXACT_DUPLICATE_GROUPS"].append({
            "group_id": f"EXACT-DUP-{idx+1}",
            "member_count": len(group),
            "classification": classification,
            "sample_content": text[:200] + ("..." if len(text) > 200 else ""),
            "document_ids": list(doc_ids),
            "document_types": list(doc_types),
            "source_families": list(fam_ids),
            "parent_shas": list(parent_shas),
            "source_urls": list(source_urls),
            "locations": locations,
            "is_same_document": is_same_doc
        })

    # Analyze Short Units
    for u in short_units:
        audit_data["SHORT_UNITS"].append({
            "document_id": u["document_id"],
            "evidence_unit_id": u["evidence_unit_id"],
            "content": u["content_text"],
            "page": u.get("page_number", 1),
            "clause": u["section_or_clause"],
            "document_type": u["document_type"],
            "source_url": u.get("source_url", "UNKNOWN"),
            "legitimate_likelihood": "UNLIKELY" if len(u["content_text"].strip()) < 3 else "REVIEW_REQUIRED"
        })

    # Write JSON
    AUDIT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    def generate_markdown_report(audit: Dict, md_path: Path):
        # Load source families map
        source_families_map = {}
        if SOURCE_FAMILIES_PATH.exists():
            with open(SOURCE_FAMILIES_PATH, "r", encoding="utf-8") as f:
                sf_data = json.load(f)
                for family in sf_data.get("source_families", []):
                    source_families_map[family.get("source_family_id")] = family.get("name")
                    for sub in family.get("subfamilies", []):
                        source_families_map[sub.get("subfamily_id")] = sub.get("name")
        
        md = f"""# Phase 5: Evidence Quality - Duplicate & Short Unit Audit

## Summary
- Total Evidence Units Analyzed: {total_units}
- Exact Duplicate Groups: {len(exact_dups)}
- Near Duplicate Groups: {len(near_dups)}
- Extremely Short Units (<10 chars): {len(short_units)}

## 1. Short Unit Investigation (Total: {len(short_units)})
| Document ID | Unit ID | Content | Page | Clause | Likelihood | URL |
|---|---|---|---|---|---|---|
"""
        for su in audit["SHORT_UNITS"]:
            md += f"| {su['document_id']} | {su['evidence_unit_id']} | `{su['content']}` | {su['page']} | {su['clause']} | {su['legitimate_likelihood']} | {su['source_url']} |\n"

        md += """
## 2. Exact Duplicate Groups Classification
"""
        class_counts = defaultdict(int)
        for g in audit["EXACT_DUPLICATE_GROUPS"]:
            class_counts[g["classification"]] += 1
            
        for k, v in class_counts.items():
            md += f"- **{k}**: {v} groups\n"

        md += "\n## 3. Top Exact Duplicate Groups (Sample)\n\n"
        sorted_groups = sorted(audit["EXACT_DUPLICATE_GROUPS"], key=lambda x: x["member_count"], reverse=True)
        for g in sorted_groups[:20]:
            families_display = [f"{f} ({source_families_map.get(f, 'Unknown')})" for f in g['source_families']]
            families_str = ', '.join(families_display[:5]) + ('...' if len(families_display) > 5 else '')
            md += f"### {g['group_id']} ({g['member_count']} members)\n"
            md += f"- **Classification**: {g['classification']}\n"
            md += f"- **Same Document**: {g['is_same_document']}\n"
            md += f"- **Sample Content**: `{g['sample_content'].strip()}`\n"
            md += f"- **Families**: {families_str}\n"
            md += "\n"

        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)

    generate_markdown_report(audit_data, AUDIT_MD_PATH)
    logger.info("✅ Duplicate Audit Complete.")

if __name__ == "__main__":
    run_duplicate_audit()
