# Graph Ontology & Relationship Specification (Phase 5A)

**Document Version**: 1.0  
**Phase**: Phase 5 — Knowledge Graph Construction & Structured BIS Relationships  
**Scope**: Node Types, Edge Types, Attributes, and Directional Semantics  

---

## 1. Node Types (Ontology Classes)

| Node Type | Description | Primary Key Example |
|---|---|---|
| `PRODUCT` | Commercial product or commodity category | `PRD-000001`, `PROD-TMT-STEEL` |
| `INDIAN_STANDARD` | Published Indian Standard Specification | `IS-1786-2008`, `IS-374-2019` |
| `AMENDMENT` | Official amendment slip or erratum | `IS-1786-2008-A1` |
| `QCO` | Statutory Quality Control Order / Gazette S.O. | `QCO-DPIIT-SO1245E-2023` |
| `CONFORMITY_SCHEME` | Statutory Conformity Assessment Scheme | `SCHEME-I`, `SCHEME-II`, `SCHEME-IV` |
| `PRODUCT_MANUAL` | BIS Product Manual for factory certification | `PM-IS-1786-2008-V1` |
| `SIT_SCHEDULE` | Scheme of Inspection and Testing Schedule | `SIT-IS-1786-2008-NOV2021` |
| `TESTING_LABORATORY`| Central, Regional, or Recognized Testing Facility | `LAB-CL-SAHIBABAD`, `LAB-RECOG-ERDA-VADODARA` |
| `LICENCE_RECORD` | Operative manufacturer certification licence | `LIC-CM-L-8400178601` |
| `CRS_REGISTRATION` | Compulsory Registration record for Electronics | `CRS-REG-4100160461` |
| `HALLMARKING_CENTRE`| Assaying and Hallmarking Centre (AHC) | `AHC-DIRECTORY-2023` |
| `EVIDENCE_UNIT` | Atomic verbatim clause or tabular evidence | `EV-IS-1786-2008-CL-4.2` |

---

## 2. Edge Types & Directional Semantics

- `Product` $\xrightarrow{\text{COVERED_BY_STANDARD}}$ `IndianStandard`
- `IndianStandard` $\xrightarrow{\text{AMENDED_BY}}$ `Amendment`
- `QCO` $\xrightarrow{\text{MANDATES_CERTIFICATION_FOR}}$ `IndianStandard`
- `IndianStandard` $\xrightarrow{\text{CERTIFIED_UNDER_SCHEME}}$ `ConformityScheme`
- `IndianStandard` $\xrightarrow{\text{HAS_PRODUCT_MANUAL}}$ `ProductManual`
- `IndianStandard` $\xrightarrow{\text{HAS_SIT_SCHEDULE}}$ `SITSchedule`
- `IndianStandard` $\xrightarrow{\text{TESTED_BY_LABORATORY}}$ `TestingLaboratory`
- `LicenceRecord` $\xrightarrow{\text{LICENSED_UNDER_STANDARD}}$ `IndianStandard`
- `CRSRegistration` $\xrightarrow{\text{REGISTERED_UNDER_STANDARD}}$ `IndianStandard`
- `IndianStandard` $\xrightarrow{\text{CONTAINS_EVIDENCE_UNIT}}$ `EvidenceUnit`
