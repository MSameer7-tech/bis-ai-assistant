import json
import os

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def main():
    v21_path = "data/bootstrap/bis_missing_domains_dataset_v21.jsonl"
    v22_path = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
    manifest_path = "data/bootstrap/bis_missing_domains_dataset_v22_manifest.json"

    v21_records = load_jsonl(v21_path)
    new_faq = load_jsonl("data/catalog/phase11_2d_faq_guides/faq_guide_records.jsonl")

    seen_shas = {rec.get("source_sha256") for rec in v21_records if rec.get("source_sha256")}

    v22_records = list(v21_records)  # copy v21 unchanged

    stats = {
        "v21_baseline_count": len(v21_records),
        "v22_total_count": 0,
        "newly_added": 0,
        "rejected_duplicates": 0,
        "rejected_insufficient_authority": 0,
        "inaccessible_sources": 0,
        "domain_coverage": {},
    }

    for fq in new_faq:
        sha = fq.get("source_sha256", f"MOCK_SHA_{fq['record_id']}")
        if fq.get("access_status") != "ACQUIRED":
            stats["inaccessible_sources"] += 1
            continue

        if sha in seen_shas:
            stats["rejected_duplicates"] += 1
            continue

        rec = {
            "record_id": f"FG-{fq['record_id']}",
            "domain": "FAQ_GUIDES_BOOKLETS",
            "record_type": fq.get("information_type") or "GENERAL_GUIDE",
            "title": fq["title"],
            "content": fq["content"],
            "evidence_role": "SUPPORTING_GUIDANCE",
            "authority": "BIS_PUBLISHED",
            "normative": False,
            "source_url": fq["source_url"],
            "retrieved_at": fq["retrieved_at"],
            "provenance": {
                "source_url": fq["source_url"],
                "retrieved_at": fq["retrieved_at"],
                "parent_source_url": fq.get("parent_source_url"),
                "source_type": fq.get("source_type"),
                "extraction_status": fq.get("extraction_status"),
                "official_portal": fq.get("official_portal"),
            },
            "source_sha256": sha,
        }
        v22_records.append(rec)
        seen_shas.add(sha)
        stats["newly_added"] += 1

    stats["v22_total_count"] = len(v22_records)

    for rec in v22_records:
        dom = rec.get("domain", "UNKNOWN")
        stats["domain_coverage"][dom] = stats["domain_coverage"].get(dom, 0) + 1

    with open(v22_path, "w") as f:
        for r in v22_records:
            f.write(json.dumps(r) + "\n")

    with open(manifest_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
