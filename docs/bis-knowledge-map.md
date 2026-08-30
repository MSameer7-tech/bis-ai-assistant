# BIS Knowledge Map & Information Ecosystem

This document establishes the authoritative knowledge taxonomy, entity relationships, and query mappings for the **BIS AI Intelligent Assistant for Indian Standards**.

---

## 1. BIS Information Ecosystem Overview

The Bureau of Indian Standards (BIS), established under the **BIS Act 2016**, operates across multiple technical and regulatory pillars:

```text
                               ┌─────────────────────────────────────────┐
                               │       Bureau of Indian Standards        │
                               │        (Statutory National Body)        │
                               └────────────────────┬────────────────────┘
                                                    │
        ┌──────────────────────┬────────────────────┴────────────────┬──────────────────────┐
        ▼                      ▼                                     ▼                      ▼
┌─────────────────┐   ┌─────────────────┐                   ┌─────────────────┐   ┌─────────────────┐
│ Standards       │   │ Regulatory &    │                   │ Conformity &    │   │ Public &        │
│ Formulation     │   │ Line Ministries │                   │ Testing Network │   │ Consumer Affairs│
├─────────────────┤   ├─────────────────┤                   ├─────────────────┤   ├─────────────────┤
│ • Standards     │   │ • QCOs (DPIIT/  │                   │ • Schemes (ISI/ │   │ • Hallmarking   │
│ • Editions      │   │   MeitY/MoP)    │                   │   CRS/CoC)      │   │ • BIS Care App  │
│ • Amendments    │   │ • Gazette Orders│                   │ • Testing Labs  │   │ • Grievance CAD │
│ • Technical Sec │   │ • Statutory Mand│                   │ • Lab Scopes    │   │ • Standards Club│
└─────────────────┘   └─────────────────┘                   └─────────────────┘   └─────────────────┘
```

---

## 2. Core Knowledge Domains & Entities

### Domain 1: Indian Standards (IS)
* **Description**: Formal technical specifications defining product safety, performance, dimensions, definitions, and sampling guidelines.
* **Issuing Body**: BIS Technical Committees (Division Councils e.g., Electrotechnical `ETD`, Electronics & IT `LITD`, Mechanical `MED`, Civil `CED`, Chemical `CHD`).
* **Authority Tier**: **Tier 1B (Normative)**.
* **Entities**:
  * `IndianStandard`: `standard_number`, `title`, `division_council`, `scope_summary`, `publication_year`, `status` (`Active`/`Withdrawn`/`Under Revision`).
  * `Clause`: `clause_number`, `clause_title`, `parent_clause`, `page_start`, `page_end`, `content_text`, `is_mandatory_normative`.
  * `Table`: `table_number`, `table_title`, `columns`, `rows`, `associated_clause`.
  * `Annex`: `annex_letter`, `annex_title`, `is_normative_or_informative`, `content`.
* **Target User Questions**:
  * *"What is the Indian Standard for self-ballasted LED lamps for general lighting?"*
  * *"What does Clause 6 of the safety standard require regarding markings?"*
  * *"What are the dielectric strength test voltage limits specified in the standard?"*
* **Verification Note**: `[⚠️ Requires Verification from Official BIS Portal upon document acquisition]`

---

### Domain 2: Standards Versions, Amendments & Reaffirmations
* **Description**: Lifecycle tracking of standards including amendment slips, year changes, corrigenda, and 5-year reaffirmation cycles.
* **Issuing Body**: Bureau of Indian Standards (Published via BIS Standards Portal / Gazette).
* **Authority Tier**: **Tier 1B (Normative)**.
* **Entities**:
  * `StandardVersion`: `standard_number`, `version_year`, `edition_number`, `effective_date`, `is_current`.
  * `Amendment`: `amendment_number`, `issue_date`, `clauses_modified`, `text_changes`, `status`.
  * `Reaffirmation`: `reaffirmation_year`, `status` (`Reaffirmed`).
