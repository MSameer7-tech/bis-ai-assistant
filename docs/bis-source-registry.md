# BIS Source Registry

This document serves as the master registry tracking all authoritative documents and data assets acquired, verified, and ingested into the **BIS AI Intelligent Assistant**.

---

## 1. Source Metadata Structure

Every source in the knowledge base is tracked using the following standardized fields:

1. **`source_id`**: Canonical unique identifier (e.g., `SRC-001`).
2. **`domain`**: Functional BIS knowledge domain (`Standards`, `Regulation`, `Certification`, `Testing`, `Laboratories`, `Consumer`).
3. **`source_type`**: Document classification (`Standard Document`, `Quality Control Order`, `Conformity Regulation`, `Procedural Guideline`, `Laboratory Directory`, `Portal Circular`).
4. **`issuing_authority`**: Statutory publisher (`Bureau of Indian Standards`, `Ministry of Electronics and Information Technology (MeitY)`, `Ministry of Consumer Affairs`).
5. **`authority_level`**: Legal and normative hierarchy (`Tier 1A - Statutory`, `Tier 1B - Normative`, `Tier 2 - Guidance`, `Tier 3 - Directory`).
6. **`title`**: Full official title of the document.
7. **`standard_or_document_number`**: Official standard or order reference.
8. **`version_edition`**: Edition, revision, or gazette S.O. reference.
9. **`publication_date`**: Official publication date in the Gazette / BIS catalog.
10. **`effective_date`**: Date of regulatory or technical enforcement.
11. **`url`**: Authoritative official URL on government/BIS portal.
12. **`retrieval_date`**: Date when information was fetched/verified.
13. **`status`**: Verification state (`pending_verification`, `verified_authentic`, `processed`, `active`, `superseded`).
14. **`notes`**: Context regarding amendments, transitions, or circulars.

---

## 2. Master Source Registry Table (Pilot: LED Lamps & Bulbs)

