# BIS Source Registry

This document serves as the master registry tracking all authoritative documents, statutory orders, and data assets acquired, verified, and ingested into the **BIS AI Intelligent Assistant**.

---

## 1. Granular Verification Status Lifecycle

To avoid premature claims of authenticity before full document inspection, every source transitions through this granular verification lifecycle:

```text
[discovered]
     ↓
[official_domain_verified]  ──> Official government/BIS URL domain confirmed
     ↓
[document_identified]       ──> Specific standard, QCO, or regulation title & number identified
     ↓
[document_acquired]         ──> Official PDF or data file downloaded into data/raw/
     ↓
[content_verified]          ──> Text, clauses, tables, and page boundaries extracted & checked
     ↓
[metadata_verified]         ──> Publication date, edition, amendments, and issuing authority checked
     ↓
[current_status_verified]   ──> Legal applicability, transition circulars, and active status confirmed
     ↓
(Optional: [superseded] / [withdrawn])
```

---

## 2. Dynamic Laboratory Information Model

Laboratory information is temporal and dynamic. The system tracks:
* `laboratory_id`: Identifier
* `lab_name`: Registered name
* `accreditation_number`: NABL / BIS certificate reference
* `current_status`: Active recognition status (`recognized`, `suspended`, `expired`)
* `scope`: Explicit list of standards and clauses the lab is authorized to test
* `validity_start`: Recognition commencement date
* `validity_end`: Recognition expiry date
* `source_retrieval_timestamp`: Exact ISO timestamp when scope was queried/retrieved

---

## 3. Master Source Registry Table (Pilot: LED Lamps & Bulbs)

| Source ID | Domain | Source Type | Issuing Authority | Authority Level | Title | Standard / Doc No | Version / Edition | Publication Date | Effective Date | Official URL | Retrieval Date | Granular Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-001** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 1: Safety Requirements* | `IS 16102 (Part 1) : 2012` | First Edition + Amds 1 & 2 | 2012-08-01 | Provisional | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Mandatory safety standard under MeitY CRO; revised 2026 edition published; pending raw PDF acquisition. |
| **SRC-002** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 2: Performance Requirements* | `IS 16102 (Part 2) : 2017` | First Revision | 2017-05-15 | Provisional | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Performance benchmark standard; pending raw PDF acquisition. |
| **SRC-003** | Regulation | Quality Control Order (QCO) | Ministry of Electronics and IT (MeitY) | Tier 1A - Statutory | *Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order* | S.O. 2905(E) / S.O. 3120(E) | Gazette Order | 2014-11-07 | Provisional | https://www.meity.gov.in/esdm/standards | 2026-08-30 | `document_identified` | Mandates CRS registration for Self-Ballasted LED Lamps; pending gazette notification text acquisition. |
| **SRC-004** | Certification | Conformity Assessment Regulation | Ministry of Consumer Affairs / BIS | Tier 1A - Statutory | *Bureau of Indian Standards (Conformity Assessment) Regulations, 2018* | Scheme II (CRS) | Gazette Notification | 2018-06-04 | 2018-06-04 | https://www.bis.gov.in | 2026-08-30 | `document_identified` | Establishes statutory framework for Scheme-II (CRS); pending regulation text acquisition. |
| **SRC-005** | Certification | Procedural Guideline | Bureau of Indian Standards (CRS Dept) | Tier 2 - Guidance | *MeitY Series Guidelines for Grouping of Self-Ballasted LED Lamps (Phase 2)* | Circular Series-LED-P2 | Version 3.0 | 2015-04-10 | Provisional | https://www.crsbis.in | 2026-08-30 | `document_identified` | Series formation guidelines for model grouping; pending circular download. |
| **SRC-006** | Standards (Circular) | Implementation Circular | Bureau of Indian Standards (CMD / CRS) | Tier 2 - Guidance | *Guidelines for Implementation of Revised Standard IS 16102 (Part 1) : 2026* | Circular CMD-III/IS16102 | Circular Ref 2026 | 2026-03-15 | Provisional | https://www.crsbis.in | 2026-08-30 | `document_identified` | Transition guidelines for revised IS 16102 (Pt 1):2026; pending circular PDF verification. |
| **SRC-007** | Related Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Lamp Controlgear - Part 2-13: Particular Requirements for d.c. or a.c. Supplied Electronic Controlgear for LED Modules* | `IS 15885 (Part 2/Sec 13) : 2012` | Reaffirmed 2022 | 2012-09-01 | Provisional | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Normative driver safety standard; pending raw PDF acquisition. |
| **SRC-008** | Laboratories | Laboratory Directory & Scopes | Bureau of Indian Standards (LIMS / LRS) | Tier 3 - Directory | *BIS Directory of Recognized Laboratories for Lighting & Electronics (LIMS)* | LIMS-LRS-Directory | Dynamic Query | 2026-08-01 | Dynamic | https://www.lims.bis.gov.in | 2026-08-30 | `official_domain_verified` | Live recognized laboratory directory; scope and validity timestamps to be queried during ingestion. |
| **SRC-009** | Consumer | Portal & Verification Guide | Bureau of Indian Standards (CAD) | Tier 2 - Guidance | *BIS Care App User Guide & Standard Mark Verification Portal* | BIS-CAD-VERIFY | Portal Guide | 2024-01-01 | Provisional | https://www.bis.gov.in | 2026-08-30 | `official_domain_verified` | Verification workflow documentation for R-Numbers and ISI marks. |