* **Target User Questions**:
  * *"Has the 2012 version of the LED safety standard been amended or reaffirmed?"*
  * *"What specific test limit was changed in Amendment 1?"*
  * *"Is an older edition still acceptable during the transition period?"*
* **Verification Note**: `[⚠️ Requires Verification from Official BIS Standards Gazette]`

---

### Domain 3: Quality Control Orders (QCOs) & Technical Regulations
* **Description**: Statutory orders issued by Central Ministries that make specific Indian Standards legally compulsory for manufacture, import, distribution, or sale in India under the BIS Act.
* **Issuing Body**: Central Ministries (DPIIT, MeitY, Ministry of Power, Ministry of Steel, etc.) published in the Gazette of India.
* **Authority Tier**: **Tier 1A (Statutory Law)**.
* **Entities**:
  * `QualityControlOrder`: `qco_id`, `issuing_ministry`, `gazette_notification_number`, `notification_date`, `effective_date`, `enforcement_status` (`Enforced`/`Extended`/`Draft`), `hs_codes_covered`.
  * `QCOApplicability`: `product_scope`, `notified_standard_id`, `applicable_scheme` (`Scheme I` vs `Scheme II`), `exemptions` (`Export`/`R&D`/`Micro-enterprises`).
* **Target User Questions**:
  * *"Is BIS certification mandatory to sell LED bulbs in India?"*
  * *"Which government ministry issued the QCO for LED lighting?"*
  * *"What is the penalty for selling non-certified products covered under a mandatory QCO?"*
  * *"Are small-scale manufacturers given an extension under the QCO?"*
* **Verification Note**: `[⚠️ Requires Verification from Official Gazette of India notifications]`

---

### Domain 4: BIS Certification Schemes
* **Description**: Conformity assessment frameworks under BIS (Conformity Assessment) Regulations, 2018.
* **Issuing Body**: BIS Conformity Assessment Department.
* **Authority Tier**: **Tier 1A (Regulatory Framework)**.
* **Entities**:
  * `CertificationScheme`: `scheme_code` (`Scheme-I-ISI`, `Scheme-II-CRS`, `Scheme-IV-CoC`, `Hallmarking`), `scheme_name`, `regulatory_basis`.
  * `SchemeRequirement`: `factory_audit_required`, `sample_testing_required`, `surveillance_frequency`, `marking_type` (`ISI Logo` vs `CRS Standard Mark`).
* **Target User Questions**:
  * *"Does an LED bulb fall under the ISI mark scheme or the Compulsory Registration Scheme (CRS)?"*
  * *"What is the key difference between Scheme I (ISI) and Scheme II (CRS)?"*
  * *"Does CRS require a factory inspection before grant of registration?"*
* **Verification Note**: `[⚠️ Requires Verification from BIS Conformity Assessment Regulations 2018]`

---

### Domain 5: Licensing & Registration Procedures
* **Description**: Operational application workflows, digital portal processes, documentary requirements, and statutory fee schedules.
* **Issuing Body**: BIS Central Marks Department / CRS Branch.
* **Authority Tier**: **Tier 2 (Official Procedural Manuals)**.
* **Entities**:
  * `LicensingProcess`: `process_id`, `scheme_code`, `portal_name` (`Manakonline` / `crsbis.in`), `step_order`, `step_description`, `typical_timeline`.
  * `DocumentRequirement`: `document_name`, `issuing_authority`, `is_mandatory`, `applies_to_foreign_mfg`.
  * `FeeSchedule`: `fee_type` (`Application`, `Processing`, `Annual License`, `Marking`), `amount_inr`, `msme_concession_applicable`.
* **Target User Questions**:
  * *"What documents are needed to apply for CRS registration for an LED bulb?"*
  * *"What is the role and requirement of an Authorized Indian Representative (AIR) for foreign manufacturers?"*
  * *"What is the validity period of a CRS registration certificate?"*
