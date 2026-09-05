#!/usr/bin/env python3
import argparse
import json
import hashlib
import time
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dataclasses import asdict

# Assuming the python path allows this
import sys
sys.path.append('.')
from ai.acquisition.lims_scope.models import Laboratory, ScopeRecord, TestingCharge
from ai.acquisition.lims_scope.scope_parser import normalize_standard, parse_testing_charge, hash_row

BASE = "https://lims.bis.gov.in"
DIRS = {
    "BIS_RECOGNIZED": "/home/labs/",
    "BIS_EMPANELLED": "/home/empaneled_labs/",
    "BIS_OWNED": "/home/bis_labs/"
}
OUT_DIR = Path("data/catalog/phase11_1_lims_scope")
RAW_DIR = Path("data/raw/immutable/lims_scope")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BIS-LIMS-Acquisition/1.0)"}

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def fetch(s: requests.Session, url: str) -> requests.Response:
    r = s.get(url, headers=HEADERS, timeout=1.0, allow_redirects=True)
    r.raise_for_status()
    return r

def text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split())

def parse_labs(page_html: str, lab_type: str, url: str) -> list:
    """Extract labs from directory pages."""
    soup = BeautifulSoup(page_html, "html.parser")
    labs = []
    
    # Generic table parser targeting LIMS layout. 
    # Usually Lab Name, Address, Recognition Validity etc.
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for r in rows[1:]:  # skip header
            cells = r.find_all(["td", "th"])
            if len(cells) < 2:
                continue
                
            lab_name = text(cells[1])
            if not lab_name:
                continue
                
            lab_code = "UNKNOWN_" + sha(lab_name.encode())[:8]
            
            # Look for scope link
            scope_url = None
            scope_status = "SCOPE_LINK_NOT_FOUND"
            for a in r.find_all("a"):
                href = a.get("href") or ""
                label = text(a).lower()
                if "scope" in label or "home_lab_scope" in href.lower():
                    if href.startswith("/"):
                        href = BASE + href
                    if href.startswith("http"):
                        scope_url = href
                        scope_status = "SCOPE_LINK_FOUND"
            
            lab = Laboratory(
                lab_code=lab_code,
                lab_name=lab_name,
                laboratory_type=lab_type,
                source_url=url,
                retrieved_at=now(),
                scope_status=scope_status
            )
            # Add the discovered scope url as a dynamically injected attribute for the crawler
            lab._scope_url = scope_url
            labs.append(lab)
            
    return labs

def parse_scope_rows(html: str, url: str, lab: Laboratory, html_sha: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    records = []
    
    tables = soup.find_all("table")
    for t_idx, table in enumerate(tables):
        for r_idx, tr in enumerate(table.find_all("tr")):
            cells = [text(td) for td in tr.find_all(["td", "th"])]
            
            # Simple heuristic for scope rows: usually start with SI No. or similar
            if len(cells) >= 5 and (cells[0].isdigit() or "standard" in str(table).lower()):
                # Columns roughly: Sl No., Product, IS No, Test Parameter, Test Method, Testing Charge
                raw_std = cells[2] if len(cells) > 2 else ""
                base_std, part, sec, year = normalize_standard(raw_std)
                
                charge_str = cells[5] if len(cells) > 5 else ""
                testing_charge = parse_testing_charge(charge_str)
                
                row_hash = hash_row(cells)
                
                rec = ScopeRecord(
                    scope_record_id=str(uuid.uuid4()),
                    laboratory_identity=lab.lab_code,
                    raw_standard_reference=raw_std,
                    normalized_standard_number=base_std,
                    part=part,
                    section=sec,
                    edition_year=year,
                    product_material=cells[1] if len(cells) > 1 else None,
                    characteristic_test=cells[3] if len(cells) > 3 else None,
                    test_method=cells[4] if len(cells) > 4 else None,
                    testing_charge=testing_charge,
                    source_url=url,
                    source_sha256=html_sha,
                    retrieved_at=now(),
                    table_index=t_idx,
                    row_index=r_idx,
                    source_row_hash=row_hash
                )
                records.append(rec)
    return records

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
        
    s = requests.Session()
    all_labs = []
    all_scopes = []
    failures = []
    
    for lab_type, directory_path in DIRS.items():
        url = BASE + directory_path + "?page=1"
        try:
            r = fetch(s, url)
        except Exception as e:
            failures.append({"url": url, "error": str(e), "type": "DIRECTORY_FETCH_FAILED"})
            continue
            
        labs = parse_labs(r.text, lab_type, url)
        if pilot:
            labs = labs[:5] # Limit to 5 per type for pilot
            
        for lab in labs:
            all_labs.append(lab)
            
            if lab._scope_url:
                try:
                    sr = fetch(s, lab._scope_url)
                    digest = sha(sr.content)
                    key = digest[:32]
                    
                    # Immutable Storage
                    d = RAW_DIR / key
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "original.html").write_bytes(sr.content)
                    
                    meta = {
                        "source_url": lab._scope_url,
                        "final_url": sr.url,
                        "retrieved_at": now(),
                        "http_status": sr.status_code,
                        "content_type": sr.headers.get("content-type"),
                        "sha256": digest,
                        "acquisition_method": "DIRECT_HTTP",
                        "tls_verified": True,
                        "laboratory_code": lab.lab_code
                    }
                    (d / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                    
                    rows = parse_scope_rows(sr.text, sr.url, lab, digest)
                    all_scopes.extend(rows)
                    
                except Exception as e:
                    failures.append({"url": lab._scope_url, "error": str(e), "type": "SCOPE_FETCH_FAILED"})
            
            time.sleep(0.2)
            
    # Deduplication
    seen_hashes = {}
    unique_scopes = []
    duplicate_count = 0
    for rec in all_scopes:
        if rec.source_row_hash in seen_hashes:
            rec.duplicate_group_id = seen_hashes[rec.source_row_hash]
            duplicate_count += 1
        else:
            seen_hashes[rec.source_row_hash] = rec.scope_record_id
        unique_scopes.append(rec)
        
    write_jsonl(OUT_DIR / "laboratories.jsonl", all_labs)
    write_jsonl(OUT_DIR / "scope_records.jsonl", unique_scopes)
    write_jsonl(OUT_DIR / "failures.jsonl", failures)
    
    # Manifest
    manifest = {
        "run_type": "PILOT" if pilot else "FULL",
        "timestamp": now(),
        "laboratories_discovered": len(all_labs),
        "scope_records_extracted": len(unique_scopes),
        "duplicate_rows": duplicate_count,
        "failures": len(failures),
        "testing_fees_extracted": sum(1 for s in unique_scopes if s.testing_charge is not None)
    }
    with open(OUT_DIR / "acquisition_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Acquisition complete. Labs: {len(all_labs)}, Scopes: {len(unique_scopes)}, Failures: {len(failures)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    
    if args.full:
        acquire(pilot=False)
    else:
        acquire(pilot=True)
