# Content Validation & Anti-Corruption Specification (Phase 3D)

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Binary Signature Verification, Magic Bytes, and Anti-Masquerading Rules  

---

## 1. Magic Byte & Format Verification Rules

To protect the trusted evidence registry from corrupted downloads, login redirects, or HTML error pages served with HTTP 200 codes, the acquisition engine verifies magic bytes:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PDF Documents:                                                      │
│    - Byte signature must begin with '%PDF-' (0x25 0x50 0x44 0x46 0x2D).│
│    - Rejects any PDF stream containing '<!DOCTYPE html' or '<html'.    │
├────────────────────────────────────────────────────────────────────────┤
│ 2. HTML Documents:                                                     │
│    - Byte stream must contain '<!doctype html', '<html', or '<body'.   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. JSON Structured Records:                                            │
│    - Byte stream must parse cleanly as valid JSON object or array.     │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Payload Size Gate:                                                  │
│    - Payload must be non-empty (minimum 32 bytes for valid metadata).  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Anti-Masquerading Gate

If an endpoint returns `Content-Type: application/pdf` but the payload begins with HTML tags, the validator explicitly classifies it as:
$$\text{CONTENT\_VALIDATION\_FAILED: Corrupted / Masquerading HTML Error Page}$$
The file is immediately rejected and quarantined, preventing false documents from polluting the corpus.
