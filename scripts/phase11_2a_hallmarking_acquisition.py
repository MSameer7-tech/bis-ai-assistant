import argparse
import json
import hashlib
import time
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root to python path
import sys
sys.path.append('.')

from ai.acquisition.hallmarking.models import HallmarkingRecord
from ai.acquisition.hallmarking.discovery import HallmarkingDiscovery
from ai.acquisition.hallmarking.parser import extract_text_from_pdf, extract_text_from_html, infer_information_type
from dataclasses import asdict

OUT_DIR = Path("data/catalog/phase11_2a_hallmarking")
RAW_DIR = Path("data/raw/immutable/hallmarking")

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_jsonl(path: Path, data: list):
    with path.open("a", encoding="utf-8") as f:
        for item in data:
            if hasattr(item, '__dataclass_fields__'):
                f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
            else:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

def acquire(pilot=False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean previous output for this run
    for f in OUT_DIR.glob("*.jsonl"):
        f.unlink()

    start_urls = [
        "https://www.bis.gov.in/index.php/hallmarking-overview/",
        "https://www.manakonline.in/MANAK/hallmarking" # Hypothetical manakonline endpoint
    ]
    
    discovery = HallmarkingDiscovery(start_urls)
    
    records = []
    failures = []
    seen_urls = set()
    
    to_visit = start_urls.copy()
    
    while to_visit:
        url = to_visit.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Stop early in pilot mode
        if pilot and len(seen_urls) > 5:
            break
            
        print(f"Fetching: {url}")
        # Setting a short timeout to fast-fail blocked endpoints like manakonline.in
        r = discovery.fetch(url, timeout=2.0)
        
        if r is None:
            failures.append({"url": url, "error": "FETCH_FAILED_OR_TIMEOUT", "type": "ACCESS_FAILED"})
            # Create a failed record to preserve the intent
            rec = HallmarkingRecord(
                record_id=str(uuid.uuid4()),
                record_type="UNKNOWN",
                title=f"Failed Acquisition: {url}",
                content="",
                source_url=url,
                source_type="UNKNOWN",
                issuing_authority="BIS",
                authority_level="SUPPORTING_GUIDANCE",
                retrieved_at=now(),
                source_sha256="",
                access_status="FAILED",
                extraction_status="FAILED"
            )
            records.append(rec)
            continue
            
        content_bytes = r.content
        digest = sha(content_bytes)
        
        # Save raw immutable
        key = digest[:32]
        d = RAW_DIR / key
        d.mkdir(parents=True, exist_ok=True)
        
        source_type = discovery.categorize_link(url)
        
        # Determine extraction
        if source_type == "PDF":
            (d / "original.pdf").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_pdf(content_bytes)
        else:
            (d / "original.html").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_html(r.text)
            
            # Discover more links from HTML
            new_links = discovery.discover_links(r.text, url)
            for link in new_links:
                if link not in seen_urls and link not in to_visit:
                    to_visit.append(link)
        
        meta = {
            "source_url": url,
            "retrieved_at": now(),
            "http_status": r.status_code,
            "sha256": digest,
            "source_type": source_type
        }
        (d / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        
        info_type = infer_information_type(url, text_content)
        
        rec = HallmarkingRecord(
            record_id=str(uuid.uuid4()),
            record_type="HALLMARKING_DOCUMENT",
            title=f"Hallmarking Source: {url.split('/')[-1] or 'overview'}",
            content=text_content,
            source_url=url,
            source_type=source_type,
            issuing_authority="BIS",
            authority_level="PROCEDURAL",
            retrieved_at=now(),
            source_sha256=digest,
            access_status="ACQUIRED",
            extraction_status=ext_status,
            information_type=info_type,
            official_portal="manakonline.in" if "manakonline" in url else "bis.gov.in"
        )
        records.append(rec)
        time.sleep(0.5)

    write_jsonl(OUT_DIR / "hallmarking_records.jsonl", records)
    write_jsonl(OUT_DIR / "failures.jsonl", failures)
    
    manifest = {
        "run_type": "PILOT" if pilot else "FULL",
        "timestamp": now(),
        "total_urls_discovered": len(seen_urls) + len(to_visit),
        "records_acquired": len([r for r in records if r.access_status == "ACQUIRED"]),
        "failures": len(failures),
        "pdfs_extracted": len([r for r in records if r.source_type == "PDF" and r.extraction_status == "SUCCESS"])
    }
    with open(OUT_DIR / "acquisition_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    
    if args.full:
        acquire(pilot=False)
    else:
        acquire(pilot=True)
