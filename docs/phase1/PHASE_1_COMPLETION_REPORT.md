# Phase 1 Completion Report: SIH PS Requirements & System Scope

**Project**: BIS AI Technical Assistant  
**Phase**: Phase 1 of 14  
**Date**: 2026-09-02  
**Status**: **COMPLETED & APPROVED (100% Passed)**  

---

## 1. Source Problem Statement (PS)
The foundation of this system is derived directly from the official **Smart India Hackathon (SIH)** problem statement issued by the **Bureau of Indian Standards (BIS)**:
> *"Development of an AI-powered conversational assistant to help citizens, manufacturers, consumers, and regulators understand Indian Standards, navigate BIS conformity schemes, identify testing laboratories, verify hallmarking, and receive grounded answers backed by authorized BIS knowledge sources."*

---

## 2. Explicit PS Requirements & 3-Tier Classification

We have formalized the requirements into our version-controlled registry ([`data/requirements/sih_requirements.json`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/data/requirements/sih_requirements.json)) with clean 3-tier classification:
- **`PS_EXPLICIT`**: Core capabilities directly required by the SIH PS.
- **`ENGINEERING_DERIVED`**: Architectural mechanisms designed to operationalize the PS.
- **`DOMAIN_KNOWLEDGE`**: Specific BIS operational facts acquired dynamically from authorized BIS registers ([`data/requirements/bis_domain_knowledge_specs.json`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/data/requirements/bis_domain_knowledge_specs.json)).

### Explicit Requirements:
1. **RQ-001 (MUST | PS_EXPLICIT)**: Answer Indian Standards questions (technical specifications, clauses, test limits).
2. **RQ-002 (MUST | PS_EXPLICIT)**: Recommend applicable standards based on natural language product descriptions.
3. **RQ-003 (MUST | PS_EXPLICIT)**: Guide users on BIS certification schemes and mandatory conformity requirements.
4. **RQ-004 (MUST | PS_EXPLICIT)**: Explain certification processes, application steps, Product Manuals, and SIT testing rules.
5. **RQ-005 (MUST | PS_EXPLICIT)**: Answer consumer queries regarding licence verification, registration numbers, hallmark authenticity, and BIS Care complaints.
6. **RQ-006 (MUST | PS_EXPLICIT)**: Guide users regarding gold and silver hallmarking processes, purity specifications, and recognized assaying centers.
7. **RQ-007 (MUST | PS_EXPLICIT)**: Suggest BIS-recognized testing laboratories equipped for specific Indian Standards.
8. **RQ-008 (MUST | PS_EXPLICIT)**: Support multilingual interaction (Hindi and English with extensible Indian languages).
9. **RQ-009 (MUST | PS_EXPLICIT)**: Ground all factual responses strictly in authorized BIS knowledge sources.
10. **RQ-010 (MUST | PS_EXPLICIT)**: Provide source-backed responses with granular document and clause citations.

---

## 3. Engineering Interpretation

The problem statement requires a **deterministic, evidence-gated regulatory intelligence architecture**. The assistant does not function as a generic chatbot that hallucinates plausible-sounding standard numbers. Instead, it operates as a precision legal-technical search engine:
- Natural language query $\to$ Entity & Intent parsing $\to$ Hybrid retrieval from verified corpus $\to$ Knowledge graph relationship validation $\to$ Evidence-gated generation with strict citations.

---

## 4. Knowledge Domains

Structured into 6 engineering knowledge domains ([`data/requirements/bis_knowledge_domains.json`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/data/requirements/bis_knowledge_domains.json)):
- `KD-001`: Indian Standards Specifications & Amendments
- `KD-002`: Certification & Conformity Assessment (QCOs, Schemes, Manuals, SIT)
- `KD-003`: Testing and Laboratories (Test parameters, Lab directories)
- `KD-004`: Hallmarking (Assaying, Purity standards, HUID, AHC)
- `KD-005`: Consumer Information & Verification (BIS Care, Licence ledgers)
- `KD-006`: General BIS Services & Statutory Frameworks (*BIS Act 2016*)

*(Note: These knowledge domains are an engineering taxonomy created to organize the BIS knowledge required to satisfy the SIH PS, rather than official categories defined by the PS text).*

---

## 5. System Capabilities & Query Taxonomy

