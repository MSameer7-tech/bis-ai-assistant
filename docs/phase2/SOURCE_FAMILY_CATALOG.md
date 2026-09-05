# Authorized BIS and Statutory Knowledge Source Families

**Document Version**: 1.1  
**Phase**: Phase 2A — BIS & Statutory Source Family Discovery  
**Authoritative Scope**: Official Knowledge Entry Points of the Bureau of Indian Standards (BIS) & Central Ministries  

---

## 1. Executive Summary

The **Authorized BIS and Statutory Knowledge Source Families Catalog** provides the authoritative architectural map of all official information families required by the BIS AI Technical Assistant.

To maintain strict regulatory truthfulness, the assistant recognizes that not all official knowledge is published directly by BIS. Statutory instruments such as Quality Control Orders (QCOs) are enacted by Central Ministries and published in *The Gazette of India*, while Acts and Rules originate from Parliament.

```
                         AUTHORIZED KNOWLEDGE SOURCE ARCHITECTURE
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
 [BIS_PUBLISHED]                     [BIS_OPERATED]                   [STATUTORY_EXTERNAL]
 • SRCF-001: Indian Standards        • SRCF-007: Licences & Registers • SRCF-003: Gazette QCOs
 • SRCF-002: Amendments & Revisions  • SRCF-008: Testing Labs        • SRCF-012: Acts & Regulations
 • SRCF-004: Product Manuals         • SRCF-009: Hallmarking System
 • SRCF-005: Inspection (SIT)        • SRCF-010: Consumer Portals
 • SRCF-006: Conformity Schemes
 • SRCF-011: FAQs & Guides
```

---

## 2. Source Family Classification Matrix

| Source Family ID | Family Name | Source Ownership | Issuing Authority | Default Authority Class | Mapped PS Requirements |
|---|---|---|---|---|---|
| **SRCF-001** | Indian Standards Specifications | `BIS_PUBLISHED` | Bureau of Indian Standards | `PRIMARY_NORMATIVE` | RQ-001, RQ-002, RQ-009, RQ-010 |
| **SRCF-002** | Standards Amendments & Revisions | `BIS_PUBLISHED` | Bureau of Indian Standards | `PRIMARY_NORMATIVE` | RQ-001, RQ-009, RQ-010 |
| **SRCF-003** | Quality Control Orders (QCO) | `STATUTORY_EXTERNAL` | Central Ministries / Gazette | `PRIMARY_NORMATIVE` | RQ-001, RQ-003, RQ-009, RQ-010 |
| **SRCF-004** | BIS Product Manuals | `BIS_PUBLISHED` | BIS CMD | `OFFICIAL_OPERATIONAL` | RQ-003, RQ-004, RQ-009, RQ-010 |
| **SRCF-005** | Scheme of Inspection & Testing (SIT) | `BIS_PUBLISHED` | BIS CMD | `OFFICIAL_OPERATIONAL` | RQ-001, RQ-004, RQ-009, RQ-010 |
| **SRCF-006** | Conformity Assessment Schemes | `BIS_PUBLISHED` | BIS Headquarters | `PRIMARY_NORMATIVE` | RQ-003, RQ-004, RQ-009, RQ-010 |
| **SRCF-007** | BIS Licences & Registrations | `BIS_OPERATED` | BIS / CRS Databases | `OFFICIAL_OPERATIONAL` | RQ-004, RQ-005, RQ-009, RQ-010 |
| **SRCF-008** | BIS Testing Laboratories Registers | `BIS_OPERATED` | BIS LPCD | `OFFICIAL_OPERATIONAL` | RQ-007, RQ-009, RQ-010 |
| **SRCF-009** | Hallmarking & Precious Metals | `BIS_OPERATED` | BIS Hallmarking Dept | `PRIMARY_NORMATIVE` | RQ-005, RQ-006, RQ-009, RQ-010 |
| **SRCF-010** | Consumer Services & BIS Care | `BIS_OPERATED` | BIS Consumer Affairs | `OFFICIAL_OPERATIONAL` | RQ-005, RQ-009, RQ-010 |
| **SRCF-011** | FAQs, Guides & Booklets | `BIS_PUBLISHED` | BIS Headquarters | `OFFICIAL_INFORMATIVE` | RQ-001, RQ-003, RQ-004, RQ-008 |
| **SRCF-012** | BIS Acts, Rules & Regulations | `STATUTORY_EXTERNAL` | Parliament / Ministry | `STATUTORY_FRAMEWORK` | RQ-001, RQ-003, RQ-005, RQ-006 |

