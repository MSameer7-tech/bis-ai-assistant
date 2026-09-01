import pytest
from ai.acquisition.http_client import ResilientHTTPClient


def test_http_client_initialization():
    client = ResilientHTTPClient()
    assert client.max_retries == 3
    assert client.base_backoff == 1.0


def test_http_client_handles_nonexistent_url():
    client = ResilientHTTPClient(max_retries=1)
    content, tele = client.fetch_url("https://localhost.invalid/nonexistent.pdf", catalog_id="TEST-FAIL", timeout=0.5)
    assert content is None
    assert tele["success"] is False
