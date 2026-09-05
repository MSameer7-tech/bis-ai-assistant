# Phase 3 Acceptance Criteria & Quality Gate Checklist

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Verification Standards for Releasing Phase 3 and Entering Phase 4  

---

## 1. Quality Gates

| Gate ID | Criterion | Requirement | Status |
|---|---|---|:---:|
| **G3-01** | Multi-Source Discovery | Discovery engine traverses all 18 registered source endpoints. | **PASS** |
| **G3-02** | Candidate Gating | Candidate validator enforces domain whitelisting and quarantines invalid URLs. | **PASS** |
| **G3-03** | Streamed Acquisition | Secure downloading with strict TLS verification and redirect tracking. | **PASS** |
| **G3-04** | Magic-Byte Content Validation | Binary signature validation (`%PDF-`, HTML tags, JSON) prevents masquerading errors. | **PASS** |
| **G3-05** | Structured Identity Generation | Deterministic IDs generated according to `source_version_rules.json`. | **PASS** |
| **G3-06** | 4-Way SHA-256 Deduplication | Accurate classification of unchanged, changed, duplicate, and distinct items. | **PASS** |
| **G3-07** | Discovered Relationships | Explicit cross-document links (amendments, manuals, SIT) captured with provenance. | **PASS** |
| **G3-08** | Immutable Raw Storage | Raw files stored immutably with sidecar `metadata.json` in `data/raw/immutable/`. | **PASS** |
| **G3-09** | Authoritative Manifest | Comprehensive manifest generated conforming to `document_metadata_schema.json`. | **PASS** |
| **G3-10** | Automated Test Suite | Pytest suite in `tests/acquisition/test_bulk_acquisition.py` passes 100%. | **PASS** |
