# SIH Problem Statement Requirements Specification

**Document Version**: 1.1  
**Phase**: Phase 1 — SIH PS Requirements & System Scope  
**Authoritative Baseline**: Smart India Hackathon (SIH) — Bureau of Indian Standards (BIS) Technical Assistant  

---

## 1. Problem Background

The **Bureau of Indian Standards (BIS)** is the National Standard Body of India established under the *BIS Act 2016* for the harmonious development of standardisation, conformity assessment, and quality assurance of goods and articles. 

Stakeholders—including domestic and foreign manufacturers, MSMEs, regulatory authorities, testing laboratories, jewellers, and everyday consumers—frequently require access to complex regulatory information across diverse BIS operations:
- Identifying relevant Indian Standards (IS codes) for manufactured goods.
- Understanding mandatory conformity orders (Quality Control Orders - QCOs) issued by central ministries.
- Navigating conformity assessment schemes (e.g. Product Certification, Compulsory Registration, Hallmarking).
- Locating accredited testing laboratories and understanding testing parameters.
- Verifying licence validity, hallmark authenticity, and consumer safety rights.

Currently, this information is distributed across technical standards, gazette notifications, product manuals, guidelines, and departmental portals, presenting a high cognitive barrier.

---

## 2. Core Problem

To design and build an **AI-powered Technical Assistant** that interacts with diverse users in natural language, retrieves authoritative regulatory and technical information from authorized BIS knowledge sources, and generates precise, truthful, and evidence-grounded answers with verifiable citations.

---

## 3. Requirements Classification Architecture

To ensure strict engineering integrity and avoid falsely attributing domain-specific facts or engineering interpretations as explicit PS text, our requirements follow a 3-tier classification:

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. PS_EXPLICIT: Directly stated as a requirement by the SIH PS.           │
├────────────────────────────────────────────────────────────────────────────┤
│ 2. ENGINEERING_DERIVED: System requirement derived to satisfy the PS.      │
├────────────────────────────────────────────────────────────────────────────┤
│ 3. DOMAIN_KNOWLEDGE: BIS domain facts acquired from authoritative sources. │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Expected Assistant Capabilities (Derived Requirements)

The system must deliver the following explicit capabilities derived from the SIH Problem Statement:

### 4.1 Indian Standards Questions (RQ-001)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Answer factual, technical, and regulatory questions concerning Indian Standards.
- **Scope**: Retrieve specific clauses, specifications, test methods, tolerances, and dimensional/chemical limits.
- **Engineering Interpretation**: Differentiate active standard editions from superseded historical versions.

### 4.2 Standard Recommendation (RQ-002)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Recommend applicable Indian Standards based on natural language product descriptions, functions, raw materials, or trade synonyms.
- **Scope**: Support users who do not know the standard code (e.g., *"I manufacture electric ceiling fans. Which BIS standard applies to my product?"*).

### 4.3 BIS Certification Schemes (RQ-003)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Guide users on applicable BIS conformity assessment schemes and statutory conformity requirements.
- **Scope**: Explain governing schemes and accurately identify mandatory enforcement under central ministry QCOs vs voluntary standard scope.
- **Domain Knowledge Binding**: Maps dynamically to Scheme-I (ISI Mark), Scheme-II (CRS), Scheme-IV (Hallmarking), etc., from authorized BIS registers (`data/requirements/bis_domain_knowledge_specs.json`).

### 4.4 Certification Processes & Licensing (RQ-004)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Explain procedural steps, documentation, factory inspection guidelines, and testing schedules required to obtain and maintain a BIS licence or registration.
- **Scope**: Outline application steps, Product Manuals, and Schemes of Inspection and Testing (SIT).

### 4.5 Consumer Queries (RQ-005)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Answer consumer-facing verification questions regarding standard marks, licences, registrations, hallmarks, and reporting of counterfeit marks.
- **Scope**: Provide guidance on verification workflows and the official **BIS Care** mobile platform.

### 4.6 Hallmarking Guidance (RQ-006)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Guide users regarding gold and silver hallmarking processes, purity specifications, hallmark verification, and recognized assaying centers.
- **Domain Knowledge Binding**: Explains 6-digit Hallmark Unique Identification (HUID) and Assaying & Hallmarking Centres (AHCs).

### 4.7 Testing Laboratories (RQ-007)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Suggest relevant BIS central/regional laboratories and recognized partner testing laboratories equipped to test specific commodities under designated Indian Standards.

