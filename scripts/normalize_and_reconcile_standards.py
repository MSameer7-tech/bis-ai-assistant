import json
import re
import hashlib
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def build_normalized_string(identity: dict) -> str:
    if not identity:
        return None
    parts = []
    if identity.get("standard_prefix"):
        parts.append(identity["standard_prefix"])
    else:
        parts.append("IS")
    
    if identity.get("base_number"):
        parts.append(identity["base_number"])
        
    sub = []
    if identity.get("part"):
        sub.append(f"Part {identity['part']}")
    if identity.get("section"):
        sub.append(f"Sec {identity['section']}")
        
    if sub:
        parts.append(f"({'/'.join(sub)})")
        
    if identity.get("edition_year"):
        parts.append(f": {identity['edition_year']}")
        
    if identity.get("amendment"):
        parts.append(identity["amendment"])
        
    return " ".join(parts)

def classify_and_extract(raw_val: str) -> dict:
    val = raw_val.strip()
    val_lower = val.lower()
    
    result = {
        "classification": "NO_STANDARD_FOUND",
        "confidence": "NONE",
        "confidence_reason": "",
        "identity": None,
        "referenced_standards": [],
        "normalized_standard_number": None
    }
    
    # 1. Obvious Rejections
    if "clause" in val_lower:
        result["classification"] = "CLAUSE_REFERENCE"
        return result
        
    if "http://" in val_lower or "https://" in val_lower:
        result["classification"] = "FILENAME_REFERENCE" # URL actually, but treated as rejection
        return result
        
    is_filename = False
    if ".pdf" in val_lower or ".doc" in val_lower:
        is_filename = True
        result["classification"] = "FILENAME_REFERENCE"
        
    # Clean string for regex (replace unicode dashes and underscores with spaces if filename)
    clean_val = val.replace('–', '-').replace('\u200b', '')
    if is_filename:
        clean_val = clean_val.replace('_', ' ')
        
    # 2. Base Number Extraction
    base_match = re.search(r'(?:IS\s*/\s*IEC|IS|IEC)?\s*([0-9]{3,})', clean_val, re.IGNORECASE)
    if not base_match:
        # Check if it's an ambiguous short number
        if re.search(r'^\s*[0-9]{1,2}\s*$', clean_val):
            result["classification"] = "NON_STANDARD_NUMERIC"
        elif re.search(r'^\s*[0-9]{4}\s*$', clean_val):
            result["classification"] = "AMBIGUOUS"
        return result
        
    base_num = base_match.group(1)
    has_is_prefix = "IS" in clean_val.upper()
    
    identity = {
        "standard_prefix": "IS", # Always treat extracted primary as IS candidate
        "base_number": base_num,
        "part": None,
        "section": None,
        "edition_year": None,
        "amendment": None
    }
    
    # 3. Part Extraction
    part_match = re.search(r'Part\s*([0-9A-Za-z]+)', clean_val, re.IGNORECASE)
    if part_match:
        identity["part"] = part_match.group(1)
    else:
        # Check IS / IEC 60947 - 2
        if "IEC" in clean_val.upper() or "IS /" in clean_val.upper():
            dash_match = re.search(r'{}\s*-\s*([0-9]+)'.format(base_num), clean_val)
            if dash_match:
                identity["part"] = dash_match.group(1)
                
    # 4. Section Extraction
    sec_match = re.search(r'Sec(?:tion)?\s*([0-9A-Za-z]+)', clean_val, re.IGNORECASE)
    if sec_match:
        identity["section"] = sec_match.group(1)
        
    # 5. Edition Year
    year_match = re.search(r':\s*([12][0-9]{3})', clean_val)
    if year_match:
        identity["edition_year"] = year_match.group(1)
        
    # 6. Amendment
    amd_match = re.search(r'(A[0-9]+|Amd[0-9]+|Amendment\s*[0-9]+)', clean_val, re.IGNORECASE)
    if amd_match:
        identity["amendment"] = amd_match.group(1)
        
    result["identity"] = identity
    result["normalized_standard_number"] = build_normalized_string(identity)
    
    # 7. Dual Standards
    if "IEC" in clean_val.upper() and "/" in clean_val:
        iec_match = re.search(r'(IEC\s*[0-9]+(?:-[0-9]+)*)', clean_val, re.IGNORECASE)
        if iec_match:
            iec_year_match = re.search(f"{re.escape(iec_match.group(1))}\\s*:\\s*([12][0-9]{{3}})", clean_val, re.IGNORECASE)
            ref = {"raw": iec_match.group(1), "edition_year": iec_year_match.group(1) if iec_year_match else None}
            result["referenced_standards"].append(ref)
            
    # 8. Classification Logic
    if is_filename:
        if base_num:
            result["classification"] = "FILENAME_CONTAINING_STANDARD_CANDIDATE"
            result["confidence"] = "LOW"
            result["confidence_reason"] = "Extracted from filename"
    elif result["referenced_standards"]:
        result["classification"] = "DUAL_STANDARD_REFERENCE"
        result["confidence"] = "HIGH"
        result["confidence_reason"] = "Dual standard structure recognized"
    elif identity["part"] or identity["section"]:
        result["classification"] = "STANDARD_CANDIDATE_WITH_PART" if not identity["section"] else "STANDARD_CANDIDATE_WITH_SECTION"
        result["confidence"] = "HIGH" if has_is_prefix else "MEDIUM"
        result["confidence_reason"] = "Contains explicit part/section structure"
    elif identity["edition_year"]:
        result["classification"] = "STANDARD_CANDIDATE_WITH_YEAR"
        result["confidence"] = "HIGH" if has_is_prefix else "MEDIUM"
        result["confidence_reason"] = "Contains explicit year structure"
    elif has_is_prefix:
        result["classification"] = "CONFIDENT_STANDARD_CANDIDATE"
        result["confidence"] = "HIGH"
        result["confidence_reason"] = "Explicit IS prefix present"
    elif len(base_num) >= 5:
        # 5+ digit number alone -> standard candidate
        result["classification"] = "STANDARD_CANDIDATE"
        result["confidence"] = "MEDIUM"
        result["confidence_reason"] = "Sufficient numeric/structural evidence"
    elif len(base_num) == 4:
        result["classification"] = "AMBIGUOUS"
        result["confidence"] = "LOW"
        result["confidence_reason"] = "4-digit number with no prefix could be a year or standard"
    else:
        result["classification"] = "NON_STANDARD_NUMERIC"
        result["confidence"] = "LOW"
        result["confidence_reason"] = "Short number with no prefix or additional structure"
        
    return result

