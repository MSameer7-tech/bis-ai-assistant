import json
from pathlib import Path

from ai.acquisition.url_normalizer import normalize_url


def test_source_registry_exists_and_valid():
    registry_path = Path("data/metadata/source_registry.json")
    assert registry_path.exists(), "source_registry.json must exist"

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 12, "Registry should contain all 12 audited pilot sources"

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
        "needs_verification",
        "superseded",
        "withdrawn",
        "CHUNKED",
        "INDEXED",
    }

    for item in data:
        for field in required_fields:
            assert field in item, f"Field '{field}' missing in item {item.get('source_id')}"
        assert (
            item["status"] in valid_statuses
        ), f"Invalid status '{item['status']}' in item {item.get('source_id')}"
        assert item["url"].startswith("http"), f"Invalid or missing URL in item {item.get('source_id')}"


def test_source_urls_are_raw():
    """Verify all URLs across source registry are raw HTTP/HTTPS URLs without Markdown formatting (Step 2)."""
    registry_path = Path("data/metadata/source_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        sources = json.load(f)

    for source in sources:
        for url_field in ("url", "source_url", "official_url"):
            url = source.get(url_field, "")
            if url:
                assert not url.startswith("["), f"{url_field} in {source.get('source_id')} starts with '[': {url}"
                assert "](" not in url, f"{url_field} in {source.get('source_id')} contains Markdown link syntax: {url}"
                assert url.startswith(("http://", "https://")), f"{url_field} in {source.get('source_id')} is not a valid http/https URL: {url}"


def test_markdown_url_is_normalized():
    """Verify normalize_url strips Markdown and bracket artifacts."""
    raw1 = "[https://archive.org/details/gov.in.is.16102.1.2012](https://archive.org/details/gov.in.is.16102.1.2012)"
    assert normalize_url(raw1) == "https://archive.org/details/gov.in.is.16102.1.2012"

    raw2 = "[https://example.com](https://example.com)"
    assert normalize_url(raw2) == "https://example.com"

    raw3 = "[Named Source Link](https://www.bis.gov.in/standards)"
    assert normalize_url(raw3) == "https://www.bis.gov.in/standards"

    raw4 = "[https://crsbis.in]"
    assert normalize_url(raw4) == "https://crsbis.in"

    raw5 = "https://archive.org/details/test](https://archive.org/details/test)"
    assert normalize_url(raw5) == "https://archive.org/details/test"

    raw6 = "https://already.clean.url/doc.pdf"
    assert normalize_url(raw6) == "https://already.clean.url/doc.pdf"
