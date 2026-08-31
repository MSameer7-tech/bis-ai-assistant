import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client


# ============================================================
# Configuration
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "SUPABASE_SERVICE_ROLE_KEY is missing from .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

SOURCE_FILE = METADATA_DIR / "source_registry.json"
DOCUMENT_FILE = METADATA_DIR / "documents.json"


# ============================================================
# Helpers
# ============================================================

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require_field(record, field, record_name):
    value = record.get(field)

    if value is None or str(value).strip() == "":
        raise ValueError(
            f"{record_name}: required field '{field}' is missing"
        )

    return value


def normalize_datetime(value):
    if not value:
        return None

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).isoformat()
        except ValueError:
            return value

    return value


# ============================================================
# Sources
# ============================================================

def ingest_sources():

    print("\n=== Ingesting sources ===")

    records = load_json(SOURCE_FILE)

    if not isinstance(records, list):
        raise ValueError(
            "source_registry.json must contain a JSON array"
        )

    source_type_map = {
        "standard_document": "bis_standard",
        "qco_order": "qco",
        "scheme_regulation": "certification_document",
        "guideline": "guideline",
        "lab_directory": "laboratory",
    }

    processed = 0
    skipped = 0

    for record in records:

        external_source_id = require_field(
            record,
            "source_id",
            "source"
        )

        name = require_field(
            record,
            "title",
            external_source_id
        )

        url = record.get("source_url") or record.get("url")

        if not url:
            print(
                f"[SKIP] {external_source_id}: "
                "no URL"
            )
            skipped += 1
            continue

        source_type = source_type_map.get(
            record.get("source_type"),
            "other"
        )

        source_data = {
            "external_source_id": external_source_id,

            "name": name,

            "url": url,

            "source_type": source_type,

            "authority_level": (
                record.get("authority_level")
                or "unknown"
            ),

            "description": record.get("notes"),

            "last_verified_at": normalize_datetime(
                record.get("retrieval_date")
            ),
        }

        try:

            (
                supabase
                .table("sources")
                .upsert(
                    source_data,
                    on_conflict="external_source_id"
                )
                .execute()
            )

            print(
                f"[OK] {external_source_id} → {name}"
            )

            processed += 1

        except Exception as e:

            print(
                f"[ERROR] {external_source_id}: {e}"
            )

    print(
        f"\nSources complete: "
        f"{processed} processed, "
        f"{skipped} skipped."
    )


# ============================================================
# Documents
# ============================================================

def ingest_documents():

    print("\n=== Ingesting documents ===")

    records = load_json(DOCUMENT_FILE)

    if not isinstance(records, list):
        raise ValueError(
            "documents.json must contain a JSON array"
        )

    processed = 0
    skipped = 0

    for record in records:

        external_document_id = require_field(
            record,
            "document_id",
            "document"
        )

        title = require_field(
            record,
            "title",
            external_document_id
        )

        source_external_id = record.get("source_id")

        source_uuid = None

        # ----------------------------------------------------
        # Resolve SRC-XXX → Supabase UUID
        # ----------------------------------------------------

        if source_external_id:

            source_result = (
                supabase
                .table("sources")
                .select("id")
                .eq(
                    "external_source_id",
                    source_external_id
                )
                .limit(1)
                .execute()
            )

            if not source_result.data:

                print(
                    f"[SKIP] {external_document_id}: "
                    f"source {source_external_id} not found"
                )

                skipped += 1
                continue

            source_uuid = source_result.data[0]["id"]

        # ----------------------------------------------------
        # Determine document type
        # ----------------------------------------------------

        standard_number = record.get(
            "standard_or_document_number"
        )

        filename = (
            record.get("file_name") or ""
        ).lower()

        if (
            standard_number
            and standard_number.startswith("IS ")
        ):
            document_type = "standard"

        elif "cro" in filename:
            document_type = "qco"

        else:
            document_type = "other"

        # ----------------------------------------------------
        # Get source URL
        # ----------------------------------------------------

        source_url = None

        if source_uuid:

            source_result = (
                supabase
                .table("sources")
                .select("url")
                .eq("id", source_uuid)
                .limit(1)
                .execute()
            )

            if source_result.data:
                source_url = source_result.data[0]["url"]

        # ----------------------------------------------------
        # Build document
        # ----------------------------------------------------

        document_data = {

            "external_document_id":
                external_document_id,

            "source_id":
                source_uuid,

            "document_type":
                document_type,

            "title":
                title,

            "file_name":
                record.get("file_name"),

            "storage_path":
                record.get("file_path"),

            "source_url":
                source_url,

            "version":
                record.get("version_edition"),

            "published_date":
                None,

            "checksum":
                record.get("file_sha256"),
        }

        # ----------------------------------------------------
        # Upsert
        # ----------------------------------------------------

        try:

            (
                supabase
                .table("documents")
                .upsert(
                    document_data,
                    on_conflict="external_document_id"
                )
                .execute()
            )

            print(
                f"[OK] {external_document_id} → {title}"
            )

            processed += 1

        except Exception as e:

            print(
                f"[ERROR] {external_document_id}: {e}"
            )

    print(
        f"\nDocuments complete: "
        f"{processed} processed, "
        f"{skipped} skipped."
    )


