#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai.acquisition.discovery_engine import CandidateDocument
from ai.acquisition.identity_resolver import IdentityResolver

def run_audit():
    registry_path = ROOT_DIR / "data" / "candidates" / "candidate_documents.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    all_candidates = [CandidateDocument(**c) for c in raw_data]

    resolver = IdentityResolver()
    
    audit_records = []
    valid_count = 0
    invalid_count = 0
    manual_review_count = 0

    for cand in all_candidates:
        doc_id, fam_id, id_err = resolver.generate_document_id(
            document_type=cand.document_type,
            standard_number=cand.standard_number,
            part=cand.part,
            edition_year=cand.edition_year,
            amendment_number=cand.metadata.get("amendment_number"),
            ministry_acronym=cand.metadata.get("ministry"),
            notification_number=cand.metadata.get("notification_number"),
            year=cand.metadata.get("year"),
            version_label=cand.metadata.get("version"),
            custom_identifier=cand.candidate_id.replace("CAND-", "")
        )

        if id_err:
            invalid_count += 1
            if "MANUAL_REVIEW" in id_err or "Missing required fields" in id_err:
                manual_review_count += 1
                
            avail = [k for k, v in cand.model_dump().items() if v]
            avail.extend([f"meta_{k}" for k, v in cand.metadata.items() if v])
            
            audit_records.append({
                "candidate_id": cand.candidate_id,
                "document_type": cand.document_type,
                "title": cand.title,
                "source_id": cand.source_id,
                "source_family": cand.source_family_id,
                "canonical_url": cand.discovered_from_url,
                "validation_failure": id_err,
                "available_identity_fields": avail,
                "missing_identity_fields": ["standard_number"] if "standard_number" in id_err else ["custom_identifier"],
                "recommended_identity_strategy": "MANUAL_REVIEW"
            })
        else:
            valid_count += 1

    out_path = ROOT_DIR / "data" / "acquisition" / "quarantine" / "candidate_validation_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_records, f, indent=2)

    print(f"TOTAL {len(all_candidates)}")
    print(f"VALID FOR ACQUISITION: {valid_count}")
    print(f"MANUAL REVIEW: {manual_review_count}")
    print(f"INVALID: {invalid_count}")

if __name__ == "__main__":
    run_audit()