def reconcile_against_src002(candidate: dict) -> dict:
    normalized_number = candidate["normalized_standard_number"]
    url = "https://standardsbis.bsbedge.com/popupextender.aspx/GetStdNo_Bis"
    
    rec_result = {
        "status": "UNRESOLVED",
        "src002_internal_bis_id": None,
        "matched_standard_number": None,
        "base_standard_match": False,
        "part_section_validated": False,
        "year_match": None
    }
    
    try:
        resolver_response = requests.post(
            url,
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            json={"prefixText": normalized_number, "count": 20, "contextKey": ""},
            verify=False,
            timeout=10
        )
        if resolver_response.status_code != 200:
            rec_result["reason"] = f"HTTP {resolver_response.status_code}"
            return rec_result
            
        data = resolver_response.json().get('d', [])
    except Exception as e:
        rec_result["reason"] = f"Resolver Error: {str(e)}"
        return rec_result
        
    internal_id = None
    for item_str in data:
        try:
            item = json.loads(item_str)
            first_text = item.get("First", "")
            base_req = candidate["identity"]["base_number"].lower()
            if base_req in first_text.lower():
                parsed_qs = parse_qs(item.get("Second", ""))
                if 'id' in parsed_qs:
                    internal_id = parsed_qs['id'][0]
                    break
        except Exception:
            continue
            
    if not internal_id:
        rec_result["status"] = "NOT_FOUND"
        return rec_result
        
    # Fetch detail
    meta_url = f"https://standardsbis.bsbedge.com/BIS_SearchStandard.aspx?Standard_Number={normalized_number.replace(' ', '+')}&id={internal_id}"
    try:
        meta_response = requests.get(meta_url, verify=False, timeout=10)
        if meta_response.status_code != 200:
            rec_result["reason"] = "Meta fetch failed"
            return rec_result
            
        soup = BeautifulSoup(meta_response.text, 'html.parser')
        std_elem = soup.find('span', id='ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr')
        if not std_elem:
            rec_result["reason"] = "Standard element not found in HTML"
            return rec_result
            
        page_std = std_elem.text.strip()
        
        base_req = candidate["identity"]["base_number"].lower()
        base_page_parts = page_std.split(':')[0].strip().lower()
        
        if base_req in base_page_parts:
            rec_result["base_standard_match"] = True
            
        if not rec_result["base_standard_match"]:
            rec_result["status"] = "IDENTITY_MISMATCH"
            rec_result["matched_standard_number"] = page_std
            return rec_result
            
        rec_result["status"] = "MATCHED"
        rec_result["src002_internal_bis_id"] = internal_id
        rec_result["matched_standard_number"] = page_std
        
        # Validation
        req_part = candidate["identity"].get("part")
        req_sec = candidate["identity"].get("section")
        req_year = candidate["identity"].get("edition_year")
        
        # Check part/section validation
        if req_part or req_sec:
            page_part = re.search(r'Part\s*([0-9A-Za-z]+)', page_std, re.IGNORECASE)
            page_sec = re.search(r'Sec(?:tion)?\s*([0-9A-Za-z]+)', page_std, re.IGNORECASE)
            
            p_val = page_part.group(1) if page_part else None
            s_val = page_sec.group(1) if page_sec else None
            
            if (req_part and req_part.lower() != (p_val.lower() if p_val else "")) or \
               (req_sec and req_sec.lower() != (s_val.lower() if s_val else "")):
                rec_result["part_section_validated"] = False
            else:
                rec_result["part_section_validated"] = True
        
        # Check year validation
        if req_year:
            page_year = re.search(r':\s*([12][0-9]{3})', page_std)
            if page_year and page_year.group(1) == req_year:
                rec_result["year_match"] = True
            elif page_year:
                rec_result["year_match"] = False
                
        return rec_result
        
    except Exception as e:
        rec_result["reason"] = f"Meta parsing Error: {str(e)}"
        return rec_result


