import argparse
import json
import hashlib
import time
import os
import uuid
import io
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import sys
sys.path.append('.')

import requests
from bs4 import BeautifulSoup

OUT_DIR = Path("data/catalog/phase11_2d_faq_guides")
RAW_DIR = Path("data/raw/immutable/faq_guides")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BIS-FAQ-Guides-Acquisition/1.0)"}

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip(), "SUCCESS"
    except Exception as e:
        return str(e), "FAILED"

def extract_text_from_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True), "SUCCESS"
    except Exception as e:
        return str(e), "FAILED"


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def infer_information_type(url, text):
    url_lower = url.lower()
    text_lower = (text[:2000] if text else "").lower()
    if "faq" in url_lower or "frequently" in text_lower:
        return "FAQ"
    if "booklet" in url_lower or "booklet" in text_lower:
        return "BOOKLET"
    if "circular" in url_lower or "circular" in text_lower:
        return "CIRCULAR"
    if "guide" in url_lower or "guideline" in text_lower or "guidance" in text_lower:
        return "GUIDE"
    if "procedure" in url_lower or "procedure" in text_lower:
        return "PROCEDURE_GUIDE"
    if "handbook" in url_lower or "handbook" in text_lower:
        return "HANDBOOK"
    if url_lower.endswith(".pdf"):
        return "OFFICIAL_DOCUMENT"
    return "GENERAL_GUIDE"


# ---------------------------------------------------------------------------
# Link filtering — broad discovery from official BIS pages, then filter
# ---------------------------------------------------------------------------

FAQ_GUIDE_KEYWORDS = {
    "faq", "guide", "guideline", "booklet", "circular", "handbook",
    "procedure", "awareness", "publication", "document", "know-your",
    "how-to", "help", "overview", "about", "information", "resource",
    "conformity", "certification", "hallmarking", "standard",
}

def is_faq_guide_candidate(url):
    """Broad filter: keep links that might lead to FAQ/guide/booklet content.
    
    Unlike 11.2C which used a tight consumer-only filter, we use a broader
    net here because FAQs and guides live across many BIS site sections.
    PDFs are always kept since they are typically official documents.
    """
    url_lower = url.lower()
    # Always keep PDFs — they are official documents
    if url_lower.endswith(".pdf"):
        return True
    # Keep links containing any FAQ/guide keyword
    for kw in FAQ_GUIDE_KEYWORDS:
        if kw in url_lower:
            return True
    return False


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

def fetch(url, timeout=5.0):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException:
        return None


# ---------------------------------------------------------------------------
# Main acquisition
# ---------------------------------------------------------------------------

def acquire(pilot=False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for f in OUT_DIR.glob("*.jsonl"):
        f.unlink()

    # Start from broad BIS entry points and let dynamic navigation discover
    # FAQ/guide pages rather than hardcoding specific FAQ URLs.
    start_urls = [
        "https://www.bis.gov.in/",
        "https://www.bis.gov.in/index.php/product-certification/",
        "https://www.bis.gov.in/index.php/hallmarking-overview/",
        "https://www.bis.gov.in/index.php/laboratory-services/",
        "https://www.bis.gov.in/index.php/consumer-affairs/",
        "https://www.bis.gov.in/index.php/system-certification-overview/",
        "https://www.bis.gov.in/index.php/standardization-overview/",
    ]

    records = []
    failures = []
    seen_urls = set()
    to_visit = start_urls.copy()

    max_urls = 8 if pilot else 50

    while to_visit:
        url = to_visit.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        if len(seen_urls) > max_urls:
            break

        print(f"Fetching: {url}")
        # Use longer timeout for PDFs since they are larger files
        timeout = 8.0 if url.lower().endswith(".pdf") else 2.0
        r = fetch(url, timeout=timeout)

        if r is None:
            failures.append({"url": url, "error": "FETCH_FAILED_OR_TIMEOUT", "type": "ACCESS_FAILED"})
            records.append({
                "record_id": str(uuid.uuid4()),
                "record_type": "UNKNOWN",
                "title": f"Failed Acquisition: {url}",
                "content": "",
                "source_url": url,
                "source_type": "UNKNOWN",
                "issuing_authority": "BIS",
                "authority_level": "SUPPORTING_GUIDANCE",
                "retrieved_at": now(),
                "source_sha256": "",
                "access_status": "FAILED",
                "extraction_status": "FAILED",
                "information_type": None,
                "official_portal": None,
            })
            continue

        content_bytes = r.content
        digest = sha256(content_bytes)

        key = digest[:32]
        d = RAW_DIR / key
        d.mkdir(parents=True, exist_ok=True)

        source_type = "PDF" if url.lower().endswith(".pdf") else "HTML"

        if source_type == "PDF":
            (d / "original.pdf").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_pdf(content_bytes)
        else:
            (d / "original.html").write_bytes(content_bytes)
            text_content, ext_status = extract_text_from_html(r.text)

            # Dynamic navigation: discover links from the page
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)
                # Stay within BIS domains
                if "bis.gov.in" not in parsed.netloc and "manakonline.in" not in parsed.netloc:
                    continue
                if full_url in seen_urls or full_url in to_visit:
                    continue
                # Apply the FAQ/guide filter
                if is_faq_guide_candidate(full_url):
                    # PDFs and guide/faq pages get priority
                    if full_url.lower().endswith(".pdf"):
                        to_visit.insert(0, full_url)
                    else:
                        to_visit.append(full_url)

        meta = {
            "source_url": url,
            "retrieved_at": now(),
            "http_status": r.status_code,
            "sha256": digest,
            "source_type": source_type,
        }
        (d / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        info_type = infer_information_type(url, text_content)

        records.append({
            "record_id": str(uuid.uuid4()),
            "record_type": "FAQ_GUIDE_DOCUMENT",
            "title": f"FAQ/Guide: {url.split('/')[-1] or 'overview'}",
            "content": text_content,
            "source_url": url,
            "source_type": source_type,
            "issuing_authority": "BIS",
            "authority_level": "SUPPORTING_GUIDANCE",
            "retrieved_at": now(),
            "source_sha256": digest,
            "access_status": "ACQUIRED",
            "extraction_status": ext_status,
            "information_type": info_type,
            "official_portal": urlparse(url).netloc,
        })
        time.sleep(0.5)

    # Write outputs
    with (OUT_DIR / "faq_guide_records.jsonl").open("w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with (OUT_DIR / "failures.jsonl").open("w", encoding="utf-8") as f:
        for item in failures:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    manifest = {
        "run_type": "PILOT" if pilot else "FULL",
        "timestamp": now(),
        "total_urls_discovered": len(seen_urls) + len(to_visit),
        "urls_crawled": len(seen_urls),
        "records_acquired": len([r for r in records if r.get("access_status") == "ACQUIRED"]),
        "failures": len(failures),
        "pdfs_extracted": len([r for r in records if r.get("source_type") == "PDF" and r.get("extraction_status") == "SUCCESS"]),
    }
    with open(OUT_DIR / "acquisition_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    if args.full:
        acquire(pilot=False)
    else:
        acquire(pilot=True)
