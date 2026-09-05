# Source Provenance & Chain of Custody Policy

**Document Version**: 1.1  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: Mandatory Metadata Preservation, Provenance Ledgers, and Zero-Unverified-Source Gate  

---

## 1. 3-Block Provenance Architecture

To prevent conflating document characteristics with network endpoint parameters, every document in the evidence registry carries 3 distinct metadata blocks:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DOCUMENT BLOCK                                                      │
│    - document_id, document_family_id, title, document_type, authority, │
│      authority_class, status, edition_year, normalized dates.          │
├────────────────────────────────────────────────────────────────────────┤
│ 2. SOURCE ENDPOINT BLOCK                                               │
│    - source_id, source_family_id, source_name, canonical_source_url,   │
│      source_ownership.                                                 │
├────────────────────────────────────────────────────────────────────────┤
│ 3. ACQUISITION BLOCK                                                   │
│    - retrieved_at, final_url, http_status, content_type, sha256,       │
│      file_type, acquisition_method, tls_verified, validation_passed.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Reusable Acquisition Gate Policy

Every document ingestion pipeline must execute the authoritative gate function from `ai/acquisition/source_gate.py`:

```python
from ai.acquisition.source_gate import is_source_acquisition_eligible

if not is_source_acquisition_eligible(source_endpoint):
    raise AcquisitionSecurityError(f"Endpoint {source_endpoint['source_id']} not eligible for acquisition")
```

---

## 3. Zero-Unverified-Source Gate

```
┌────────────────────────────────────────────────────────────────────────┐
│  NO VALID SOURCE_ID or NON-WHITELISTED DOMAIN                          │
│                         ↓                                              │
│                  UNTRUSTED SOURCE                                      │
│                         ↓                                              │
│         REJECTED BEFORE EXTRACT & INDEX PIPELINE                       │
│                         ↓                                              │
│         CANNOT ENTER PRODUCTION EVIDENCE REGISTRY                      │
└────────────────────────────────────────────────────────────────────────┘
```
