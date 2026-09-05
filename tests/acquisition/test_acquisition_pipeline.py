import json
import pytest
from pathlib import Path
from ai.acquisition.identity_resolver import IdentityResolver, DeduplicationDecision

def test_same_id_same_sha(tmp_path):
    registry_path = tmp_path / "registry.json"
    resolver = IdentityResolver(registry_path=registry_path)
    resolver.known_id_to_hash = {"DOC-1": "abc123sha"}
    resolver.known_hash_to_ids = {"abc123sha": {"DOC-1"}}
    
    dec = resolver.resolve_deduplication("DOC-1", "FAM-1", "abc123sha")
    assert dec.deduplication_status == "UNCHANGED_DOCUMENT"

def test_same_id_different_sha(tmp_path):
    registry_path = tmp_path / "registry.json"
    resolver = IdentityResolver(registry_path=registry_path)
    resolver.known_id_to_hash = {"DOC-1": "abc123sha"}
    resolver.known_hash_to_ids = {"abc123sha": {"DOC-1"}}
    
    dec = resolver.resolve_deduplication("DOC-1", "FAM-1", "new456sha")
    assert dec.deduplication_status == "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW"

def test_different_id_same_sha(tmp_path):
    registry_path = tmp_path / "registry.json"
    resolver = IdentityResolver(registry_path=registry_path)
    resolver.known_id_to_hash = {"DOC-1": "abc123sha"}
    resolver.known_hash_to_ids = {"abc123sha": {"DOC-1"}}
    
    dec = resolver.resolve_deduplication("DOC-2", "FAM-2", "abc123sha")
    assert dec.deduplication_status == "DUPLICATE_REPRESENTATION_ALIAS"
    assert "DOC-1" in dec.alias_of_document_ids

def test_different_id_different_sha(tmp_path):
    registry_path = tmp_path / "registry.json"
    resolver = IdentityResolver(registry_path=registry_path)
    resolver.known_id_to_hash = {"DOC-1": "abc123sha"}
    resolver.known_hash_to_ids = {"abc123sha": {"DOC-1"}}
    
    dec = resolver.resolve_deduplication("DOC-2", "FAM-2", "new456sha")
    assert dec.deduplication_status == "DISTINCT_DOCUMENT"

def test_html_masquerading_as_pdf(tmp_path):
    from ai.acquisition.content_validator import ContentValidator
    v = ContentValidator()
    
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"<!doctype html><html><body>Error</body></html>")
    
    ok, err = v.validate_file(fake_pdf, "PDF")
    assert not ok
    assert "masquerading" in err.lower() or "expected pdf" in err.lower()

def test_zero_byte_response(tmp_path):
    from ai.acquisition.content_validator import ContentValidator
    v = ContentValidator()
    
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    
    ok, err = v.validate_file(empty_file, "PDF")
    assert not ok
    assert "too small" in err.lower()
