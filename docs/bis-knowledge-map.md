# BIS Knowledge Map

This document establishes the official knowledge taxonomy and domain mappings for the **BIS AI Intelligent Assistant for Indian Standards**. It defines the 12 core knowledge domains, their authoritative provenance, update frequencies, and user query mappings.

---

## Domain Overview & Entity Taxonomy

```text
                               ┌────────────────────────────────┐
                               │   BIS Knowledge Ecosystem      │
                               └───────────────┬────────────────┘
                                               │
        ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
        ▼                      ▼                               ▼                      ▼
┌────────────────┐    ┌─────────────────┐             ┌─────────────────┐    ┌─────────────────┐
│ Standards &    │    │ Regulatory &    │             │ Conformity &    │    │ Public &        │
│ Technical Spec │    │ Enforcement     │             │ Infrastructure  │    │ Consumer        │
├────────────────┤    ├─────────────────┤             ├─────────────────┤    ├─────────────────┤
│ • Standards    │    │ • QCOs          │             │ • Schemes       │    │ • Hallmarking   │
│ • Versions     │    │ • Amendments    │             │ • Licensing     │    │ • Consumer Info │
│ • Technical    │    │ • Gazette Notif │             │ • Testing       │    │ • FAQs/Guides   │
│ • References   │    │                 │             │ • Laboratories  │    │                 │
└────────────────┘    └─────────────────┘             └─────────────────┘    └─────────────────┘
```

---

## Detailed Knowledge Domains

### 1. Indian Standards (IS)
* **What Information Exists**: Formal technical standard documents outlining scope, terminology, product classification, constructional requirements, performance benchmarks, marking requirements, and normative annexes.
* **Who Publishes It**: Bureau of Indian Standards (Technical Committee / Division Councils e.g., ETD, LITD, MED, CHD, TXD, FAD).
* **How Authoritative Is It**: **Tier 1 (Highest)** — Formal national standard.
* **How Often Can It Change**: Periodic revision cycle (typically every 5 years with interim amendments or reaffirmations).
* **Target User Questions**:
  * *"What is the standard for self-ballasted LED lamps?"*
  * *"What does Clause 6 of IS 16102 (Part 1) state regarding marking requirements?"*
  * *"What are the insulation resistance tolerances specified in the standard?"*

---

### 2. Standards Versions, Amendments & Reaffirmations
* **What Information Exists**: Corrigenda, amendment slips (Amendment 1, Amendment 2), year-of-publication changes, withdrawal notices, supersession notices, and reaffirmation dates.
* **Who Publishes It**: Bureau of Indian Standards (Gazette notifications and BIS Official Standards Portal).
* **How Authoritative Is It**: **Tier 1** — Legally alters or supersedes clauses of parent standards.
* **How Often Can It Change**: As needed when technical requirements are updated or errors corrected.
* **Target User Questions**:
  * *"Is IS 16102 (Part 1):2012 still valid or has it been amended?"*
  * *"What changes were introduced in Amendment 2 to IS 16102 (Part 2)?"*
  * *"Which version of the standard is currently active?"*

---

### 3. Quality Control Orders (QCOs) & Technical Regulations
* **What Information Exists**: Statutory orders issued by line Ministries making specific Indian Standards mandatory for manufacture, import, sale, and distribution in India. Specifies product scope, custom tariff headings (HSN codes), enforcement dates, and exemption rules.
* **Who Publishes It**: Central Government Ministries (DPIIT, MeitY, Ministry of Power, Ministry of Steel, Ministry of Mines, Ministry of Chemicals & Fertilizers) published via the Gazette of India.
* **How Authoritative Is It**: **Tier 1 (Statutory Law)** — Overrides voluntary status of standards; legally binding under BIS Act 2016.
* **How Often Can It Change**: Issued continuously; extension notifications frequently update enforcement deadlines.
* **Target User Questions**:
  * *"Is BIS certification mandatory for selling LED bulbs in India?"*
  * *"What is the enforcement date of the Electronics and IT Goods QCO for lighting?"*
  * *"Are imported LED drivers exempt from QCO compliance if used for R&D?"*

