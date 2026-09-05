# Acquisition Manifest Schema & Provenance Architecture (Phase 3G & 3H)

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Authoritative Acquisition Manifest Structure and Immutability Standards  

---

## 1. Top-Level Manifest Structure

The acquisition manifest at `data/acquisition/manifests/acquisition_manifest.json` provides the complete machine-readable audit trail of all acquired documents:

```json
{
  "manifest_version": "1.0",
  "phase": "Phase 3: Bulk BIS Data Discovery & Acquisition",
  "generated_at": "2026-09-02T00:54:00Z",
  "total_discovered": 111,
  "total_validated": 111,
  "total_acquired": 111,
  "total_failures": 0,
  "total_quarantined": 0,
  "total_relationships": 30,
  "documents": [ ... ],
  "relationships": [ ... ]
}
```

---

## 2. 3-Block Document Provenance Entry

Every entry in `documents` conforms strictly to `data/sources/document_metadata_schema.json`:

```json
{
  "document": {
    "document_id": "IS-1786-2008",
    "document_family_id": "IS-1786",
    "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
    "document_type": "INDIAN_STANDARD",
    "authority": "Bureau of Indian Standards",
    "authority_class": "PRIMARY_NORMATIVE",
    "edition_year": 2008,
    "status": "CURRENT"
  },
  "source": {
    "source_id": "SRC-001",
    "source_family_id": "SRCF-001",
    "source_name": "BIS Know Your Standard Portal",
    "canonical_source_url": "https://www.bis.gov.in/know-your-standard/",
    "source_ownership": "BIS_PUBLISHED"
  },
  "acquisition": {
    "retrieved_at": "2026-09-02T00:54:03Z",
    "final_url": "https://www.bis.gov.in/standards/IS-1786-2008.pdf",
    "http_status": 200,
    "content_type": "application/pdf",
    "content_length_bytes": 1024,
    "sha256": "4a5b6c...",
    "file_type": "PDF",
    "acquisition_method": "HTTPS_GET_STREAM",
    "tls_verified": true,
    "validation_passed": true,
    "deduplication_result": "DISTINCT_DOCUMENT",
    "storage_path": "data/raw/immutable/IS-1786-2008/original.pdf"
  }
}
```
