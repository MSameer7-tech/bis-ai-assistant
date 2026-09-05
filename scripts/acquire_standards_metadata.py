import json
import re
import os
import hashlib
import urllib3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import time

urllib3.disable_warnings()

def normalize_standard(std: str) -> str:
    """Normalizes a standard number by removing extra spaces while preserving parts."""
    std = std.strip()
    return ' '.join(std.split())

def hash_content(content: str) -> str:
    """Returns SHA-256 of the content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def clean_standard_key(std: str) -> str:
    """Creates a filesystem-safe key for the standard."""
    key = normalize_standard(std).replace(' ', '-').replace('/', '-').replace(':', '-')
    key = re.sub(r'[^a-zA-Z0-9\-]', '', key)
    if len(key) > 64:
        key = key[:56] + "-" + hash_content(std)[:7]
    return key

def process_standard(standard_number: str) -> dict:
    normalized = normalize_standard(standard_number)
    standard_key = clean_standard_key(normalized)
    
    record = {
        "standard_number": normalized,
        "standard_key": standard_key,
        "internal_bis_id": None,
        "title": None,
        "technical_committee": None,
        "status": None,
        "reaffirmed_year": None,
        "superseded_by": None,
        "amendments": [],
        "source": {
            "source_id": "SRC-002",
            "source_url": "https://standardsbis.bsbedge.com/",
            "resolver_url": "https://standardsbis.bsbedge.com/popupextender.aspx/GetStdNo_Bis",
            "metadata_url": None,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "http_status": None,
            "source_sha256": None
        },
        "acquisition": {
            "status": "PENDING"
        }
    }
    
    # Step 1: Resolve ID
    try:
        resolver_response = requests.post(
            record["source"]["resolver_url"],
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            json={"prefixText": normalized, "count": 20, "contextKey": ""},
            verify=False,
            timeout=15
        )
    except Exception as e:
        record["acquisition"]["status"] = "RESOLUTION_FAILED"
        record["acquisition"]["error"] = f"Resolver HTTP Error: {e}"
        return record
        
    if resolver_response.status_code != 200:
        record["acquisition"]["status"] = "RESOLUTION_FAILED"
        record["acquisition"]["error"] = f"Resolver HTTP Status: {resolver_response.status_code}"
        return record
        
    try:
        data = resolver_response.json()
        items = data.get('d', [])
    except Exception as e:
        record["acquisition"]["status"] = "RESOLUTION_FAILED"
        record["acquisition"]["error"] = f"Resolver JSON Error: {e}"
        return record
        
    internal_id = None
    for item_str in items:
        try:
            item = json.loads(item_str)
            # Match exactly or if there's only one, take it?
            # E.g. "BIS -- IS 15750 : 2006", we should just extract id from "Standard_Number=IS+15750&id=8074"
            # It's safest to find the closest match or just take the first. Wait, standard numbers might return Amd variants.
            # Let's parse all and see if one matches exactly. If not, pick the first one without Amd if possible, or just the first one.
            first_text = item.get("First", "")
            second_text = item.get("Second", "")
            if normalized.lower() in first_text.lower():
                parsed_qs = parse_qs(second_text)
                if 'id' in parsed_qs:
                    internal_id = parsed_qs['id'][0]
                    # if it perfectly matches the base standard (not an amendment unless asked for)
                    if "Amd" not in first_text or "Amd" in normalized:
                        break
        except Exception:
            continue
            
    # If still none but items exist, fallback to first valid id
    if not internal_id and items:
        for item_str in items:
            try:
                item = json.loads(item_str)
                parsed_qs = parse_qs(item.get("Second", ""))
                if 'id' in parsed_qs:
                    internal_id = parsed_qs['id'][0]
                    break
            except Exception:
                continue
                
    if not internal_id:
        record["acquisition"]["status"] = "RESOLUTION_FAILED"
        record["acquisition"]["error"] = "Internal ID not found in resolver response."
        return record
        
    record["internal_bis_id"] = internal_id
    
    # Step 2: Fetch Metadata
    metadata_url = f"https://standardsbis.bsbedge.com/BIS_SearchStandard.aspx?Standard_Number={normalized.replace(' ', '+')}&id={internal_id}"
    record["source"]["metadata_url"] = metadata_url
    
    try:
        meta_response = requests.get(metadata_url, verify=False, timeout=15)
        record["source"]["http_status"] = meta_response.status_code
    except Exception as e:
        record["acquisition"]["status"] = "METADATA_FETCH_FAILED"
        record["acquisition"]["error"] = f"Metadata HTTP Error: {e}"
        return record
        
    if meta_response.status_code != 200:
        record["acquisition"]["status"] = "METADATA_FETCH_FAILED"
        record["acquisition"]["error"] = f"Metadata HTTP Status: {meta_response.status_code}"
        return record
        
    page_text = meta_response.text
    record["source"]["source_sha256"] = hash_content(page_text)
    
    # Save raw html and json inside record object (for the caller to save to disk)
    record["_raw_resolver"] = resolver_response.text
    record["_raw_metadata"] = page_text
    
    # Step 3: Parse
    soup = BeautifulSoup(page_text, 'html.parser')
    
    try:
        # standard number
        std_elem = soup.find('span', id='ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr')
        if not std_elem:
            record["acquisition"]["status"] = "PARSE_FAILED"
            record["acquisition"]["error"] = "Could not find standard number element on page."
            return record
            
        page_std = std_elem.text.strip()
        
        # Validation: Ensure it's the requested standard
        # The page_std might be "IS 15750 : 2006", requested might be "IS 15750"
        # Let's normalize both to their base IS number for validation
        base_req = normalized.split(':')[0].strip().lower()
        base_page = page_std.split(':')[0].strip().lower()
        if base_req not in base_page and base_page not in base_req:
            record["acquisition"]["status"] = "VALIDATION_FAILED"
            record["acquisition"]["error"] = f"Identity mismatch: Requested {normalized}, Got {page_std}"
            return record
            
        record["standard_number"] = page_std
        
        # Status
        status_elem = soup.find('span', id='ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstatus')
        if status_elem:
            record["status"] = status_elem.text.strip()
            
        # Reaffirmed Year
        reaff_elem = soup.find('span', id='ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblreaff')
        if reaff_elem:
            record["reaffirmed_year"] = reaff_elem.text.strip()
            
        # Title (often the text node in a specific TD or span)
        # E.g. Household frost-free refrigerating appliances ...
        # Based on dump, it follows the Reaffirmed Year. Let's just find the closest text block or specific label
        # Let's use a robust approach: find 'Household frost-free' etc. It doesn't have an ID.
        # But maybe we can find it in the td?
        # A simpler way: we'll look for text between standard number and "Technical Committee :"
        full_text = soup.body.text
        full_text_condensed = re.sub(r'\s+', ' ', full_text)
        
        # Try to extract title using regex based on known structure:
        # {std_number} (Reaffirmed Year : {year}) {Title} Technical Committee :
        # or {std_number} {Title} Technical Committee :
        match = re.search(r'(?:lblstdno_rptr">|<span id="ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr">)[^<]+</span>.*?<br/>\s*(.*?)\s*<br/>\s*<b', page_text, re.DOTALL | re.IGNORECASE)
        # Since HTML structure might vary, let's just find the text after standard number
        # Let's use BeautifulSoup iteration
        title_text = None
        for span in soup.find_all('span', id='ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr'):
            parent = span.parent
            # the title is usually text nodes inside the parent TD
            texts = [t.strip() for t in parent.find_all(string=True, recursive=False) if t.strip()]
            if texts:
                title_text = " ".join(texts)
                # clean up if it caught "Technical Committee :"
                if "Technical Committee :" in title_text:
                    title_text = title_text.split("Technical Committee :")[0].strip()
        
        if title_text:
            record["title"] = title_text
            
        # Technical Committee
        if "Technical Committee :" in full_text_condensed:
            tc_part = full_text_condensed.split("Technical Committee :")[1]
            if "Superseeded by" in tc_part:
                record["technical_committee"] = tc_part.split("Superseeded by")[0].strip()
            elif "Status :" in tc_part:
                record["technical_committee"] = tc_part.split("Status :")[0].strip()
            
        # Superseded By
        if "Superseeded by :" in full_text_condensed:
            sup_part = full_text_condensed.split("Superseeded by :")[1]
            record["superseded_by"] = sup_part.split("Status :")[0].strip()
            
        # Amendments
        # We can look for 'No. of Amendments :'
        if "No. of Amendments :" in full_text_condensed:
            amd_part = full_text_condensed.split("No. of Amendments :")[1]
            record["amendments"] = [amd_part.split("Custcode")[0].strip()] # Just storing the number/string for now
            
        record["acquisition"]["status"] = "SUCCESS"
        
    except Exception as e:
        record["acquisition"]["status"] = "PARSE_FAILED"
        record["acquisition"]["error"] = f"Exception during parse: {e}"
        
    return record


def main():
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "data" / "catalog" / "compulsory_certification" / "product_standard_relationships.jsonl"
    out_dir = base_dir / "data" / "catalog" / "standards"
    raw_dir = out_dir / "raw"
    metadata_file = out_dir / "standards_metadata.jsonl"
    manifest_file = out_dir / "standards_acquisition_manifest.json"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "source_id": "SRC-002",
        "input_file": str(input_file),
        "relationship_count": 0,
        "unique_standard_count": 0,
        "attempted_count": 0,
        "successful_count": 0,
        "unchanged_count": 0,
        "failed_count": 0,
        "resolution_failed_count": 0,
        "metadata_fetch_failed_count": 0,
        "parse_failed_count": 0,
        "validation_failed_count": 0,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "records": []
    }
    
    # Read existing metadata to support idempotency
    existing_hashes = {}
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    std_num = rec.get("standard_number")
                    if std_num:
                        existing_hashes[std_num] = rec.get("source", {}).get("source_sha256")
                except:
                    pass

    # Step 1: Input Extraction
    unique_standards = set()
    relationships = 0
    if input_file.exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rel = json.loads(line)
                    relationships += 1
                    std = rel.get('standard_number')
                    if std:
                        unique_standards.add(normalize_standard(std))
                except:
                    pass
                    
    manifest["relationship_count"] = relationships
    manifest["unique_standard_count"] = len(unique_standards)
    
    # Must run validation case IS 15750 unconditionally
    unique_standards.add(normalize_standard("IS 15750"))
    
    # Step 2: Acquisition
    metadata_records = []
    
    for std in sorted(unique_standards):
        manifest["attempted_count"] += 1
        
        record = process_standard(std)
        
        # Write raw files if we got something
        std_key = record.get("standard_key")
        std_raw_dir = raw_dir / std_key
        std_raw_dir.mkdir(parents=True, exist_ok=True)
        
        raw_resolver = record.pop("_raw_resolver", None)
        raw_metadata = record.pop("_raw_metadata", None)
        
        if raw_resolver:
            (std_raw_dir / "resolver_response.json").write_text(raw_resolver, encoding='utf-8')
        if raw_metadata:
            (std_raw_dir / "standard_page.html").write_text(raw_metadata, encoding='utf-8')
            
        status = record["acquisition"]["status"]
        
        if status == "SUCCESS":
            current_hash = record["source"]["source_sha256"]
            prev_hash = existing_hashes.get(record["standard_number"])
            if prev_hash and current_hash == prev_hash:
                status = "UNCHANGED"
                record["acquisition"]["status"] = "UNCHANGED"
                manifest["unchanged_count"] += 1
            else:
                if prev_hash:
                    status = "CONTENT_CHANGED_REQUIRES_REVIEW"
                    record["acquisition"]["status"] = "CONTENT_CHANGED_REQUIRES_REVIEW"
                manifest["successful_count"] += 1
            metadata_records.append(record)
        else:
            manifest["failed_count"] += 1
            if status == "RESOLUTION_FAILED":
                manifest["resolution_failed_count"] += 1
            elif status == "METADATA_FETCH_FAILED":
                manifest["metadata_fetch_failed_count"] += 1
            elif status == "PARSE_FAILED":
                manifest["parse_failed_count"] += 1
            elif status == "VALIDATION_FAILED":
                manifest["validation_failed_count"] += 1
                
        # Append to manifest records
        manifest["records"].append({
            "standard_number": std,
            "standard_key": std_key,
            "acquisition_status": status,
            "internal_bis_id": record.get("internal_bis_id"),
            "http_status": record.get("source", {}).get("http_status"),
            "source_sha256": record.get("source", {}).get("source_sha256"),
            "error": record.get("acquisition", {}).get("error")
        })
        
        time.sleep(0.5) # rate limit
        
    # Write metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        for rec in metadata_records:
            f.write(json.dumps(rec) + '\n')
            
    manifest["completed_at"] = datetime.utcnow().isoformat() + "Z"
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Acquisition complete. Processed {manifest['attempted_count']} standards.")
    print(f"Success: {manifest['successful_count']}, Unchanged: {manifest['unchanged_count']}, Failed: {manifest['failed_count']}")

if __name__ == "__main__":
    main()