---

### 4. BIS Certification Schemes
* **What Information Exists**: Conformity assessment schemes defined under BIS (Conformity Assessment) Regulations, 2018:
  * **Scheme I**: ISI Mark Scheme (Product Certification with factory audit & surveillance)
  * **Scheme II**: Compulsory Registration Scheme (CRS) (Self-declaration based on lab test reports)
  * **Scheme IV**: Certificate of Conformity (CoC)
  * **Scheme X**: Management System Certification
* **Who Publishes It**: Bureau of Indian Standards (Conformity Assessment Department).
* **How Authoritative Is It**: **Tier 1 (Regulatory)** — Mandated procedure under BIS Act.
* **How Often Can It Change**: Stable; procedural guidelines updated annually or biennially.
* **Target User Questions**:
  * *"Does an LED bulb fall under Scheme I (ISI) or Scheme II (CRS)?"*
  * *"What is the difference between ISI Mark and CRS Registration?"*
  * *"Can an overseas manufacturer apply for Scheme II registration directly?"*

---

### 5. Licensing & Registration Procedures
* **What Information Exists**: Step-by-step application flows, portal guides (Manakonline / CRS portal), documentation checklists, factory audit criteria, fee structures (application, processing, marking/inspection fees), renewal timelines, and surveillance requirements.
* **Who Publishes It**: Bureau of Indian Standards (Central Marks Department / CRS Branch).
* **How Authoritative Is It**: **Tier 2 (Official Procedural Manuals)**.
* **How Often Can It Change**: Process digitalization and fee schedules updated periodically.
* **Target User Questions**:
  * *"What documents are required to apply for a BIS CRS license for LED lamps?"*
  * *"How long is a BIS registration certificate valid before renewal?"*
  * *"What is the government fee structure for an MSME startup applying for BIS certification?"*

---

### 6. Testing Requirements & Test Methods
* **What Information Exists**: Detailed test descriptions (e.g., high voltage breakdown, insulation resistance, harmonic current emissions, lumen maintenance, color temperature, ingress protection), test setup procedures, sampling criteria, pass/fail thresholds, and standard operating limits.
* **Who Publishes It**: BIS Standards (Sections on Test Methods) & BIS Product Manuals / Guidelines for Testing.
* **How Authoritative Is It**: **Tier 1 / Tier 2**.
* **How Often Can It Change**: Updated during standard amendments or test manual revisions.
* **Target User Questions**:
  * *"What tests must an LED bulb undergo to comply with IS 16102 (Part 1)?"*
  * *"What is the required sample size for life testing of self-ballasted LED lamps?"*
  * *"What is the maximum permissible total harmonic distortion (THD) under IS 16102 (Part 2)?"*

---

### 7. Laboratories & Laboratory Recognition Scheme (LRS)
* **What Information Exists**: Registry of BIS in-house Central/Regional/Branch labs and external private/government testing laboratories recognized under the BIS LRS. Contains laboratory name, contact, city, state, accreditation details (NABL), recognition validity, and **exact test scope** (list of standards and clauses the lab is authorized to test).
* **Who Publishes It**: Bureau of Indian Standards (Laboratory Recognition Department / LIMS portal).
* **How Authoritative Is It**: **Tier 1 (Official Registry)**.
* **How Often Can It Change**: Dynamic; monthly updates as recognition scopes are granted, suspended, or renewed.
* **Target User Questions**:
  * *"Which BIS recognized laboratories in Delhi NCR can test LED lamps under IS 16102?"*
  * *"Is Laboratory XYZ authorized to conduct endurance testing under Clause 13?"*
  * *"Where can I send my LED driver sample for safety compliance testing?"*

---

