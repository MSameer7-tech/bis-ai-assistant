import json
import shutil
from pathlib import Path

MANIFEST_PATH = Path("data/processed/extraction_manifest.json")
EVIDENCE_UNITS_ROOT = Path("data/processed/evidence_units")

with open(MANIFEST_PATH, "r") as f:
    manifest = json.load(f)

success_docs = {d["document_id"] for d in manifest["classifications"]["EXTRACTION_SUCCESS"]}

stale_folders = []
for doc_dir in EVIDENCE_UNITS_ROOT.iterdir():
    if not doc_dir.is_dir(): continue
    if doc_dir.name not in success_docs:
        stale_folders.append(doc_dir)

print(f"Found {len(stale_folders)} stale folders. They belong to documents that are no longer EXTRACTION_SUCCESS.")
for f in stale_folders:
    print(f"Removing {f}")
    shutil.rmtree(f)

