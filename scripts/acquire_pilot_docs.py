"""
Script to acquire and register pilot documents into data/raw/ with SHA-256 cryptographic provenance.
"""

import argparse
import hashlib
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
METADATA_DIR = ROOT_DIR / "data" / "metadata"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, destination: Path) -> Path:
    """Downloads a file from a URL with standard user-agent header."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BIS-AI-Assistant/1.0"},
    )
    logger.info("Fetching: %s -> %s", url, destination)
    with urllib.request.urlopen(req, timeout=30) as response, open(destination, "wb") as out_file:
        data = response.read()
        out_file.write(data)
    return destination


def register_document(
    source_id: str,
    raw_file_path: Path,
    source_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Updates source_registry.json with file path, SHA-256 hash, and status."""
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Target file does not exist: {raw_file_path}")

    file_hash = compute_sha256(raw_file_path)
    file_size = raw_file_path.stat().st_size
    rel_path = raw_file_path.relative_to(ROOT_DIR)
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    record_found = False
    updated_item = {}

    for item in registry:
        if item["source_id"] == source_id:
            item["file_path"] = str(rel_path)
            item["file_sha256"] = file_hash
            item["file_size_bytes"] = file_size
            item["retrieval_date"] = timestamp
            item["status"] = "document_acquired"
            if source_url:
                item["url"] = source_url
            if notes:
                item["notes"] = notes
            record_found = True
            updated_item = item
            break

    if not record_found:
        raise ValueError(f"Source ID '{source_id}' not found in registry {REGISTRY_PATH}")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    logger.info(
        "✅ Registered %s: %s (Size: %d bytes, SHA-256: %s...)",
        source_id,
        rel_path,
        file_size,
        file_hash[:16],
    )
    return updated_item


def main():
    parser = argparse.ArgumentParser(description="Acquire and register BIS pilot documents.")
    parser.add_argument("--source-id", required=True, help="Source ID (e.g. SRC-001)")
    parser.add_argument("--file-path", help="Local file path if already downloaded")
    parser.add_argument("--url", help="Download URL")
    parser.add_argument("--dest", help="Destination file path in data/raw/...")
    parser.add_argument("--notes", help="Optional notes on acquisition")

    args = parser.parse_args()

    if args.url and args.dest:
        dest_path = ROOT_DIR / args.dest
        download_file(args.url, dest_path)
        register_document(args.source_id, dest_path, source_url=args.url, notes=args.notes)
    elif args.file_path:
        local_path = ROOT_DIR / args.file_path if not Path(args.file_path).is_absolute() else Path(args.file_path)
        register_document(args.source_id, local_path, source_url=args.url, notes=args.notes)
    else:
        logger.error("Must provide either --file-path OR (--url and --dest)")


if __name__ == "__main__":
    main()
