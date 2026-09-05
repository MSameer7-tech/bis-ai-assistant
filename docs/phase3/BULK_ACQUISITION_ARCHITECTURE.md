# Bulk BIS Data Discovery & Acquisition Architecture

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Generic Multi-Source Discovery, Candidate Validation, Streamed Acquisition, and Immutable Raw Storage  

---

## 1. Executive Summary

Phase 3 implements the generic, scalable acquisition engine that turns official registered BIS and statutory endpoints into an immutable, cryptographically verified raw regulatory corpus.

In accordance with our scope boundaries, the acquisition engine operates across the broader BIS knowledge base rather than restricting ingestion to a static 25-product boundary.

```
       REGISTERED SOURCE ENDPOINTS (SRC-001 to SRC-018)
                              │
                              ▼
      [3A. DISCOVERY ENGINE] (discovery_engine.py)
      Queries search portals, catalogs, gazette engines
                              │
                              ▼
        Candidate Documents (candidate_documents.json)
                              │
                              ▼
      [3B. CANDIDATE VALIDATOR] (candidate_validator.py)
      Domain whitelisting, schema checks, quarantine
                              │
                              ▼
      [3C. STREAMED ACQUISITION] (pipeline_downloader.py)
      HTTPS streaming, strict TLS, rate limiting, redirects
                              │
                              ▼
      [3D. CONTENT VALIDATION] (content_validator.py)
      Magic bytes (%PDF-, HTML, JSON), anti-masquerade
                              │
                              ▼
      [3E. IDENTITY & DEDUPLICATION] (identity_resolver.py)
      Structured ID generation, SHA-256 4-way decision
                              │
                              ▼
      [3F. RELATIONSHIP DISCOVERY] (relationship_discoverer.py)
      Discovers Amendments, Manuals, SIT, QCO links
                              │
                              ▼
      [3G. IMMUTABLE RAW STORAGE] (data/raw/immutable/<doc_id>/)
      original.pdf/html + sidecar metadata.json
                              │
                              ▼
      [3H. AUTHORITATIVE MANIFEST] (acquisition_manifest.json)
```

---

## 2. Core Sub-Phase Specifications

- **3A. Discovery Engine**: Traverses all 18 registered endpoints and discovers candidate items without hardcoding static product lists.
- **3B. Candidate Validation**: Authoritative security gate checking domain namespaces against `AUTHORIZED_GOV_DOMAINS` and routing invalid links to quarantine.
- **3C. Streamed Acquisition**: High-reliability downloader with strict TLS, exponential backoff, and redirect verification.
- **3D. Content Validation**: Magic-byte inspection ensuring that HTML error pages or corrupted payloads are never recorded as PDFs.
- **3E. Identity & Deduplication**: Generates structured IDs (e.g. `IS-16046-P2-2018`, `QCO-DPIIT-SO1245E-2023`) and enforces the 4-way hash review policy.
- **3F. Discovered Relationships**: Captures verified links (`AMENDS`, `CERTIFICATION_GUIDELINE_FOR`, `TESTING_SCHEDULE_FOR`, `MANDATES_CERTIFICATION_FOR`) with provenance.
- **3G. Immutable Storage**: Raw files are permanently stored under `data/raw/immutable/<doc_id>/` and are never modified in place.
- **3H. Authoritative Manifest**: Compiled at `data/acquisition/manifests/acquisition_manifest.json`.
