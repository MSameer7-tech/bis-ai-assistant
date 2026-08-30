"""
Script to register manually acquired or downloaded pilot documents with stable Document IDs and SHA-256 hashes.
"""

import argparse
import logging
from pathlib import Path
from ai.ingestion.acquisition import register_acquired_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Register acquired BIS pilot document artifact.")
    parser.add_argument("--document-id", required=True, help="Document ID (e.g. DOC-001)")
    parser.add_argument("--source-id", required=True, help="Source ID (e.g. SRC-001)")
    parser.add_argument("--file-path", required=True, help="File path in data/raw/...")
    parser.add_argument("--title", help="Official document title")
    parser.add_argument("--doc-number", help="Standard / Notification Number")
    parser.add_argument("--version", help="Version / Edition")
    parser.add_argument("--url", help="Official source URL")
    parser.add_argument("--notes", help="Provenance or acquisition notes")

    args = parser.parse_args()
    raw_path = ROOT_DIR / args.file_path if not Path(args.file_path).is_absolute() else Path(args.file_path)

    register_acquired_document(
        document_id=args.document_id,
        source_id=args.source_id,
        raw_file_path=raw_path,
        title=args.title,
        document_number=args.doc_number,
        version_edition=args.version,
        source_url=args.url,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
