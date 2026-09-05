import json
import os

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def main():
    v19_path = "data/bootstrap/bis_missing_domains_dataset_v19.jsonl"
    v20_path = "data/bootstrap/bis_missing_domains_dataset_v20.jsonl"
    manifest_path = "data/bootstrap/bis_missing_domains_dataset_v20_manifest.json"
    
    v19_records = load_jsonl(v19_path)
    new_licences = load_jsonl("data/catalog/phase11_2b_licences/licences_records.jsonl")
    
    seen_shas = {rec.get("source_sha256") for rec in v19_records if rec.get("source_sha256")}
    
    v20_records = []
    # 1. Copy v19 unchanged
    v20_records.extend(v19_records)
    
    stats = {
        "v19_baseline_count": len(v19_records),
        "v20_total_count": 0,
        "newly_added": 0,
        "rejected_duplicates": 0,
        "rejected_insufficient_authority": 0,
        "inaccessible_sources": 0,
        "domain_coverage": {}
    }
    
    for lc in new_licences:
        sha = lc.get("source_sha256", f"MOCK_SHA_{lc['record_id']}")
        if lc.get("access_status") != "ACQUIRED":
            stats["inaccessible_sources"] += 1
            continue
            
        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue
            
        rec = {
            "record_id": f"LIC-{lc['record_id']}",
            "domain": "LICENCES_REGISTRATIONS",
            "record_type": lc["information_type"] or "APPLICATION_PROCEDURE",
            "title": lc["title"],
            "content": lc["content"],
            "evidence_role": "PROCEDURAL",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": lc["source_url"],
            "retrieved_at": lc["retrieved_at"],
            "provenance": {
                "source_url": lc["source_url"],
                "retrieved_at": lc["retrieved_at"],
                "parent_source_url": lc.get("parent_source_url"),
                "source_type": lc.get("source_type"),
                "extraction_status": lc.get("extraction_status"),
                "official_portal": lc.get("official_portal")
            },
            "source_sha256": sha
        }
        v20_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1

    stats["v20_total_count"] = len(v20_records)
    
    # Calculate domain coverage
    for rec in v20_records:
        dom = rec.get("domain", "UNKNOWN")
        stats["domain_coverage"][dom] = stats["domain_coverage"].get(dom, 0) + 1

    with open(v20_path, "w") as f:
        for r in v20_records:
            f.write(json.dumps(r) + "\n")
            
    with open(manifest_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
