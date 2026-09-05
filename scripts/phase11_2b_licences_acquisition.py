import argparse
import json
import hashlib
import time
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import sys
sys.path.append('.')

from ai.acquisition.licences.models import LicenceRecord
from ai.acquisition.licences.discovery import LicencesDiscovery
from ai.acquisition.licences.parser import extract_text_from_pdf, extract_text_from_html, infer_information_type
from dataclasses import asdict

OUT_DIR = Path("data/catalog/phase11_2b_licences")
RAW_DIR = Path("data/raw/immutable/licences")

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
    
    for f in OUT_DIR.glob("*.jsonl"):
        f.unlink()

    # Prioritize publicly accessible BIS material FIRST
    start_urls = [
        "https://www.bis.gov.in/index.php/product-certification/",
        "https://www.bis.gov.in/index.php/fmcs/",
        "https://www.bis.gov.in/index.php/product-certification/product-certification-scheme/",
        "https://crsbis.in/CRS/",            # Operational portal 
        "https://www.manakonline.in/MANAK/"  # Operational portal
    ]
    
    discovery = LicencesDiscovery(start_urls)
    records = []
    failures = []
    seen_urls = set()
    to_visit = start_urls.copy()
    
    while to_visit:
        url = to_visit.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        if pilot and len(seen_urls) > 6:
            break
        if not pilot and len(seen_urls) > 40:
            break
            
        print(f"Fetching: {url}")
        r = discovery.fetch(url, timeout=2.0)
        
        if r is None:
            failures.append({"url": url, "error": "FETCH_FAILED_OR_TIMEOUT", "type": "ACCESS_FAILED"})
            rec = LicenceRecord(
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
        
        key = digest[:32]
        d = RAW_DIR / key
        d.mkdir(parents=True, exist_ok=True)
        
        source_type = discovery.categorize_link(url)
        
        if source_type == "PDF":
            (d / "original.pdf").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_pdf(content_bytes)
        else:
            (d / "original.html").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_html(r.text)
            
            # Extract links to continue crawling publicly accessible info
            new_links = discovery.discover_links(r.text, url)
            for link in new_links:
                if link not in seen_urls and link not in to_visit:
                    # Append operational portals to end, prioritize bis.gov.in
                    if "manakonline" in link or "crsbis" in link:
                        to_visit.append(link)
                    else:
                        to_visit.insert(0, link)
        
        meta = {
            "source_url": url,
            "retrieved_at": now(),
            "http_status": r.status_code,
            "sha256": digest,
            "source_type": source_type
        }
        (d / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        
        info_type = infer_information_type(url, text_content)
        
        rec = LicenceRecord(
            record_id=str(uuid.uuid4()),
            record_type="LICENCE_DOCUMENT",
            title=f"Licences Source: {url.split('/')[-1] or 'overview'}",
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
            official_portal=urlparse(url).netloc
        )
        records.append(rec)
        time.sleep(0.5)

    write_jsonl(OUT_DIR / "licences_records.jsonl", records)
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