### 4.8 Multilingual Interaction (RQ-008)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Support multilingual interaction (English, Hindi, and regional Indian languages) to enable access for diverse stakeholders across India.

### 4.9 Authorized Knowledge Sources (RQ-009)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Ground all factual responses strictly in authorized BIS knowledge sources without ungrounded assumptions.

### 4.10 Source-Backed Responses & Citations (RQ-010)
- **Classification**: `PS_EXPLICIT`
- **Capability**: Provide references to relevant documents and specific clauses for all factual claims.

---

## 5. Knowledge Source Architecture & Domain Taxonomy

The system architecture organizes BIS knowledge into 6 engineering knowledge domains (`data/requirements/bis_knowledge_domains.json`):
- **KD-001**: Indian Standards Specifications & Amendments
- **KD-002**: Certification & Conformity Assessment (QCOs, Schemes, Manuals, SIT)
- **KD-003**: Testing and Laboratories (Test parameters, Lab directories)
- **KD-004**: Hallmarking (Assaying, Purity standards, HUID, AHC)
- **KD-005**: Consumer Information & Verification (BIS Care, Licence ledgers)
- **KD-006**: General BIS Services & Statutory Frameworks (*BIS Act 2016*)

*(Note: These domains represent an engineering taxonomy created to organize the required BIS corpus, rather than official categories defined by the PS text).*

---

## 6. PS Requirements vs Project Engineering Targets

To maintain transparency, we explicitly separate high-level PS requirements from internal engineering performance benchmarks:

| Parameter | Type | Standard / Threshold |
|---|---|---|
| **Indian Standards Q&A** | PS Requirement | Supported across all indexed standard specifications |
| **Multilingual Interaction** | PS Requirement | English & Hindi natural interaction with regional extensibility |
| **Source-Backed Responses** | PS Requirement | Granular document, standard edition, and clause locators |
| **Zero Hallucination Gate** | Safety & Quality Policy | 0 unverified standards, QCOs, schemes, or tolerances |
| **Intent Classification Accuracy** | Project Engineering Target | $\ge 98\%$ on benchmark query suites |
| **Product Resolution Precision** | Project Engineering Target | $\ge 95\%$ on natural language queries |
| **Retrieval Clause Recall** | Project Engineering Target | $\ge 95\%$ on top-5 ranked chunks |
| **End-to-End Latency** | Project Engineering Target | $< 2.5\text{s}$ average response time |

---

## 7. Traceability Summary

| Req ID | Title | Source Basis | System Components | Verification Suite |
|---|---|---|---|---|
| **RQ-001** | Indian Standards Q&A | `PS_EXPLICIT` | `StandardsRegistry`, `UnifiedHybridRetriever` | `test_rag_pipeline.py` |
| **RQ-002** | Standard Recommendation | `PS_EXPLICIT` | `ProductResolver`, `QueryUnderstandingEngine` | `test_product_resolver_v6.py` |
| **RQ-003** | Certification Scheme Guidance | `PS_EXPLICIT` | `SchemeRegistry`, `QCORegistry` | `test_certification_chain_v5.py` |
| **RQ-004** | Certification Process | `PS_EXPLICIT` | `ProductManualRegistry`, `SITRegistry` | `test_batch_c_product_manuals_sit.py` |
| **RQ-005** | Consumer Queries | `PS_EXPLICIT` | `ConsumerRegistry`, `LicenceRegistry` | `test_batch_d_laboratories_licences_crs.py` |
| **RQ-006** | Hallmarking Guidance | `PS_EXPLICIT` | `HallmarkRegistry`, `CertificationChainReasoner` | `test_hallmarking_registry.py` |
| **RQ-007** | Testing Laboratories | `PS_EXPLICIT` | `LaboratoryRegistry`, `TestRegistry` | `test_batch_d_laboratories_licences_crs.py` |
| **RQ-008** | Multilingual Interaction | `PS_EXPLICIT` | `MultilingualQueryLayer` | Phase 10 Multilingual Suite |
| **RQ-009** | Authorized Knowledge Sources | `PS_EXPLICIT` | `SourceRegistry`, `EvidenceRegistry` | `test_source_registry_v4.py` |
| **RQ-010** | Source-Backed Responses | `PS_EXPLICIT` | `StandardizedCitationFormatter` | `test_citation_formatter.py` |
