# Document Acquisition Contract & Storage Architecture

**Document Version**: 1.0  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: Pre-flight HTTP Validation, Integrity Verification, and Raw Immutable Storage  

---

## 1. Pre-Flight Acquisition Verification

The acquisition pipeline must never rely solely on HTTP 200 response codes. Many government portals return HTTP 200 with HTML error bodies, Cloudflare captchas, or login redirects.

The acquisition engine must pass all 6 pre-flight validation gates:

```
Candidate Document URL
        ↓
[Gate 1: Whitelist Domain Validation] ──> Must match AUTHORIZED_GOV_DOMAINS
        ↓
[Gate 2: HTTP Status & SSL Validation] ──> Status == 200, Valid Government TLS Cert
        ↓
[Gate 3: Content-Type Header Check]   ──> 'application/pdf' or 'text/html'
        ↓
[Gate 4: Magic Byte Signature Check]  ──> '%PDF-' for PDF, '<!DOCTYPE' for HTML
        ↓
[Gate 5: Non-Empty Payload Check]     ──> Content length > 512 bytes
        ↓
[Gate 6: Cryptographic Hashing]       ──> Compute SHA-256 over entire binary stream
        ↓
PASSED: Ingest into Raw Immutable Storage
```

---

## 2. Storage Directory Architecture

```
data/
├── sources/
│   ├── source_families.json
│   ├── source_registry.json
│   ├── source_access_methods.json
│   ├── source_authority_levels.json
│   ├── source_version_rules.json
│   └── document_metadata_schema.json
├── raw/
│   └── bis/
│       └── <document_id>/
│           ├── original.pdf (or original.html)
│           └── metadata.json
└── manifests/
    └── acquisition/
        └── provenance_ledger.json
```

**Immutability Guarantee**: Raw acquired files are never edited or overwritten in place. If an amendment or newer version is published, it is stored under a new `document_id` or version directory, preserving historical auditability.
