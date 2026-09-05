# Phase 8.14: Knowledge Coverage Audit Report

## A. Executive Summary
This report quantifies the actual existing knowledge coverage of the integrated BIS RAG system across 12 knowledge domains. It deterministically measures Source Presence, Retrieval Coverage, Evidence Sufficiency, and Provenance Completeness without generating LLM text.

## B. Overall Coverage Statistics
- **Total Probes**: 13
- **Applicable Probes**: 5
- **Not-Applicable/Missing Probes**: 8
- **Passed Probes**: 5
- **Failed Probes**: 8
- **Source Presence %**: 30.8%
- **Retrieval Coverage %**: 38.5%
- **Evidence Sufficiency %**: 38.5%
- **Provenance Completeness %**: 38.5%

## C. 12-Domain Coverage Matrix
| Domain | Source Presence | Retrieval Coverage | Evidence Sufficiency | Provenance Completeness | Overall Status | Gap Classification |
|--------|-----------------|--------------------|----------------------|-------------------------|----------------|--------------------|
| PRODUCT_STANDARD | ✅ | ✅ | ✅ | ✅ | 🟢 COVERED | NO_GAP |
| STANDARD_METADATA | ✅ | ✅ | ✅ | ✅ | 🟢 COVERED | NO_GAP |
| TECHNICAL_CLAUSES | ✅ | ✅ | ✅ | ✅ | 🟢 COVERED | NO_GAP |
| CERTIFICATION | ✅ | ✅ | ✅ | ✅ | 🟢 COVERED | NO_GAP |
| TESTING_SIT | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| LABORATORIES | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| HALLMARKING | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| QCO_GAZETTE | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| LICENCES | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| CONSUMER_BIS_CARE | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| ACTS_RULES | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |
| FAQ_GUIDES | ❌ | ❌ | ❌ | ❌ | ⚫ MISSING SOURCE | GAP_SOURCE |

## D. Per-Probe Results
| Probe ID | Domain | Query | Expected Intent | Actual Intent | Expected Source | Actual Source | Retrieval Result | Evidence State | Provenance State | Gap Classification | PASS/FAIL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PRB-KD001-01 | PRODUCT_STANDARD | What is the standard for Secondary Cells and Batteries for Solar Photovoltaic Application? | PRODUCT_STANDARD | PRODUCT_STANDARD | PRODUCT_STANDARD_RELATIONSHIP,RELATIONSHIP_EVIDENCE | RELATIONSHIP_EVIDENCE | PASS | SUFFICIENT | COMPLETE | NO_GAP | PASS |
| PRB-KD001-02 | PRODUCT_STANDARD | What is the standard for Quantum Flux Capacitors? | PRODUCT_STANDARD | OUT_OF_SCOPE |  |  | PASS | SUFFICIENT | COMPLETE | NO_GAP | PASS |
| PRB-KD002-01 | STANDARD_METADATA | What is the status of IS 14286 : 2010? | STANDARD_LOOKUP | STANDARD_LOOKUP | IDENTITY_EVIDENCE,STANDARD_METADATA | IDENTITY_EVIDENCE | PASS | SUFFICIENT | COMPLETE | NO_GAP | PASS |
| PRB-KD003-01 | TECHNICAL_CLAUSES | What are the requirements in Clause 7 of IS 2082 : 2018? | CLAUSE_LOOKUP | CLAUSE_LOOKUP | NORMATIVE_EVIDENCE,DOCUMENT_EVIDENCE | NORMATIVE_EVIDENCE | PASS | SUFFICIENT | COMPLETE | NO_GAP | PASS |
| PRB-KD004-01 | CERTIFICATION | Is the ISI mark mandatory for Cement Paint? | CERTIFICATION_QCO | CERTIFICATION_QCO | PROCEDURAL_EVIDENCE,DOCUMENT_EVIDENCE | PROCEDURAL_EVIDENCE | PASS | SUFFICIENT | COMPLETE | NO_GAP | PASS |
| PRB-KD005-01 | TESTING_SIT | What is the scheme of testing for IS 16270? | CERTIFICATION_QCO |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD006-01 | LABORATORIES | Which laboratories are accredited for testing IS 16270? | LABORATORY |  | LABORATORY_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD007-01 | HALLMARKING | What is the process for HUID hallmarking? | GENERAL_QA |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD008-01 | QCO_GAZETTE | What is the Gazette notification date for the QCO on Follow-up Formula? | CERTIFICATION_QCO |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD009-01 | LICENCES | Is licence number CM/L-1234567 valid? | COMPLIANCE_CHECK |  | LICENCE_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD010-01 | CONSUMER_BIS_CARE | How do I file a complaint on the BIS Care App? | GENERAL_QA |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD011-01 | ACTS_RULES | What are the penalties under the BIS Act 2016? | GENERAL_QA |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |
| PRB-KD012-01 | FAQ_GUIDES | What is the FMCS simplified procedure? | GENERAL_QA |  | PROCEDURAL_EVIDENCE |  | MISSING_SOURCE | INSUFFICIENT | INCOMPLETE | GAP_SOURCE | FAIL |

## F. Knowledge Gaps
The following gaps were empirically identified based on corpus absence:
- **SOURCE**: Multiple domains completely lack source files (SITs, Laboratories, Hallmarking, Gazettes, Licences, Consumer Guides, Acts).
- **RETRIEVAL**: Covered domains successfully retrieve relationships, metadata, and normative evidence.

## G. Recommended Next Actions
1. **Targeted Acquisition (Phase 9)**: Acquire sources for `TESTING_SIT`, `LABORATORIES`, `HALLMARKING`, `QCO_GAZETTE`, `LICENCES`, `CONSUMER_BIS_CARE`, `ACTS_RULES`, and `FAQ_GUIDES`.
2. **Integration Expansion**: Extend retrieval logic to handle the newly acquired data structures for those domains.
3. **Do not** re-acquire normative standards or product relationships, as these are well-covered.
