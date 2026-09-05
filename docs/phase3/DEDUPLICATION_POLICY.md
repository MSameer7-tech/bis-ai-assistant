# Deduplication & Hash Review Policy (Phase 3E)

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: 4-Way SHA-256 Decision Matrix and Review Triggering  

---

## 1. The 4-Way Deduplication Decision Matrix

Every acquired file is compared against existing repository records using its canonical identity (`document_id`) and cryptographic content hash (`sha256`):

| Canonical ID Match | SHA-256 Hash Match | Deduplication Classification | Operational Decision |
|---|---|---|---|
| **YES (Same ID)** | **YES (Same Hash)** | `UNCHANGED_DOCUMENT` | Keep existing raw file; no re-parsing or vector mutation needed. |
| **YES (Same ID)** | **NO (Different Hash)** | `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW` | Route to version review queue. Compare metadata to determine if it is an erratum, amendment, or revision. Do NOT blindly overwrite. |
| **NO (Different ID)** | **YES (Same Hash)** | `DUPLICATE_REPRESENTATION_ALIAS` | Register cross-listing alias in provenance ledger without duplicating storage or vector chunks. |
| **NO (Different ID)** | **NO (Different Hash)** | `DISTINCT_DOCUMENT` | Ingest as new unique regulatory document. |

---

## 2. Integrity Guarantee

- Raw binary files in `data/raw/immutable/` remain strictly immutable.
- A new version or updated PDF is stored under a distinct revision directory or updated sidecar ledger, preserving historical legal auditability.
