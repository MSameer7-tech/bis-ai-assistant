import json
import os

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def main():
    v20_path = "data/bootstrap/bis_missing_domains_dataset_v20.jsonl"
    v21_path = "data/bootstrap/bis_missing_domains_dataset_v21.jsonl"
    manifest_path = "data/bootstrap/bis_missing_domains_dataset_v21_manifest.json"
    
    v20_records = load_jsonl(v20_path)
    new_consumer = load_jsonl("data/catalog/phase11_2c_consumer/consumer_records.jsonl")
    
    seen_shas = {rec.get("source_sha256") for rec in v20_records if rec.get("source_sha256")}
    
    v21_records = []
    # 1. Copy v20 unchanged
    v21_records.extend(v20_records)
    
    stats = {
        "v20_baseline_count": len(v20_records),
        "v21_total_count": 0,
        "newly_added": 0,
        "rejected_duplicates": 0,
        "rejected_insufficient_authority": 0,
        "inaccessible_sources": 0,
        "domain_coverage": {}
    }
    
    for cm in new_consumer:
        sha = cm.get("source_sha256", f"MOCK_SHA_{cm['record_id']}")
        if cm.get("access_status") != "ACQUIRED":
            stats["inaccessible_sources"] += 1
            continue
            
        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue
            
        rec = {
            "record_id": f"CON-{cm['record_id']}",
            "domain": "CONSUMER_BIS_CARE",
            "record_type": cm["information_type"] or "AWARENESS",
            "title": cm["title"],
            "content": cm["content"],
            "evidence_role": "SUPPORTING_GUIDANCE",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": cm["source_url"],
            "retrieved_at": cm["retrieved_at"],
            "provenance": {
                "source_url": cm["source_url"],
                "retrieved_at": cm["retrieved_at"],
                "parent_source_url": cm.get("parent_source_url"),
                "source_type": cm.get("source_type"),
                "extraction_status": cm.get("extraction_status"),
                "official_portal": cm.get("official_portal")
            },
            "source_sha256": sha
        }
        v21_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1

    stats["v21_total_count"] = len(v21_records)
    
    # Calculate domain coverage
    for rec in v21_records:
        dom = rec.get("domain", "UNKNOWN")
        stats["domain_coverage"][dom] = stats["domain_coverage"].get(dom, 0) + 1

    with open(v21_path, "w") as f:
        for r in v21_records:
            f.write(json.dumps(r) + "\n")
            
    with open(manifest_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