---

## 3. Detailed Source Family Profiles & Evidence Hierarchies

### SRCF-001: Indian Standards Specifications
- **Ownership**: `BIS_PUBLISHED` (BIS Standard Formulation Committees)
- **Default Authority**: `PRIMARY_NORMATIVE`
- **Claim Roles**: Technical parameters, dimensional tolerances, test methods, physical/chemical specifications.
- **Official Entry Points**:
  - `https://www.bis.gov.in/know-your-standard/`
  - `https://standardsbis.bsbedge.com/`

### SRCF-002: Standards Amendments & Revisions
- **Ownership**: `BIS_PUBLISHED` (BIS Technical Committees)
- **Default Authority**: `PRIMARY_NORMATIVE`
- **Claim Roles**: Errata slips, clause amendments, validity extensions, active supersession status.
- **Official Entry Points**:
  - `https://www.bis.gov.in/know-your-standard/`
  - `https://www.manakonline.in/`

### SRCF-003: Quality Control Orders (QCO) & Gazette Notifications
- **Ownership**: `STATUTORY_EXTERNAL` (Ministry of Commerce & Industry / DPIIT, MeitY, MoEFCC, MoS, etc.)
- **Default Authority**: `PRIMARY_NORMATIVE`
- **Evidence Hierarchy for Legal Claims**:
  ```
  1. Actual Gazette Notification (S.O. instrument published in The Gazette of India)
          ↓
  2. Applicable Ministry Statutory Order
          ↓
  3. Official BIS Compulsory Certification Information Portal
  ```
- **Official Entry Points**:
  - `https://www.egazette.gov.in/`
  - `https://www.bis.gov.in/product-certification/products-under-compulsory-certification/`

### SRCF-004: BIS Product Manuals
- **Ownership**: `BIS_PUBLISHED` (Certification Management Department - CMD)
- **Default Authority**: `OFFICIAL_OPERATIONAL`
- **Claim Roles**: Grouping guidelines, in-house laboratory equipment checklists, sample selection sizes.
- **Official Entry Points**:
  - `https://www.bis.gov.in/product-certification/product-manuals/`
  - `https://www.manakonline.in/`

### SRCF-005: Scheme of Inspection and Testing (SIT)
- **Ownership**: `BIS_PUBLISHED` (BIS CMD)
- **Default Authority**: `OFFICIAL_OPERATIONAL` (with document-specific normative testing rules)
- **Claim Roles**: Routine test frequencies, acceptance test levels, raw material verification, lot control rules.
- **Official Entry Points**:
  - `https://www.bis.gov.in/product-certification/scheme-of-inspection-and-testing/`
  - `https://www.manakonline.in/`

### SRCF-006: Conformity Assessment Schemes
- **Ownership**: `BIS_PUBLISHED` (BIS Headquarters)
- **Default Authority**: `PRIMARY_NORMATIVE`
- **Dynamic Model**: Evaluates scheme identifiers dynamically (`scheme_identifier`, `scheme_name`, `applicability`, `version_status`) across Scheme-I, Scheme-II, Scheme-IV, FMCS, and newly promulgated schemes.
- **Official Entry Points**:
  - `https://www.bis.gov.in/product-certification/product-certification-overview/`
  - `https://www.crsbis.in/BIS/`

### SRCF-007: BIS Licences & Registration Registers
- **Ownership**: `BIS_OPERATED` (Central Licence & CRS Registries)
- **Default Authority**: `OFFICIAL_OPERATIONAL`
- **Claim Roles**: Operative manufacturer licence verification (CM/L numbers), CRS electronic registration numbers (R-numbers), factory addresses, registered brands.
- **Official Entry Points**:
  - `https://www.bis.gov.in/product-certification/search-licence-details/`
  - `https://www.crsbis.in/BIS/app-status.do`

