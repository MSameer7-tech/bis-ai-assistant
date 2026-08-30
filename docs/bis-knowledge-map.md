# BIS Knowledge Map & Information Ecosystem

This document establishes the official knowledge taxonomy, core first-class entities, relational mappings, and query intent classifications for the **BIS AI Intelligent Assistant for Indian Standards**.

---

## 1. Core Architectural Separation: Standards vs. Regulation vs. Certification

A fundamental design principle of this architecture is the strict separation between:

1. **Standard Applicability**: Does an Indian Standard (IS) exist that specifies the technical characteristics, safety parameters, or performance tests for a given product?
2. **Regulatory Applicability**: Is there an active statutory instrument (such as a Quality Control Order issued by a line ministry) that legally governs the product?
3. **Conformity Mandate**: What is the legal status of certification?
   * **`Mandatory`**: Legally required under a gazetted QCO prior to manufacturing, importing, selling, or distributing.
   * **`Voluntary`**: Standard exists, but certification is optional unless specified by commercial contracts, public procurement, or tenders.
   * **`Conditional`**: Required only for specific sub-categories, voltage ratings, end-use applications, or capacity thresholds (e.g., above certain wattages, or with specific exclusions for R&D/export).

```text
                                  PRODUCT
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
        [STANDARD APPLICABILITY]              [REGULATORY APPLICABILITY]
     "Does an Indian Standard exist?"       "Is there an active Gazette QCO?"
                 │                                       │
                 ▼                                       ▼
       Technical Specification                 Statutory Compliance Status
       (Clauses, Tests, Limits)               ┌──────────┼──────────┐
                                              ▼          ▼          ▼
                                          Mandatory  Voluntary Conditional
                                              │
                                              ▼
                                    [CONFORMITY ASSESSMENT]
                                    Applicable Scheme & Route
                                    (e.g., Scheme I vs Scheme II)
```

---

## 2. First-Class Knowledge Entities

The knowledge base is built around normalized first-class entities:

### 2.1 `Product` (User & Catalog Domain)
Represents physical goods described by a user or manufacturer.
* `product_id`: Canonical unique identifier.
* `product_name`: Standardized nomenclature (e.g., "Self-Ballasted LED Lamp").
* `category`: Product category (e.g., "Lighting and Luminaires").
* `manufacturer_description`: Raw or extracted product description.
* `technical_attributes`: Key-value pairs representing parameters (e.g., `wattage`, `voltage_range`, `cap_type`, `driver_type`).
* `intended_use`: Operational context (e.g., "General Domestic Lighting", "Industrial Hazard Area").
* `variants`: Commercial variations covered under common series guidelines.
* `classification`: Sub-tier classifications (e.g., "Mains-powered electronic apparatus").

### 2.2 `Source` (Provenance & Authority Domain)
Represents every official document, gazette notification, or portal registry asset.
* `source_id`: Canonical source identifier (e.g., `SRC-001`).
* `domain`: Knowledge domain (Standards, Regulation, Schemes, Testing, Laboratories, Consumer).
* `source_type`: Document classification (`standard_document`, `qco_order`, `scheme_regulation`, `product_manual`, `guideline`, `lab_directory`).
* `issuing_authority`: Official publisher (e.g., `Bureau of Indian Standards`, `MeitY`, `DPIIT`, `MoP`).
* `authority_level`: Hierarchy level (`Tier 1A - Statutory`, `Tier 1B - Normative`, `Tier 2 - Guidance`, `Tier 3 - Directory`).
* `title`: Full official title.
* `standard_or_document_number`: Official standard/order code (e.g., `IS 16102 (Part 1) : 2012`).
* `version_edition`: Revision or edition identifier.
* `publication_date`: Date of gazette notification or publication.
* `effective_date`: Date when regulatory or technical enforcement begins.
* `url`: Authoritative official URL on government/BIS portal.
* `retrieval_date`: Timestamp of acquisition.
* `status`: Verification state (`pending_verification`, `verified_authentic`, `processed`, `active`, `superseded`).
* `notes`: Provenance notes, supersession details, and migration circulars.

### 2.3 `Claim` (Evidence & Trust Domain)
The atomic unit of factual reasoning and answer generation, enabling granular citation verification.
* `claim_id`: Unique identifier for an atomic assertion.
* `claim_text`: The factual proposition generated or verified (e.g., "Self-ballasted LED lamps require mandatory CRS registration under MeitY QCO").
* `claim_type`: Classification (`standard_recommendation`, `regulatory_mandate`, `testing_requirement`, `fee_schedule`, `laboratory_scope`).
* `evidence_ids`: References to the specific knowledge chunk(s) supporting the claim.
* `confidence_status`: (`direct_evidence`, `reasoned_inference`, `unsupported_abstain`).
* `citation_mapping`: Exact link to `source_id`, `document_number`, `clause_number`, and `page_number`.

