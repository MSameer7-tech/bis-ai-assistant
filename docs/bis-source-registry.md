# BIS Source Registry

This document serves as the master registry tracking all authoritative documents, statutory orders, and data assets acquired, verified, and ingested into the **BIS AI Intelligent Assistant**.

---

## 1. Granular Verification Status Lifecycle

To prevent premature claims of authenticity before full document inspection, every source transitions through this granular verification lifecycle:

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
(Optional: [superseded] / [needs_verification] / [withdrawn])
```

---

## 2. Dynamic Laboratory & Temporal Regulatory Modeling

* **Temporal Regulatory Lineage**:
  $$\text{2012 CRO (Historical)} \longrightarrow \text{2021 CRO (Pending Verification)} \longrightarrow \text{2026 CRO Amendment (Pending Verification)}$$
* **Standards Revision Lifecycle**:
  $$\text{IS 16102 (Part 1) : 2012 (Operational)} \longleftrightarrow \text{IS 16102 (Part 1) : 2026 (First Revision)}$$
* **Dynamic Laboratory Information**:
  `laboratory_id`, `lab_name`, `accreditation_number`, `current_status`, `authorized_clauses`, `validity_start`, `validity_end`, `source_retrieval_timestamp`.

---

## 3. Master Source Registry Table (Pilot: LED Lamps & Bulbs)

| Source ID | Domain | Source Type | Issuing Authority | Authority Level | Title | Standard / Doc No | Version / Edition | Publication Date | Effective Date | Official URL | Retrieval Date | Granular Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-001** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 1: Safety Requirements* | `IS 16102 (Part 1) : 2012` | First Edition | 2012-08-01 | `null` | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Safety standard under active lab scopes on BIS LIMS; pending raw PDF acquisition. |
| **SRC-002** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 2: Performance Requirements* | `IS 16102 (Part 2) : 2017` | First Revision | 2017-05-15 | `null` | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Performance benchmark standard; verified in active BIS LIMS lab scopes. |
| **SRC-003** | Regulation | Quality Control Order (QCO) | Ministry of Electronics and IT (MeitY) | Tier 1A - Statutory | *Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2012* | S.O. 2357(E) / S.O. 2905(E) | 2012 Order | 2012-10-03 | `null` | https://www.meity.gov.in/esdm/standards | 2026-08-30 | `superseded` | Historical 2012 CRO that originally notified LED lamps; superseded by the 2021 CRO framework. |
| **SRC-004** | Certification | Conformity Assessment Regulation | Ministry of Consumer Affairs / BIS | Tier 1A - Statutory | *The Bureau of Indian Standards (Conformity Assessment) Regulations, 2018* | BIS Conformity Assessment Regulations 2018 | Principal Regs (2024 & 2026 Amds) | 2018-06-04 | `null` | https://www.bis.gov.in | 2026-08-30 | `document_identified` | Statutory framework governing conformity assessment schemes (Scheme I, Scheme II CRS, etc.). |
| **SRC-005** | Certification | Procedural Guideline | Bureau of Indian Standards (CRS Dept) | Tier 2 - Guidance | *Series Guidelines for Grouping of Self-Ballasted LED Lamps* | Circular Series-LED-P2 | Provisional Reference | `null` | `null` | https://www.crsbis.in | 2026-08-30 | `needs_verification` | 🔴 Unverified exact circular reference; do not ingest until official BIS circular PDF is retrieved. |
| **SRC-006** | Standards (Circular) | Implementation Circular | Bureau of Indian Standards (CMD / CRS) | Tier 2 - Guidance | *Guidelines for Implementation of Revised Standard IS 16102 (Part 1) : 2026* | Circular CMD-III/IS16102 | Provisional Reference | `null` | `null` | https://www.crsbis.in | 2026-08-30 | `needs_verification` | 🔴 Transition circular & deadline claim require official circular PDF verification before trusting. |
| **SRC-007** | Related Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Lamp Controlgear - Part 2-13: Particular Requirements for d.c. or a.c. Supplied Electronic Controlgear for LED Modules* | `IS 15885 (Part 2/Sec 13) : 2012` | Reaffirmed 2022 | 2012-09-01 | `null` | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Normative driver safety standard verified in active BIS LIMS lab scopes. |
| **SRC-008** | Laboratories | Laboratory Directory & Scopes | Bureau of Indian Standards (LIMS / LRS) | Tier 3 - Directory | *BIS Directory of Recognized Laboratories for Lighting & Electronics (LIMS)* | LIMS-LRS-Directory | Dynamic Query Snapshot | `null` | `null` | https://www.lims.bis.gov.in | 2026-08-30 | `official_domain_verified` | Dynamic BIS LIMS registry exposing recognized lab names, clauses, testing charges, and validity dates. |
| **SRC-009** | Consumer | Portal & Verification Guide | Bureau of Indian Standards (CAD) | Tier 2 - Guidance | *BIS Care App & Standard Mark Verification Portal* | BIS-CAD-APPS | Portal Documentation | `null` | `null` | https://www.bis.gov.in/bis-apps/?lang=en | 2026-08-30 | `official_domain_verified` | Specific official BIS Care portal for authenticating CRS R-Numbers, ISI CML numbers, and HUID. |
| **SRC-010** | Regulation | Quality Control Order (QCO) | Ministry of Electronics and Information Technology (MeitY) | Tier 1A - Statutory | *Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2021* | CRO 2021 | 2021 Principal Order | 2021-03-18 | `null` | https://www.meity.gov.in/esdm/standards | 2026-08-30 | `document_identified` | 2021 CRO identified on the official BIS Scheme-II portal; document acquisition and content verification pending. |
| **SRC-011** | Regulation | Quality Control Order (QCO) | Ministry of Electronics and Information Technology (MeitY) | Tier 1A - Statutory | *Electronics and Information Technology Goods (Requirement of Compulsory Registration) Amendment Order, 2026* | CRO Amendment 2026 | 2026 Amendment | `null` | `null` | https://www.meity.gov.in/esdm/standards | 2026-08-30 | `document_identified` | 2026 amendment reference identified on the official BIS Scheme-II portal; exact notification document and applicability pending acquisition and verification. |
| **SRC-012** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 1: Safety Requirements (First Revision)* | `IS 16102 (Part 1) : 2026` | First Revision (2026) | `null` | `null` | https://standardsbis.bsbedge.com | 2026-08-30 | `document_identified` | Newly published 2026 revised standard identified in BIS LIMS with active lab scopes; separate version from 2012 edition. |
