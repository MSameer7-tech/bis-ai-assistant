import json
import os
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
    """Load a JSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require_field(record, field, record_name):
    """Ensure a required field exists."""

    value = record.get(field)

    if value is None or str(value).strip() == "":
        raise ValueError(
            f"{record_name}: required field '{field}' is missing"
        )

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

    inserted = 0
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
                "no URL/source_url"
            )
            skipped += 1
            continue

        # ----------------------------------------------------
        # Convert metadata to our Supabase representation
        # ----------------------------------------------------

        source_data = {
            "external_source_id": external_source_id,

            "name": name,

            "url": url,

            "source_type": (
                record.get("source_type")
                or "other"
            ),

            "authority_level": (
                record.get("authority_level")
                or "unknown"
            ),

            "description": record.get("notes"),

            "last_verified_at": (
                record.get("retrieval_date")
            ),
        }

        # ----------------------------------------------------
        # Upsert
        # ----------------------------------------------------

        try:
            result = (
                supabase
                .table("sources")
                .upsert(
                    source_data,
                    on_conflict="external_source_id"
                )
                .execute()
            )

            print(
                f"[OK] {external_source_id} → "
                f"{name}"
            )

            inserted += 1

        except Exception as e:
            print(
                f"[ERROR] {external_source_id}: {e}"
            )

    print(
        f"\nSources complete: "
        f"{inserted} processed, "
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
                    f"source {source_external_id} "
                    f"not found"
                )

                skipped += 1
                continue

            source_uuid = source_result.data[0]["id"]

        # ----------------------------------------------------
        # Determine document type
        # ----------------------------------------------------

        standard_number = (
            record.get(
                "standard_or_document_number"
            )
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
        # Build Supabase record
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
                None,

            "version":
                record.get("version_edition"),

            "published_date":
                None,

            "checksum":
                record.get("file_sha256"),
        }

        # ----------------------------------------------------
        # Resolve source URL
        # ----------------------------------------------------

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
                document_data["source_url"] = (
                    source_result.data[0]["url"]
                )

        # ----------------------------------------------------
        # Upsert document
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
                f"[OK] {external_document_id} → "
                f"{title}"
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