# ============================================================
# Main
# ============================================================

def main():

    print("============================================")
    print(" BIS AI Assistant Metadata Ingestion")
    print("============================================")

    ingest_sources()

    ingest_documents()

    print("\n============================================")
    print(" Metadata ingestion completed")
    print("============================================")


if __name__ == "__main__":
    main()

# ============================================================
# Standards + Standard Versions
# ============================================================

import re


def parse_standard_number(full_number):
    """
    Convert:

        IS 16102 (Part 1) : 2012

    into:

        IS 16102 (Part 1)

    The year is treated as the version/publication year.
    """

    if not full_number:
        return None

    value = full_number.strip()

    # Remove the trailing year
    value = re.sub(
        r"\s*:\s*\d{4}\s*$",
        "",
        value
    )

    return value.strip()


def get_document_uuid(external_document_id):

    result = (
        supabase
        .table("documents")
        .select("id")
        .eq(
            "external_document_id",
            external_document_id
        )
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]["id"]


def ingest_standards_and_versions():

    print("\n=== Ingesting standards + versions ===")

    records = load_json(DOCUMENT_FILE)

    standards_processed = 0
    versions_processed = 0
    skipped = 0

    for record in records:

        document_external_id = record.get(
            "document_id"
        )

        full_standard_number = record.get(
            "standard_or_document_number"
        )

        title = record.get("title")

        # ----------------------------------------------------
        # Only process Indian Standards
        # ----------------------------------------------------

        if not full_standard_number:
            print(
                f"[SKIP] {document_external_id}: "
                "missing standard/document number"
            )
            skipped += 1
            continue

        if not full_standard_number.startswith("IS "):

            print(
                f"[SKIP] {document_external_id}: "
                f"not an Indian Standard ({full_standard_number})"
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Parse base standard number
        # ----------------------------------------------------

        standard_number = parse_standard_number(
            full_standard_number
        )

        if not standard_number:
            print(
                f"[SKIP] {document_external_id}: "
                "could not parse standard number"
            )
            skipped += 1
            continue

        # ----------------------------------------------------
        # Find or create standard
        # ----------------------------------------------------

        try:

            standard_result = (
                supabase
                .table("standards")
                .upsert(
                    {
                        "standard_number":
                            standard_number,

                        "title":
                            title,

                        "description":
                            None,

                        "status":
                            "active",
                    },
                    on_conflict="standard_number"
                )
                .execute()
            )

            if not standard_result.data:
                raise RuntimeError(
                    "Standard upsert returned no data"
                )

            standard_id = standard_result.data[0]["id"]

            standards_processed += 1

        except Exception as e:

            print(
                f"[ERROR] {document_external_id} "
                f"standard: {e}"
            )

            continue

        # ----------------------------------------------------
        # Find document UUID
        # ----------------------------------------------------

        document_id = get_document_uuid(
            document_external_id
        )

        if not document_id:

            print(
                f"[SKIP] {document_external_id}: "
                "document not found"
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Extract year
        # ----------------------------------------------------

        year_match = re.search(
            r"(\d{4})\s*$",
            full_standard_number
        )

        publication_date = None

        if year_match:

            year = year_match.group(1)

            publication_date = f"{year}-01-01"

        # ----------------------------------------------------
        # Edition
        # ----------------------------------------------------

        edition = record.get(
            "version_edition"
        )

        if not edition:

            edition = f"Edition {year_match.group(1)}" \
                if year_match else "Unknown"

        # ----------------------------------------------------
        # Determine status
        # ----------------------------------------------------

        record_status = (
            record.get("status") or ""
        ).lower()

        if "withdrawn" in record_status:

            version_status = "withdrawn"

        elif "superseded" in record_status:

            version_status = "superseded"

        elif "draft" in record_status:

            version_status = "draft"

        else:

            version_status = "active"

        # ----------------------------------------------------
        # External version ID
        # ----------------------------------------------------

        external_version_id = (
            f"{document_external_id}-v1"
        )

        # ----------------------------------------------------
        # Create standard version
        # ----------------------------------------------------

        version_data = {

            "standard_id":
                standard_id,

            "document_id":
                document_id,

            "edition":
                edition,

            "publication_date":
                publication_date,

            "effective_date":
                None,

            "status":
                version_status,

            "external_version_id":
                external_version_id,
        }

        try:

            (
                supabase
                .table("standard_versions")
                .upsert(
                    version_data,
                    on_conflict="external_version_id"
                )
                .execute()
            )

            print(
                f"[OK] {document_external_id} → "
                f"{standard_number} → {edition}"
            )

            versions_processed += 1

        except Exception as e:

            print(
                f"[ERROR] {document_external_id} "
                f"version: {e}"
            )

    print(
        f"\nStandards processed: "
        f"{standards_processed}"
    )

    print(
        f"Versions processed: "
        f"{versions_processed}"
    )

    print(
        f"Skipped: {skipped}"
    )