### 8. Hallmarking of Precious Metals
* **What Information Exists**: Mandatory hallmarking regulations for gold and silver jewelry, purity grades (e.g., 24K, 22K - 916, 18K - 750, 14K - 585), Assaying and Hallmarking Centre (AHC) recognition, Hallmarking Unique Identification (HUID) specifications, consumer rights, and jeweler registration.
* **Who Publishes It**: BIS Hallmarking Department & Ministry of Consumer Affairs.
* **How Authoritative Is It**: **Tier 1 (Statutory & Regulatory)**.
* **How Often Can It Change**: Expansion of mandatory districts and HUID guidelines updated periodically.
* **Target User Questions**:
  * *"What are the three mandatory marks on hallmarked gold jewelry?"*
  * *"How can a customer verify a 6-digit alphanumeric HUID code?"*
  * *"What compensation is a consumer entitled to if hallmarked gold fails purity testing?"*

---

### 9. Consumer Affairs & Grievance Redressal
* **What Information Exists**: Consumer verification mechanisms (e.g., BIS Care App, "Verify R-Number", "Verify License/CML"), complaint filing process against sub-standard or counterfeit products, penalty provisions under BIS Act 2016, and guidelines on Standards Clubs in schools/colleges.
* **Who Publishes It**: BIS Consumer Affairs Department (CAD) & Ministry of Consumer Affairs.
* **How Authoritative Is It**: **Tier 2 (Official Guidelines / Public Service Information)**.
* **How Often Can It Change**: Periodic revisions to portals and consumer outreach initiatives.
* **Target User Questions**:
  * *"How do I check if the ISI mark on an electrical appliance is genuine?"*
  * *"How can I file a complaint if a certified LED bulb fails prematurely?"*
  * *"What does the R-number under the CRS mark represent?"*

---

### 10. Technical Information & Performance Parameters
* **What Information Exists**: Electrical, optical, thermal, and mechanical parameters; normative formulas; tolerance tables; interchangeability dimensions (e.g., E27, B22d lamp caps); environmental endurance specs.
* **Who Publishes It**: BIS Standards (Clauses, Tables, Annexes) & International Harmonized Bodies (IEC, ISO).
* **How Authoritative Is It**: **Tier 1**.
* **How Often Can It Change**: Tied to standard revision cycles.
* **Target User Questions**:
  * *"What is the standard creepage distance requirement for 230V mains components?"*
  * *"What are the dimension limits for B22d cap fitment under Indian standards?"*
  * *"How is luminous efficacy measured for LED lighting?"*

---

### 11. FAQs & Official Guidelines / Product Manuals
* **What Information Exists**: Grouping guidelines for product families, sample selection rules, series guidelines for CRS registration, official clarifications issued to manufacturers, and BIS portal FAQs.
* **Who Publishes It**: BIS Technical Committees and Branch Offices.
* **How Authoritative Is It**: **Tier 2 (Advisory / Interpretative)**.
* **How Often Can It Change**: Frequently updated as practical implementation challenges arise.
* **Target User Questions**:
  * *"Can multiple wattage variants (e.g., 7W, 9W, 12W) be registered under a single series application?"*
  * *"What is the lead time for CRS registration approval?"*
  * *"Who is an Authorized Indian Representative (AIR) for foreign manufacturers?"*

---

### 12. Related & Cross-Referenced Standards (Normative References)
* **What Information Exists**: Cross-cutting standards referenced within core product standards (e.g., safety of lamp controlgear IS 15885, general lighting safety IS 16103, environmental testing IS 9000, degrees of protection provided by enclosures IS/IEC 60529).
* **Who Publishes It**: BIS Sectional Committees.
* **How Authoritative Is It**: **Tier 1 (Normatively Binding where cited)**.
* **How Often Can It Change**: Independent lifecycle per standard.
* **Target User Questions**:
  * *"Which driver safety standard is referenced by IS 16102 (Part 1)?"*
  * *"What ingress protection (IP) standard applies to outdoor LED luminaires?"*
  * *"Which EMC and EMI standards must be satisfied alongside safety standards?"*
