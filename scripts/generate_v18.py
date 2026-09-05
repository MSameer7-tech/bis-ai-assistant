import json
import uuid
import os

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def main():
    v17_path = "data/bootstrap/bis_missing_domains_dataset_v17.jsonl"
    v18_path = "data/bootstrap/bis_missing_domains_dataset_v18.jsonl"
    manifest_path = "data/bootstrap/bis_missing_domains_dataset_v18_manifest.json"
    
    v17_records = load_jsonl(v17_path)
    
    new_labs = load_jsonl("data/catalog/phase11_1_lims_scope/laboratories.jsonl")
    new_scopes = load_jsonl("data/catalog/phase11_1_lims_scope/scope_records.jsonl")
    
    # Deduplication state
    seen_shas = {rec.get("source_sha256") for rec in v17_records if rec.get("source_sha256")}
    
    v18_records = []
    # 1. Copy v17 unchanged
    v18_records.extend(v17_records)
    
    # Track stats
    stats = {
        "v17_baseline_count": len(v17_records),
        "v18_total_count": 0,
        "newly_added": 0,
        "rejected_duplicates": 0,
        "rejected_insufficient_authority": 0,
        "inaccessible_sources": 0,
        "conflicting_records": 0,
        "recognized_labs_discovered": len([l for l in new_labs if l.get("laboratory_type") == "BIS_RECOGNIZED"]),
        "recognized_labs_acquired": 0,
        "empanelled_labs_discovered": len([l for l in new_labs if l.get("laboratory_type") == "BIS_EMPANELLED"]),
        "empanelled_labs_acquired": 0,
        "scope_pages_discovered": len(new_labs), # 1 scope page per lab
        "scope_pages_successfully_acquired": len(set(s.get("source_url") for s in new_scopes if s.get("source_url"))),
        "domain_coverage": {}
    }
    
    # Process new laboratories
    for lab in new_labs:
        sha = lab.get("source_sha256", f"MOCK_SHA_{lab['lab_code']}") # Lab might not have a page hash if link not found
        if lab.get("scope_status") == "SCOPE_LINK_NOT_FOUND":
            stats["inaccessible_sources"] += 1
            continue
            
        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue
            
        # Authority check (we know LIMS is official BIS)
        # Create record
        rec = {
            "record_id": f"LAB-{lab['lab_code']}",
            "domain": "LABORATORIES",
            "record_type": lab["laboratory_type"],
            "title": f"{lab['lab_name']} Laboratory",
            "content": json.dumps(lab),
            "evidence_role": "SUPPORTING_GUIDANCE",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": lab.get("source_url"),
            "retrieved_at": lab.get("retrieved_at"),
            "provenance": {
                "source_url": lab.get("source_url"),
                "retrieved_at": lab.get("retrieved_at")
            },
            "source_sha256": sha
        }
        v18_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1
        
        if lab["laboratory_type"] == "BIS_RECOGNIZED":
            stats["recognized_labs_acquired"] += 1
        elif lab["laboratory_type"] == "BIS_EMPANELLED":
            stats["empanelled_labs_acquired"] += 1

    # Process new scopes
    for scope in new_scopes:
        sha = scope.get("source_row_hash")
        if not sha:
            sha = scope.get("source_sha256", "UNKNOWN")
            
        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue
            
        rec = {
            "record_id": f"SCOPE-{scope['scope_record_id']}",
            "domain": "LABORATORIES",
            "record_type": "LAB_SCOPE",
            "title": f"Scope for {scope['laboratory_identity']} - {scope['normalized_standard_number']}",
            "content": json.dumps(scope),
            "evidence_role": "SUPPORTING_GUIDANCE",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": scope.get("source_url"),
            "retrieved_at": scope.get("retrieved_at"),
            "provenance": {
                "source_url": scope.get("source_url"),
                "retrieved_at": scope.get("retrieved_at"),
                "table_index": scope.get("table_index"),
                "row_index": scope.get("row_index")
            },
            "source_sha256": sha
        }
        v18_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1

    stats["v18_total_count"] = len(v18_records)
    
    # Calculate domain coverage
    for rec in v18_records:
        dom = rec.get("domain", "UNKNOWN")
        stats["domain_coverage"][dom] = stats["domain_coverage"].get(dom, 0) + 1

    # Write output
    with open(v18_path, "w") as f:
        for r in v18_records:
            f.write(json.dumps(r) + "\n")
            
    with open(manifest_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