### SRCF-008: BIS Testing Laboratories Registers
- **Ownership**: `BIS_OPERATED` (Central Laboratory & LPCD)
- **Default Authority**: `OFFICIAL_OPERATIONAL`
- **Laboratory Status Categorization**:
  - `BIS_OWNED`: Laboratories directly owned and operated by BIS (Central Laboratory Sahibabad, Regional Labs).
  - `BIS_RECOGNIZED`: Independent commercial/institutional laboratories recognized under the BIS Laboratory Recognition Scheme (LRS).
  - `BIS_EMPANELLED`: Laboratories empanelled for specific testing overflow or specialized tests.
  - `NABL_ACCREDITED`: Partner facilities with valid NABL accreditation scopes.
  - `OTHER_RECOGNIZED`: Government-notified testing institutes.
- **Official Entry Points**:
  - `https://www.bis.gov.in/laboratories/bis-laboratories/`
  - `https://www.bis.gov.in/laboratories/recognized-laboratories/`

### SRCF-009: Hallmarking & Precious Metals Architecture
- **Ownership**: `BIS_OPERATED` (BIS Hallmarking Department)
- **Default Authority**: `PRIMARY_NORMATIVE`
- **Internal Subfamilies**:
  - `SRCF-009A`: **Hallmarking Standards** (IS 1417 gold, IS 2112 silver specifications)
  - `SRCF-009B`: **Hallmarking Regulations** (*BIS Hallmarking Regulations 2018*)
  - `SRCF-009C`: **Mandatory Hallmarking Orders** (District-wise gazetted phase orders & amendments)
  - `SRCF-009D`: **HUID / Consumer Verification** (6-digit alphanumeric unique identifier rules)
  - `SRCF-009E`: **Assaying & Hallmarking Centres (AHC)** (Accredited centre directory & testing scopes)
  - `SRCF-009F`: **Jeweller & Refinery Registrations** (Registered jewellers & certified refineries)
- **Official Entry Points**:
  - `https://www.bis.gov.in/hallmarking-overview/`
  - `https://www.manakonline.in/MANAK/hallmarking`

### SRCF-010: Consumer Services & BIS Care
- **Ownership**: `BIS_OPERATED` (BIS Consumer Affairs)
- **Default Authority**: `OFFICIAL_OPERATIONAL`
- **Claim Roles**: Standard mark verification guides, BIS Care mobile workflows, complaint redressal.
- **Official Entry Points**:
  - `https://www.bis.gov.in/consumer-overview/`

### SRCF-011: Informative FAQs, Guides & Booklets
- **Ownership**: `BIS_PUBLISHED` (BIS Headquarters)
- **Default Authority**: `OFFICIAL_INFORMATIVE`
- **Claim Roles**: Simplified procedural FAQs, MSME guidance, fee concession guides.
- **Official Entry Points**:
  - `https://www.bis.gov.in/faq/`
  - `https://www.bis.gov.in/publications/`

### SRCF-012: BIS Acts, Rules & Statutory Regulations
- **Ownership**: `STATUTORY_EXTERNAL` (Parliament of India / Ministry of Consumer Affairs)
- **Default Authority**: `STATUTORY_FRAMEWORK`
- **Temporal Versioning Contract**: Must preserve `effective_from`, `effective_to`, `amendment_of`, `consolidated_version`, and `status` to prevent quoting superseded statutory regulations.
- **Official Entry Points**:
  - `https://www.bis.gov.in/the-bis-act-rules-regulations/`
  - `https://www.egazette.gov.in/`

---

## 4. Domain Whitelist & Domain Namespace Rules

1. **Strict Authority Boundary**: The trusted corpus is strictly restricted to approved government and BIS domains (`bis.gov.in`, `egazette.gov.in`, `manakonline.in`, `crsbis.in`, `standardsbis.bsbedge.com`).
2. **App Store Classification**: External distribution channels (e.g. Google Play Store listing for BIS Care) are classified as `APP_DISTRIBUTION_METADATA` / `NON_NORMATIVE` and excluded from primary evidence grounding.
3. **Phase 2A vs Phase 2B Verification Scope**: Phase 2A verifies structural catalog integrity and schema adherence. Live HTTP endpoint validation, search parameter contracts, and discovery protocols are executed in Phase 2B.
