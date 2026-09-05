# Discovered Relationship Specification (Phase 3F)

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Formal Relationship Models Between Standards, Amendments, Manuals, SIT, and QCOs  

---

## 1. Explicit Relationship Types

Relationships between discovered entities are established only through explicit document linkages and authoritative metadata, never through filename guessing:

```mermaid
graph TD
    STD["Indian Standard (IS 1786:2008)"]
    AMD["Amendment Slip (IS 1786:2008-A1)"]
    PM["Product Manual (PM-IS-1786-2008-V1)"]
    SIT["SIT Schedule (SIT-IS-1786-2008-NOV2021)"]
    QCO["Gazette QCO (QCO-DPIIT-SO1245E-2023)"]

    AMD -->|AMENDS| STD
    PM -->|CERTIFICATION_GUIDELINE_FOR| STD
    SIT -->|TESTING_SCHEDULE_FOR| STD
    QCO -->|MANDATES_CERTIFICATION_FOR| STD
```

---

## 2. Relationship Schema

Each relationship entry in `data/acquisition/manifests/acquisition_manifest.json` contains:
- `source_document_id`: Origin document ID (e.g. `IS-1786-2008-A1`)
- `target_document_id`: Target document ID (e.g. `IS-1786-2008`)
- `relationship_type`: Formal enum code (`AMENDS`, `CERTIFICATION_GUIDELINE_FOR`, `TESTING_SCHEDULE_FOR`, `MANDATES_CERTIFICATION_FOR`)
- `confidence`: $1.0$ (deterministic binding)
- `discovered_via`: Source endpoint ID (e.g. `SRC-003`)
- `provenance_metadata`: Additional context (edition year, ministry, etc.)