def main():
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "data" / "catalog" / "compulsory_certification" / "product_standard_relationships.jsonl"
    out_dir = base_dir / "data" / "catalog" / "standards"
    out_file = out_dir / "standard_identity_reconciliation.jsonl"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_relationships": 0,
        "unique_raw_values": set(),
        "candidates_extracted": 0,
        "candidates_rejected": 0,
        "ambiguous": 0,
        "clause_references": 0,
        "filename_references": 0,
        "dual_standards": 0,
        "sent_to_src002": 0,
        "matched": 0,
        "not_found": 0,
        "identity_mismatch": 0,
        "part_section_mismatch": 0,
        "year_mismatch": 0,
        "unresolved": 0
    }

    relationships = []
    if input_file.exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rel = json.loads(line)
                    relationships.append(rel)
                    std = rel.get('standard_number')
                    if std:
                        stats["unique_raw_values"].add(std)
                except:
                    pass
                    
    stats["total_relationships"] = len(relationships)
    
    cache = {}
    
    # Process unique raw values
    for raw_val in sorted(list(stats["unique_raw_values"])) + ["IS 15750"]:
        extraction = classify_and_extract(raw_val)
        
        if extraction["classification"] in ["AMBIGUOUS", "NON_STANDARD_NUMERIC"]:
            stats["ambiguous"] += 1
        elif extraction["classification"] == "CLAUSE_REFERENCE":
            stats["clause_references"] += 1
        elif "FILENAME" in extraction["classification"]:
            stats["filename_references"] += 1
        elif extraction["classification"] == "DUAL_STANDARD_REFERENCE":
            stats["dual_standards"] += 1
            
        if not extraction["identity"] or extraction["confidence"] == "NONE":
            stats["candidates_rejected"] += 1
            cache[raw_val] = {
                "extracted": extraction,
                "reconciliation": {"status": "INVALID_CANDIDATE"}
            }
            continue
            
        stats["candidates_extracted"] += 1
        
        # Reconciliation
        if extraction["confidence"] in ["HIGH", "MEDIUM"]:
            stats["sent_to_src002"] += 1
            rec_res = reconcile_against_src002(extraction)
            
            if rec_res["status"] == "MATCHED":
                stats["matched"] += 1
                if extraction["identity"]["part"] and not rec_res.get("part_section_validated"):
                    stats["part_section_mismatch"] += 1
                if extraction["identity"]["edition_year"] and rec_res.get("year_match") is False:
                    stats["year_mismatch"] += 1
            elif rec_res["status"] == "NOT_FOUND":
                stats["not_found"] += 1
            elif rec_res["status"] == "IDENTITY_MISMATCH":
                stats["identity_mismatch"] += 1
            else:
                stats["unresolved"] += 1
        else:
            rec_res = {"status": "UNRESOLVED", "reason": "Low confidence, not sent to SRC-002"}
            
        cache[raw_val] = {
            "extracted": extraction,
            "reconciliation": rec_res
        }
        
        time.sleep(0.2)
        
    # Write output
    with open(out_file, 'w', encoding='utf-8') as f:
        for rel in relationships:
            raw_val = rel.get('standard_number')
            if not raw_val: continue
            
            c = cache.get(raw_val, {})
            extracted = c.get("extracted", {})
            
            out_rec = {
                "relationship_id": rel.get("relationship_id", hash_content(json.dumps(rel))[:12]),
                "product_name": rel.get("product_name"),
                "raw_standard_value": raw_val,
                "extracted_identity": extracted.get("identity"),
                "normalized_standard_number": extracted.get("normalized_standard_number"),
                "standard_identity_type": extracted.get("classification"),
                "confidence": extracted.get("confidence"),
                "confidence_reason": extracted.get("confidence_reason"),
                "referenced_standards": extracted.get("referenced_standards", []),
                "source": rel.get("source", {}),
                "reconciliation": c.get("reconciliation")
            }
            f.write(json.dumps(out_rec) + '\n')
            
    print("Reconciliation Stats:")
    print(f"Total Relationships: {stats['total_relationships']}")
    print(f"Unique Raw Values: {len(stats['unique_raw_values'])}")
    print(f"Candidates Extracted: {stats['candidates_extracted']}")
    print(f"Candidates Rejected: {stats['candidates_rejected']}")
    print(f"Ambiguous: {stats['ambiguous']}")
    print(f"Clause References: {stats['clause_references']}")
    print(f"Filename References: {stats['filename_references']}")
    print(f"Dual Standards: {stats['dual_standards']}")
    print(f"Sent to SRC-002: {stats['sent_to_src002']}")
    print(f"Matched: {stats['matched']}")
    print(f"Not Found: {stats['not_found']}")
    print(f"Identity Mismatch: {stats['identity_mismatch']}")
    print(f"Part/Section Mismatch: {stats['part_section_mismatch']}")
    print(f"Year Mismatch: {stats['year_mismatch']}")
    print(f"Unresolved: {stats['unresolved']}")
    
    # Check IS 15750 control
    control = cache.get("IS 15750")
    if control:
        print(f"IS 15750 Control Result: {control['reconciliation']}")
        
if __name__ == "__main__":
    main()
