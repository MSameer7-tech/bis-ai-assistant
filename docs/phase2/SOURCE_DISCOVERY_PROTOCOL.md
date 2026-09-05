# Source Discovery Protocol & Ingestion Workflows

**Document Version**: 1.0  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: Algorithmic Workflows for Discovering and Normalizing Official Candidate Documents  

---

## 1. Discovery Workflows by Input Query Type

```
User Query / Product Description
        ↓
[1. Product & Intent Resolver] ──> Standard Candidate (e.g. IS 1786)
        ↓
[2. Source Endpoint Router]    ──> Maps to SRC-001 (KYS), SRC-004 (Gazette), SRC-006 (PM)
        ↓
[3. Protocol Execution]        ──> HTML Search / PDF Link Extraction / Gazette Query
        ↓
[4. Candidate Normalization]   ──> Extracts Title, Edition, Amendment Slips, Status
        ↓
[5. Identity & Validation]     ──> Assigns DOC-ID, Verifies SHA-256, Validates PDF Structure
        ↓
[6. Evidence Registration]     ──> Ingests into Raw Storage & Provenance Ledger
```

---

## 2. Discovery Matrix by Source Family

| Source Family | Primary Input Trigger | Discovery Method | Validation Protocol | Output Candidate Schema |
|---|---|---|---|---|
| **SRCF-001 (Standards)** | Standard Code / Product Keyword | `HTML_SEARCH` against `SRC-001` | Exact standard number regex + title match | `StandardRecord` (ID, edition, clauses) |
| **SRCF-002 (Amendments)** | Base Standard ID | `PDF_LINK_DISCOVERY` against `SRC-003` | Parent link check + amendment sequence | `AmendmentRecord` (A1..An, slip number) |
| **SRCF-003 (QCOs)** | Commodity / Standard / Ministry | `SEARCH_ENDPOINT` against `SRC-004` & `SRC-005` | Gazette S.O. number + enforcement date | `QCORecord` (S.O. no, ministry, dates) |
| **SRCF-004 (Product Manuals)** | Standard Code | `PDF_LINK_DISCOVERY` against `SRC-006` | CMD document header + IS code match | `ProductManualRecord` (grouping, labs) |
| **SRCF-005 (SIT Schedules)** | Standard Code | `PDF_LINK_DISCOVERY` against `SRC-007` | SIT table structure + testing levels | `SITRecord` (routine/acceptance levels) |
| **SRCF-007 (Licences)** | CM/L Number / Brand | `REGISTRY_QUERY` against `SRC-010` | Operative licence ledger match | `LicenceRecord` (CM/L, manufacturer) |
| **SRCF-008 (Laboratories)** | Standard Code / Region | `HTML_CATALOG` against `SRC-012` & `SRC-013` | Lab code + active test scope validation | `LaboratoryRecord` (lab code, scope) |
| **SRCF-009 (Hallmarking)** | HUID / Gold Purity / District | `REGISTRY_QUERY` against `SRC-014` & `SRC-015` | 6-digit alphanumeric regex + AHC register | `HallmarkRecord` (HUID, purity, AHC) |

---

## 3. Discovery Integrity Gates

1. **Anti-Collateral Filter**: If a search query returns multiple matching items (e.g. search for "1786" returns standards and administrative circulars), the discovery engine must filter by document type prefix and reject non-normative circulars.
2. **Amendment Association**: Discovery of a base standard automatically triggers discovery of all child amendment slips to ensure full temporal synchronization.
