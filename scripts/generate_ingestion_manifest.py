"""
CLI Script to Generate / Refresh data/metadata/ingestion_manifest.json (Step 10).
"""

import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.ingestion.manifest import IngestionManifestManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    manager = IngestionManifestManager()
    manifest = manager.generate_manifest()

    print("\n" + "=" * 95)
    print(f"📋 BIS INGESTION MANIFEST AUDIT ({manifest['total_documents']} Documents Registered):")
    print("=" * 95)
    print(f"{'Doc ID':<10} | {'Status':<12} | {'Chunks':<8} | {'Requires Reindex':<18} | {'Standard'}")
    print("-" * 95)

    for doc_id, data in manifest["documents"].items():
        st = data.get("status", "UNKNOWN")
        ch = data.get("total_chunks", 0)
        reidx = str(data.get("requires_reindex", False))
        std = str(data.get("standard_number", ""))[:32]
        print(f"{doc_id:<10} | {st:<12} | {ch:<8} | {reidx:<18} | {std}")

    print("=" * 95)
    print(f"Manifest written to: data/metadata/ingestion_manifest.json (Last Run: {manifest['last_run']})\n")


if __name__ == "__main__":
    main()