The system establishes 19 domain intents and 6 query states ([`data/requirements/query_intents.json`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/data/requirements/query_intents.json)):
- **Domain Intents**: Standard Lookup, Recommendation, Requirements, Related Standards, Certification Schemes, Processes, Licensing, QCO Lookup, Mandatory Status, Testing Requirements, Test Methods, Laboratories, Hallmarking, HUID, Assaying, Consumer Queries, BIS Care, Technical Queries, General BIS Services.
- **Query States & Scope Classification**: `STANDARD_CONVERSATION`, `AMBIGUOUS`, `OUT_OF_SCOPE`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_REQUEST`, `MULTILINGUAL_INPUT`.

---

## 6. Traceability Matrix

Documented in detail in [`docs/phase1/PS_TRACEABILITY_MATRIX.md`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/docs/phase1/PS_TRACEABILITY_MATRIX.md). Every requirement (RQ-001 through RQ-010) is linked to concrete system components, knowledge domains, and verification test suites.

---

## 7. Answer Grounding Policy

Documented in [`docs/phase1/ANSWER_GROUNDING_POLICY.md`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/docs/phase1/ANSWER_GROUNDING_POLICY.md). Enforces claim-appropriate evidence tiering across the **8 Immutable Grounding Rules**:
- Rule 1: No invention of BIS standards
- Rule 2: No invention of QCOs
- Rule 3: No invention of certification schemes
- Rule 4: No invention of testing parameters & tolerances
- Rule 5: No invention of laboratory accreditations
- Rule 6: Evidence-backed mandatory vs voluntary claims
- Rule 7: Deterministic safe refusal on unverified or out-of-scope queries
- Rule 8: Granular document and clause provenance on every factual statement

---

## 8. Evaluation Policy & Performance Benchmarks

Documented in [`docs/phase1/EVALUATION_POLICY.md`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/docs/phase1/EVALUATION_POLICY.md). Establishes a 7-stage verification pipeline for every query (Intent Understanding $\to$ Retrieval Precision $\to$ Evidence Binding $\to$ Scheme Logic $\to$ Technical Value Precision $\to$ Citation Completeness $\to$ Scope Safety), while clearly separating high-level PS capabilities from internal project engineering target benchmarks.

---

## 9. Scope Boundaries & Anti-Hallucination Protections

Documented in [`docs/phase1/PS_SCOPE_BOUNDARIES.md`](file:///Users/sameer/Documents/SIH%202026/bis-ai-assistant/docs/phase1/PS_SCOPE_BOUNDARIES.md).
- Decouples the project from arbitrary assumptions.
- The 25-product suite is formally defined as a **Representative Product Benchmark** for regression testing and precision verification, rather than a hard boundary limit of the BIS corpus.

---

## 10. Acceptance Criteria Checklist

- [x] All 10 explicit PS requirements documented with source basis classification: **YES**
- [x] All explicit PS capabilities mapped to components & test suites: **YES**
- [x] Required BIS engineering knowledge domains identified: **YES**
- [x] Authorized BIS source requirements formalized with claim-appropriate evidence tiering: **YES**
- [x] Evidence and citation requirements defined: **YES**
- [x] Multilingual requirements incorporated: **YES**
- [x] Multi-dimensional evaluation policy defined with target distinctions: **YES**
- [x] Scope protection established (25 products = Representative Benchmark): **YES**

---

## 11. Phase 1 Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sameer/Documents/SIH 2026/bis-ai-assistant
collected 5 items

tests/requirements/test_ps_requirements.py::test_all_10_ps_requirements_exist PASSED [ 20%]
tests/requirements/test_ps_requirements.py::test_requirements_classification_and_basis PASSED [ 40%]
tests/requirements/test_ps_requirements.py::test_knowledge_domains_complete_mapping PASSED [ 60%]
tests/requirements/test_ps_requirements.py::test_query_intents_cover_requirements PASSED [ 80%]
tests/requirements/test_ps_requirements.py::test_phase1_documentation_artifacts_exist PASSED [100%]

============================== 5 passed in 0.03s ===============================
```

---

## 12. Phase 2 Entry Criteria

Phase 1 is now formally completed. The system is ready to proceed to:
**Phase 2: BIS Authorized Knowledge-Source Architecture**

### Key Objectives for Phase 2:
1. Systematically catalog all authorized BIS source families (Standards, QCOs, Product Manuals, SIT, Test Specifications, Lab Registers, Licences, Hallmarking Orders).
2. Establish automated discovery, download, and ingestion protocols for each family.
3. Design document versioning, amendment detection, and cryptographic SHA-256 provenance tracking.
