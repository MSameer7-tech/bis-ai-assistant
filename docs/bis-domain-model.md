# BIS Domain Model & Entity Relationship Architecture

This document defines the formal relational structure, entity definitions, and reasoning graphs for the **BIS AI Knowledge Base**. It translates the real-world BIS regulatory ecosystem into deterministic data models and graph relationships.

---

## 1. Core Relationship Maps

### 1.1 Product-Centric Regulatory & Operational Flow

```text
                                  ┌───────────────────────┐
                                  │        PRODUCT        │
                                  │ (e.g., 9W LED Lamp)   │
                                  └───────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
        ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
        │   APPLICABLE STANDARD │ │   GOVERNMENT QCO      │ │  CERTIFICATION SCHEME │
        │   (IS 16102 Part 1)   │ │ (Electronics QCO)     │ │   (Scheme II - CRS)   │
        └───────────┬───────────┘ └───────────┬───────────┘ └───────────┬───────────┘
                    │                         │                         │
                    ▼                         ▼                         ▼
        ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
        │   CLAUSES & SECTIONS  │ │ MANDATORY THRESHOLD?  │ │ LICENSING / REGISTR.  │
        │   (Clause 5, 8, 12)   │ │ (Effective Date & Ex.)│ │ (Documents & Portal)  │
        └───────────┬───────────┘ └───────────────────────┘ └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │      TESTS & METH.    │
        │   (Insulation, Surge) │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ RECOGNIZED LAB NETWORK│
        │ (Lab Name & Scope IS) │
        └───────────────────────┘
```

---

### 1.2 Standard-Centric Lifecycle & Hierarchy

```text
                            ┌──────────────────────────────────┐
                            │         INDIAN STANDARD          │
                            │   (Base Code: IS 16102 Part 1)   │
                            └────────────────┬─────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
          ┌───────────────────────────┐               ┌───────────────────────────┐
          │     STANDARD VERSION      │               │     RELATED STANDARDS     │
          │  (Year: 2012, Rev 1, Act) │               │  (Normative: IS 15885)    │
          └────────────┬──────────────┘               └───────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│   AMENDMENTS     │        │     CLAUSES      │
│ (Amd 1, Amd 2)   │        │ (Hierarchy 1..N) │
└──────────────────┘        └────────┬─────────┘
                                     │
                       ┌─────────────┴─────────────┐
                       ▼                           ▼
          ┌──────────────────────────┐┌──────────────────────────┐
          │   TEST SPECIFICATIONS    ││      TABLES / ANNEX    │
          │  (Limits & Pass Criteria)││ (Dimensions & Constants) │
          └──────────────────────────┘└──────────────────────────┘
```

---

## 2. Entity Definitions & Schema Specifications

### 2.1 `Product`
Represents physical consumer or industrial goods seeking compliance.
* `product_id`: Unique slug (`led-self-ballasted-lamp`)
* `category`: Broad category (`Lighting & Luminaires`)
* `common_names`: Aliases (`LED bulb`, `LED lamp`, `rechargeable bulb`, `B22 LED`)
* `attributes`: Key technical parameters (`wattage_range`, `voltage`, `cap_type`, `application`)

### 2.2 `IndianStandard` & `StandardVersion`
Represents the technical specification issued by BIS.
* `standard_number`: Canonical standard identifier (`IS 16102 (Part 1)`)
* `title`: Full official title
* `technical_committee`: Issuing sectional committee (`ETD 23 - Electric Lamps and Luminaires`)
* `version_year`: Year of edition (`2012`)
* `status`: Lifecycle state (`Active`, `Amended`, `Withdrawn`, `Under Revision`)
* `reaffirmation_year`: Latest reaffirmation (`2022`)

### 2.3 `Clause`
The fundamental atomic unit of normative requirements and semantic chunks.
* `clause_id`: Identifier (`IS16102_P1_2012_CLAUSE_8.2`)
* `standard_number`: Parent standard
* `clause_number`: Dot-notated section (`8.2`)
* `clause_title`: Section title (`Insulation Resistance and Electric Strength`)
* `page_start`: Physical PDF start page
* `page_end`: Physical PDF end page
* `parent_clause`: Hierarchical parent (`8`)
* `content_text`: Cleaned text of the clause
* `is_test_specification`: Boolean flag indicating if this clause dictates a physical laboratory test

### 2.4 `QualityControlOrder` (QCO)
Represents statutory government notifications enforcing mandatory certification.
* `qco_id`: Gazette reference (`MeitY-QCO-CRO-2014-LED`)
* `ministry`: Issuing ministry (`Ministry of Electronics and Information Technology - MeitY`)
* `gazette_notification_number`: Official S.O. number
* `order_title`: Title of the order
* `notified_standards`: List of referenced Indian Standards made compulsory
* `effective_date`: Date from which compliance became legally mandatory
* `enforcement_status`: (`Enforced`, `Extended`, `Draft Notification`)
* `exemptions`: Explicit exclusions (e.g., `Export goods`, `Prototypes < 50 units`)

### 2.5 `CertificationScheme` & `LicensingRequirement`
Conformity assessment routes and operational application criteria.
* `scheme_code`: (`Scheme-I-ISI`, `Scheme-II-CRS`, `Scheme-IV-CoC`, `Hallmarking`)
* `scheme_name`: Full descriptive scheme name
* `governing_regulation`: BIS Conformity Assessment Regulations 2018 clause
* `factory_inspection_required`: Boolean (`True` for ISI, `False` for CRS)
* `lab_testing_required`: Boolean (`True`)
* `portal_url`: Official application portal (`https://www.crsbis.in` / `https://manakonline.in`)
* `mandatory_documents`: Checklist (e.g., `Test Report`, `Trademark Reg`, `AIR Undertaking`)

### 2.6 `TestRequirement` & `Laboratory`
Laboratory testing criteria and recognized testing infrastructure.
* `test_id`: Identifier (`TEST-IS16102-INSULATION`)
* `test_name`: Name of test (`Electric Strength Test at 4000V`)
* `standard_number`: `IS 16102 (Part 1)`
* `clause_reference`: `Clause 8.3`
* `acceptance_criteria`: Quantitative or qualitative pass criteria
* `laboratory_id`: Identifier of recognized lab
* `lab_name`: Registered name of test lab
* `location`: City, State, Pin
* `nabl_accreditation_no`: NABL certificate reference
* `authorized_standards`: Explicit list of standards within the lab's active BIS LRS scope

---

## 3. Knowledge Graph Ingestion & Retrieval Strategy

```text
                       HYBRID RETRIEVAL & REASONING FLOW
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[DETERMINISTIC GRAPH TRAVERSAL]                            [SEMANTIC CHUNK SEARCH]
(Exact Lookups & Legal Mandates)                           (Natural Language Questions)
  • Product -> QCO -> Compulsory status                     • "What happens if lamp operates
  • Standard -> Clause -> Page number                         at 110% rated voltage?"
  • Standard -> Clause -> Lab Scope Match                   • Matches Clause 12 embeddings
     │                                                                 │
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
                      [GROUNDED REASONING & SYNTHESIS]
                                      │
                                      ▼
                        [VERIFIED CITATION RESPONSE]
```

This multi-relational architecture ensures that whenever an answer is formulated, every factual claim is grounded in structured, queryable entities with exact document, clause, and page provenance.