* **Verification Note**: `[⚠️ Requires Verification from official Manakonline and CRS portal guidelines]`

---

### Domain 6: Testing Requirements & Test Methods
* **Description**: Explicit physical, electrical, optical, and mechanical tests required to prove conformity to a standard.
* **Issuing Body**: BIS Standards & Product Manuals.
* **Authority Tier**: **Tier 1B / Tier 2**.
* **Entities**:
  * `TestRequirement`: `test_id`, `test_name`, `standard_number`, `clause_ref`, `test_type` (`Type Test`, `Routine Test`, `Acceptance Test`), `sample_size`.
  * `TestProcedure`: `apparatus_required`, `environmental_conditions`, `procedure_steps`, `acceptance_criteria`, `failure_condition`.
* **Target User Questions**:
  * *"What electrical safety tests must an LED bulb pass before certification?"*
  * *"What is the insulation resistance threshold after humidity treatment?"*
  * *"What is the temperature and duration for the glow-wire flame test?"*
* **Verification Note**: `[⚠️ Requires Verification against normative text of relevant standard]`

---

### Domain 7: Laboratories & Laboratory Recognition Scheme (LRS)
* **Description**: BIS in-house and recognized testing facilities authorized to execute tests under specific standards.
* **Issuing Body**: BIS Laboratory Recognition Department / LIMS Portal.
* **Authority Tier**: **Tier 1 / Tier 3 (Directory & Scope)**.
* **Entities**:
  * `Laboratory`: `lab_id`, `lab_name`, `lab_type` (`BIS Central/Regional`, `Govt Recognized`, `Private NABL Accredited`), `city`, `state`, `contact_email`, `status`.
  * `LaboratoryScope`: `lab_id`, `standard_number`, `authorized_clauses` (`Full Scope` or specific clauses), `validity_start`, `validity_end`.
* **Target User Questions**:
  * *"Where can I test my LED lamps in Maharashtra or Gujarat for BIS compliance?"*
  * *"Is Lab X recognized by BIS to conduct photometric testing under IS 16102 Part 2?"*
  * *"Can an unaccredited lab report be submitted for CRS registration?"*
* **Verification Note**: `[⚠️ Requires Verification from active BIS LIMS portal registry snapshot]`

---

### Domain 8: Hallmarking of Precious Metals
* **Description**: Purity certification and tracking of gold and silver jewelry under mandatory hallmarking rules.
* **Issuing Body**: BIS Hallmarking Department.
* **Authority Tier**: **Tier 1A (Statutory & Regulatory)**.
* **Entities**:
  * `HallmarkStandard`: `standard_number` (`IS 1417` for Gold, `IS 2112` for Silver), `purity_grades` (`24K/999`, `22K/916`, `18K/750`, `14K/585`).
  * `HUIDStructure`: `huid_length` (`6 alphanumeric digits`), `mandatory_marks` (`BIS Logo`, `Purity Grade`, `6-digit HUID`).
  * `AssayingCentre`: `ahc_id`, `center_name`, `location`, `recognition_status`.
* **Target User Questions**:
  * *"What are the three mandatory marks visible on certified gold jewelry?"*
  * *"How does a consumer verify the 6-digit HUID code?"*
  * *"Is hallmarking mandatory across all districts in India?"*
* **Verification Note**: `[⚠️ Requires Verification from BIS Hallmarking Department notifications]`

---

### Domain 9: Consumer Affairs & Verification
* **Description**: Consumer empowerment, mark validation mechanisms, and grievance redressal systems.
* **Issuing Body**: BIS Consumer Affairs Department (CAD).
* **Authority Tier**: **Tier 2 (Public Guidance)**.
* **Entities**:
  * `VerificationMechanism`: `mechanism_name` (`BIS Care App`, `Verify License CML`, `Verify R-Number`), `input_identifier`, `output_fields`.
  * `GrievanceProcedure`: `complaint_category` (`Counterfeit ISI`, `Misuse of Hallmark`, `Sub-standard Quality`), `filing_steps`, `investigation_timeline`.