| Source ID | Domain | Source Type | Issuing Authority | Authority Level | Title | Standard / Doc No | Version / Edition | Publication Date | Effective Date | Official URL | Retrieval Date | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-001** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 1: Safety Requirements* | `IS 16102 (Part 1) : 2012` | First Edition + Amds 1 & 2 | 2012-08-01 | Active | https://standardsbis.bsbedge.com | 2026-08-30 | `verified_authentic` | Mandatory safety standard notified under MeitY CRO; revised version IS 16102 (Pt 1):2026 published. |
| **SRC-002** | Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Self-Ballasted LED Lamps for General Lighting Services - Part 2: Performance Requirements* | `IS 16102 (Part 2) : 2017` | First Revision | 2017-05-15 | Active | https://standardsbis.bsbedge.com | 2026-08-30 | `verified_authentic` | Specifies luminous flux, efficacy, CCT, CRI, and lumen maintenance testing requirements. |
| **SRC-003** | Regulation | Quality Control Order (QCO) | Ministry of Electronics and IT (MeitY) | Tier 1A - Statutory | *Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order* | S.O. 2905(E) / S.O. 3120(E) | Gazette Order | 2014-11-07 | 2015-05-07 | https://www.meity.gov.in/esdm/standards | 2026-08-30 | `verified_authentic` | Mandates compulsory registration under Scheme-II (CRS) for Self-Ballasted LED Lamps prior to sale/import. |
| **SRC-004** | Certification | Conformity Assessment Regulation | Ministry of Consumer Affairs / BIS | Tier 1A - Statutory | *Bureau of Indian Standards (Conformity Assessment) Regulations, 2018* | Scheme II (CRS) | Gazette Notification | 2018-06-04 | 2018-06-04 | https://www.bis.gov.in | 2026-08-30 | `verified_authentic` | Establishes the legal framework for Compulsory Registration Scheme based on recognized lab test reports. |
| **SRC-005** | Certification | Procedural Guideline | Bureau of Indian Standards (CRS Dept) | Tier 2 - Guidance | *MeitY Series Guidelines for Grouping of Self-Ballasted LED Lamps (Phase 2)* | Circular Series-LED-P2 | Version 3.0 | 2015-04-10 | Active | https://www.crsbis.in | 2026-08-30 | `verified_authentic` | Defines series formation rules for grouping wattage ratings and cap variants under a single test application. |
| **SRC-006** | Standards (Circular) | Implementation Circular | Bureau of Indian Standards (CMD / CRS) | Tier 2 - Guidance | *Guidelines for Implementation of Revised Standard IS 16102 (Part 1) : 2026* | Circular CMD-III/IS16102 | Circular Ref 2026 | 2026-03-15 | 2027-02-02 | https://www.crsbis.in | 2026-08-30 | `verified_authentic` | Official circular extending the mandatory migration deadline for revised IS 16102 (Pt 1):2026 to February 2, 2027. |
| **SRC-007** | Related Standards | Standard Document | Bureau of Indian Standards (ETD 23) | Tier 1B - Normative | *Lamp Controlgear - Part 2-13: Particular Requirements for d.c. or a.c. Supplied Electronic Controlgear for LED Modules* | `IS 15885 (Part 2/Sec 13) : 2012` | Reaffirmed 2022 | 2012-09-01 | Active | https://standardsbis.bsbedge.com | 2026-08-30 | `verified_authentic` | Normative reference for LED drivers/controlgear used within or alongside LED lamps. |
| **SRC-008** | Laboratories | Laboratory Directory & Scopes | Bureau of Indian Standards (LIMS / LRS) | Tier 3 - Directory | *BIS Directory of Recognized Laboratories for Lighting & Electronics (LIMS)* | LIMS-LRS-Snapshot | Live Directory | 2026-08-01 | Active | https://www.lims.bis.gov.in | 2026-08-30 | `pending_verification` | Live list of accredited testing laboratories with authorized testing scope for IS 16102 (Pt 1 & 2). |
| **SRC-009** | Consumer | Portal & Verification Guide | Bureau of Indian Standards (CAD) | Tier 2 - Guidance | *BIS Care App User Guide & Standard Mark Verification Portal* | BIS-CAD-VERIFY | Portal Documentation | 2024-01-01 | Active | https://www.bis.gov.in | 2026-08-30 | `pending_verification` | Consumer verification guidelines for authenticating CRS R-Numbers and ISI CML numbers. |

---

## 3. Identification Status & Verification Notes

### A. Authoritative Sources Verified:
1. **`SRC-001`**: `IS 16102 (Part 1) : 2012` verified on `standardsbis.bsbedge.com` and `crsbis.in`.
2. **`SRC-002`**: `IS 16102 (Part 2) : 2017` verified on `standardsbis.bsbedge.com`.
3. **`SRC-003`**: MeitY Compulsory Registration Order S.O. 2905(E) verified on `meity.gov.in/esdm/standards`.
4. **`SRC-004`**: BIS Conformity Assessment Regulations 2018 verified on `bis.gov.in`.
5. **`SRC-005`**: MeitY Series Guidelines for Phase 2 LED Lamps verified on `crsbis.in`.
6. **`SRC-006`**: BIS CRS Circular extending revised IS 16102 (Pt 1):2026 compliance to February 2, 2027 verified on `crsbis.in`.
7. **`SRC-007`**: `IS 15885 (Part 2/Sec 13) : 2012` verified on `standardsbis.bsbedge.com`.

### B. Sources Requiring Acquisition & Deep Verification (Phase 2):
1. **`SRC-008` (LIMS Lab Directory)**: Detailed lab scope matrix (matching specific accredited testing laboratories to clauses) needs a structured snapshot downloaded from `lims.bis.gov.in`.
2. **`SRC-009` (Consumer Verification Guidelines)**: BIS Care verification workflow documentation needs official PDF/portal snapshot.
