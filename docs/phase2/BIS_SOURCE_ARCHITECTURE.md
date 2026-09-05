# BIS & Statutory Knowledge Source Architecture

**Document Version**: 1.0  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: End-to-End Source Discovery, Authority Tiering, and Access Protocols  

---

## 1. Architectural Philosophy

The **BIS AI Technical Assistant** relies on an immutable regulatory chain of custody. If the system cannot establish the official provenance of a regulatory fact, that fact is prohibited from entering the production evidence index.

```
       SOURCE FAMILY (12 Families in source_families.json)
                              ↓
      OFFICIAL ENDPOINT (18 Endpoints in source_registry.json)
                              ↓
        ACCESS PROTOCOL (source_access_methods.json)
                              ↓
      DISCOVERY & IDENTITY (source_version_rules.json)
                              ↓
      RAW IMMUTABLE STORAGE + SHA-256 (document_metadata_schema.json)
                              ↓
     TRUSTED EVIDENCE REGISTRY (Primary & Operational Tiers)
```

---

## 2. Core Architectural Principles

1. **Decoupled Discovery**: The acquisition layer discovers standards, gazette orders, manuals, and test schedules dynamically using official endpoints rather than hardcoding static document lists.
2. **Authority-Tiered Reasoning**: 
   - Factual specifications and mandatory legal status require `PRIMARY_NORMATIVE` sources (Gazette QCOs, Standards, SIT).
   - Factory guidelines, grouping, and lab scopes use `OFFICIAL_OPERATIONAL` sources (Product Manuals, Lab Registers).
   - Informative advice uses `OFFICIAL_INFORMATIVE` sources (FAQs, Booklets).
3. **Deterministic Identity vs Content Hash**:
   - `document_id` (e.g. `IS-1786-2008`) identifies the statutory entity.
   - `sha256` hash identifies the exact binary content payload retrieved.
4. **Zero Untrusted Ingestion**: Non-whitelisted domains (commercial PDF sellers, engineering blogs, unverified forums) are systematically blocked at the discovery and acquisition gate.