* **Target User Questions**:
  * *"How can I verify if an ISI mark or R-number on an electrical product is genuine?"*
  * *"How do I file a complaint if a product bearing the ISI mark fails prematurely?"*
* **Verification Note**: `[⚠️ Requires Verification from BIS Care Portal documentation]`

---

### Domain 10: Related & Cross-Referenced Standards
* **Description**: Normative standards invoked inside core product standards (e.g., driver safety, component safety, environmental tests).
* **Issuing Body**: BIS Sectional Committees / Harmonized IEC/ISO Committees.
* **Authority Tier**: **Tier 1B (Normatively Binding)**.
* **Entities**:
  * `NormativeReference`: `parent_standard`, `referenced_standard`, `referenced_clause`, `context_of_citation` (e.g., `Driver Safety`, `Ingress Protection`, `EMC`).
* **Target User Questions**:
  * *"Which LED driver standard is cited by the LED lamp safety standard?"*
  * *"What ingress protection (IP) standard applies to luminaires?"*
* **Verification Note**: `[⚠️ Requires Verification from Clause 2 'Normative References' of official standards]`

---

## 3. Relational Mapping Between Entities

```text
Product (e.g., LED Lamp)
  ├── Maps to ──────────> IndianStandard (IS 16102 Pt 1)
  │                         ├── Has Version ────> StandardVersion (2012 / Reaffirmed 2022)
  │                         ├── Has Amendments ─> Amendment (Amd 1, Amd 2)
  │                         ├── Contains ───────> Clause (Clause 6 Marking, Clause 8 Insulation)
  │                         │                       └── Specifies ──> TestRequirement
  │                         │                                           └── Tested at ──> Laboratory (LRS Scope)
  │                         └── Cites ──────────> NormativeReference (IS 15885 Driver Safety)
  │
  ├── Regulated by ─────> QualityControlOrder (MeitY Electronics QCO)
  │                         ├── Mandates ───────> CertificationScheme (Scheme II - CRS)
  │                         │                       └── Governs ────> LicensingProcess & FeeSchedule
  │                         └── Enforces ───────> Mandatory Effective Date & Exemptions
  │
  └── Consumer Checks ──> VerificationMechanism (BIS Care App / R-Number Lookup)
```

---

## 4. Query Intent Taxonomy

| Intent Code | Intent Name | Description | Example Query |
| :--- | :--- | :--- | :--- |
| `standard_lookup` | Standard Lookup | Lookup by standard number or title | *"What does IS 16102 Part 1 cover?"* |
| `standard_recommendation` | Standard Recommendation | Recommend standard from product description | *"I make 9W rechargeable LED bulbs, which standard applies?"* |
| `qco_applicability` | Regulatory Applicability | Determine if certification is legally mandatory | *"Is BIS mandatory for LED bulbs in India?"* |
| `scheme_guidance` | Scheme & Process | Explain certification routes & application steps | *"How do I apply for CRS registration?"* |
| `testing_parameters` | Technical & Testing | Query clauses, tolerances, test methods | *"What is the high-voltage test requirement in Clause 8?"* |
| `laboratory_search` | Laboratory Search | Find recognized testing labs for a standard | *"Where can I test LED lamps in Gujarat?"* |
| `hallmarking_inquiry` | Hallmarking | Gold/Silver purity, HUID, and jeweler compliance | *"How to verify 6-digit HUID?"* |
| `consumer_rights` | Consumer Verification | Mark authentication and filing complaints | *"How to check if an ISI mark is authentic?"* |

---

> [!IMPORTANT]
> **Data Integrity Constraint**: All concrete standard numbers, clause texts, gazette dates, and testing thresholds in this knowledge map serve as architectural schemas. Actual values must only be populated from verified source documents ingested during Phase 2.
