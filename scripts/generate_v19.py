import json
import os

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def main():
    v18_path = "data/bootstrap/bis_missing_domains_dataset_v18.jsonl"
    v19_path = "data/bootstrap/bis_missing_domains_dataset_v19.jsonl"
    manifest_path = "data/bootstrap/bis_missing_domains_dataset_v19_manifest.json"
    
    v18_records = load_jsonl(v18_path)
    new_hm = load_jsonl("data/catalog/phase11_2a_hallmarking/hallmarking_records.jsonl")
    
    seen_shas = {rec.get("source_sha256") for rec in v18_records if rec.get("source_sha256")}
    
    v19_records = []
    # 1. Copy v18 unchanged
    v19_records.extend(v18_records)
    
    stats = {
        "v18_baseline_count": len(v18_records),
        "v19_total_count": 0,
        "newly_added": 0,
        "rejected_duplicates": 0,
        "rejected_insufficient_authority": 0,
        "inaccessible_sources": 0,
        "domain_coverage": {}
    }
    
    for hm in new_hm:
        sha = hm.get("source_sha256", f"MOCK_SHA_{hm['record_id']}")
        if hm.get("access_status") != "ACQUIRED":
            stats["inaccessible_sources"] += 1
            continue
            
        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue
            
        rec = {
            "record_id": f"HM-{hm['record_id']}",
            "domain": "HALLMARKING",
            "record_type": hm["information_type"] or "GENERAL_PROCEDURE",
            "title": hm["title"],
            "content": hm["content"],
            "evidence_role": "PROCEDURAL",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": hm["source_url"],
            "retrieved_at": hm["retrieved_at"],
            "provenance": {
                "source_url": hm["source_url"],
                "retrieved_at": hm["retrieved_at"],
                "parent_source_url": hm.get("parent_source_url"),
                "source_type": hm.get("source_type"),
                "extraction_status": hm.get("extraction_status"),
                "official_portal": hm.get("official_portal")
            },
            "source_sha256": sha
        }
        v19_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1

    stats["v19_total_count"] = len(v19_records)
    
    # Calculate domain coverage
    for rec in v19_records:
        dom = rec.get("domain", "UNKNOWN")
        stats["domain_coverage"][dom] = stats["domain_coverage"].get(dom, 0) + 1

    with open(v19_path, "w") as f:
        for r in v19_records:
            f.write(json.dumps(r) + "\n")
            
    with open(manifest_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
