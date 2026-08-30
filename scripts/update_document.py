"""
CLI Tool to Execute the Incremental Update Pipeline (Step 11).
Usage:
    python scripts/update_document.py --document-id DOC-001 --pdf-path data/raw/standards/IS_16102_Part_1_2012.pdf
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.ingestion.update_pipeline import IncrementalUpdatePipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Trigger incremental knowledge update pipeline for a BIS document.")
    parser.add_argument("--document-id", required=True, help="Document ID (e.g. DOC-001)")
    parser.add_argument("--pdf-path", required=True, help="Path to new/updated PDF")
    parser.add_argument("--version-label", help="Optional version label (e.g. IS 16102 Part 1 : 2026)")
    parser.add_argument("--force", action="store_true", help="Force reprocessing even if SHA matches")
    args = parser.parse_args()

    pipeline = IncrementalUpdatePipeline()
    res = pipeline.process_updated_document(
        document_id=args.document_id,
        new_pdf_path=Path(args.pdf_path),
        version_label=args.version_label,
        force=args.force,
    )

    print("\n" + "=" * 90)
    print(f"🔄 INCREMENTAL UPDATE PIPELINE EXECUTION REPORT FOR {args.document_id}:")
    print("=" * 90)
    print(f"Status: {res.get('status')} | Version ID: {res.get('version_id', 'N/A')}")
    print(f"SHA-256: {res.get('sha256', 'N/A')}")
    print(f"Total Chunks: {res.get('total_chunks', 0)}")
    print(f"⚡ Vectors Requiring Embedding: {res.get('reembed_required_count', 0)}")
    print(f"🟢 Unchanged Vectors Reused:    {res.get('unchanged_chunks_count', 0)}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
