import json
from pathlib import Path


def test_source_registry_exists_and_valid():
    registry_path = Path("data/metadata/source_registry.json")
    assert registry_path.exists(), "source_registry.json must exist"

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 10, "Registry should contain initial pilot sources"

    required_fields = {
        "source_id",
        "title",
        "document_type",
        "issuing_organization",
        "authority_tier",
        "domain",
        "status",
    }

    for item in data:
        for field in required_fields:
            assert field in item, f"Field '{field}' missing in item {item.get('source_id')}"
        assert item["status"] in ["pending", "acquired", "verified", "processed", "active", "superseded"]