### 2.4 `IndianStandard` & `Clause` (Technical Specification Domain)
* `IndianStandard`: `standard_number`, `title`, `division_council`, `scope_summary`, `publication_year`, `status`.
* `Clause`: `clause_id`, `standard_number`, `clause_number`, `clause_title`, `parent_clause`, `page_start`, `page_end`, `content_text`, `is_normative_requirement`.
* `Table`: `table_number`, `table_title`, `associated_clause`, `table_data`.
* `Annex`: `annex_letter`, `annex_title`, `is_normative`, `content_text`.

### 2.5 `QualityControlOrder` (Regulatory Mandate Domain)
* `qco_id`: Unique statutory identifier.
* `issuing_ministry`: Line ministry.
* `gazette_notification_number`: Official S.O. reference.
* `notification_date`: Issue date.
* `effective_date`: Enforcement deadline.
* `notified_standards`: List of referenced Indian Standards made compulsory.
* `applicability_criteria`: Criteria determining which products/ratings fall under scope.
* `exemptions`: Conditions under which compliance is exempt.

### 2.6 `CertificationScheme` & `LicensingRequirement` (Conformity Domain)
* `scheme_code`: Identifier (e.g., `Scheme-I-ISI`, `Scheme-II-CRS`).
* `scheme_name`: Full legal scheme name.
* `factory_audit_required`: Boolean.
* `lab_testing_required`: Boolean.
* `portal_url`: Official application portal.
* `process_steps`: Step-by-step workflow.

### 2.7 `TestRequirement` & `Laboratory` (Testing Domain)
* `test_id`: Test identifier.
* `test_name`: Name of test (e.g., "Insulation Resistance Test").
* `standard_number`: Referenced standard.
* `clause_ref`: Clause defining test method and parameters.
* `acceptance_criteria`: Quantitative or qualitative threshold.
* `laboratory_id`: Recognized lab identifier.
* `lab_name`: Facility name.
* `city`, `state`: Geographic location.
* `authorized_standards`: Specific standards and clauses in lab's active LRS scope.

---

## 3. Evidence-Backed Citation Lineage

To prevent hallucination, every user-facing answer traverses this immutable lineage:

```text
User Question
      ↓
Answer Synthesis
      ↓
Atomic Claims
      ↓
Evidence Chunks (Structured Text + Metadata)
      ↓
Authoritative Source (Source ID + URL)
      ↓
Official Document (Document ID + Standard/Order No)
      ↓
Exact Clause & Page Number (Clause X.Y, Page N)
```

---

## 4. Query Intent Taxonomy

| Intent Code | Intent Category | Purpose | Example Query |
| :--- | :--- | :--- | :--- |
| `standard_lookup` | Standard Lookup | Lookup by standard number or title | *"What does IS 16102 cover?"* |
| `standard_recommendation` | Recommendation | Map product description to applicable standards | *"I manufacture 9W LED lamps, which standards apply?"* |
| `qco_applicability` | Regulatory Status | Check whether certification is mandatory, voluntary, or conditional | *"Is BIS certification compulsory for LED bulbs in India?"* |
| `scheme_guidance` | Scheme & Process | Explain certification routes, procedures, and required documents | *"How do I apply for CRS registration for lighting products?"* |
| `testing_parameters` | Technical & Testing | Query specific clauses, test methods, tolerances, and limits | *"What is the high-voltage test voltage specified in Clause 8?"* |
| `laboratory_search` | Laboratory Search | Identify recognized labs with authorized scopes | *"Where can I test my lamps in Gujarat?"* |
| `hallmarking_inquiry` | Hallmarking | Gold/Silver purity, HUID rules, and AHC verification | *"How do I verify a 6-digit HUID?"* |
| `consumer_rights` | Consumer Affairs | Mark validation and grievance filing via BIS Care | *"How do I verify an R-number on a product label?"* |

---

> [!NOTE]
> All concrete standard numbers, order identifiers, dates, clauses, and laboratory listings mentioned above serve as structural schemas and illustrative examples. Factual values are dynamically retrieved from verified entries in the BIS Source Registry and knowledge base.
