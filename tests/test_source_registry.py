import json
from pathlib import Path


def test_source_registry_exists_and_valid():
    registry_path = Path("data/metadata/source_registry.json")
    assert registry_path.exists(), "source_registry.json must exist"

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 8, "Registry should contain verified pilot sources"

    required_fields = {
        "source_id",
        "domain",
        "source_type",
        "issuing_authority",
        "authority_level",
        "title",
        "standard_or_document_number",
        "version_edition",
        "publication_date",
        "effective_date",
        "url",
        "retrieval_date",
        "status",
        "notes",
    }

    valid_statuses = {
        "discovered",
        "official_domain_verified",
        "document_identified",
        "document_acquired",
        "content_verified",
        "metadata_verified",
        "current_status_verified",
        "superseded",
        "withdrawn",
    }

    for item in data:
        for field in required_fields:
            assert field in item, f"Field '{field}' missing in item {item.get('source_id')}"
        assert (
            item["status"] in valid_statuses
        ), f"Invalid status '{item['status']}' in item {item.get('source_id')}"
        assert item["url"].startswith("http"), f"Invalid or missing URL in item {item.get('source_id')}"
