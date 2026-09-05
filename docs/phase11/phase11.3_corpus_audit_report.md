# Phase 11.3 Corpus Audit

## Audit Run Metadata
- **Audit Run ID**: audit_202609d162023
- **Timestamp**: 2026-09-04T16:20:23.521101
- **Input File**: data/bootstrap/bis_missing_domains_dataset_v22.jsonl
- **Input SHA256**: 68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe
- **Total Records**: 1135

## 1. Corpus Integrity
- **Valid Records**: 1134
- **Invalid Records**: 1

## 2. Provenance
- **Complete**: 577
- **Incomplete**: 558
- **Missing**: 0

- **Accessible Sources**: 1131
- **Inaccessible Sources**: 4
- **Extraction Success**: 1135
- **Extraction Failure**: 0

## 3. Duplicate Analysis
- **Duplicate IDs**: 0
- **Duplicate Source Hashes**: 0
- **Exact Duplicate Records**: 0
- **Unique Canonical URLs**: 204
- **Shared Source URL Groups**: 81
- **Records in Shared Source URL Groups**: 1012

*Note: Shared source URL != duplicate knowledge record. Multiple legitimate records (like LIMS scopes) may originate from the same endpoint.*

## 4. Knowledge Entity Coverage
### Documents
- **Document Record Count**: 50
- **Unique Document Identity Count**: 50
- **Unique Document URL Count**: 48

### Laboratories
- **Laboratory Record Count**: 32
- **Unique Laboratory Name Count**: 32
- **Unique Laboratory Scope Record Count**: 514
*(Explicit sub-categories found: Recognized: 8, Empanelled: 6)*

### Standards
- **Unique Normalized IS Numbers**: 110
- **Unique Raw IS References**: 112

### Fees
- **Explicit Fee Record Count**: 201
- **Fee Records with Amount**: 189
- **Fee Records without Amount**: 12
- **Fee Records with Currency**: 188
- **Fee Records with Effective Date**: 188

## 5. Domain Coverage
(Detailed by domain in JSON output)

## 6. Authority Coverage
(Detailed by authority in JSON output)

## 7. Freshness
- Records evaluated successfully for dates.

## 8. Supersession Candidates
- Candidates: 21

## 9. Conflict Analysis
- Potential Conflicts: 0
- Manual Review Candidates: 0

## 10. Gap Analysis
- **Critical Gaps**: 0
- **High Gaps**: 0
- **Medium Gaps**: 2
- **Low Gaps**: 3

## 11. Question-Level Coverage
- Laboratories -> IS mapping: PARTIAL_EVIDENCE
- Testing fees: PARTIAL_EVIDENCE
- Jeweller Registration: AVAILABLE_EVIDENCE
- HUID details: AVAILABLE_EVIDENCE
- Consumer complaints: AVAILABLE_EVIDENCE

## 12. Audit Reconciliation
The previous execution reported discrepancies between JSON and Markdown (e.g., 931 duplicate URLs). This occurred because shared URLs from endpoints (e.g., LIMS structured data) were mistakenly counted as "duplicate records" in one output but ignored in another. The current execution uses a single source of truth for both JSON and Markdown, explicitly differentiates "Shared source URL groups" from "Exact duplicate records", and applies mutually exclusive provenance buckets. 

## 13. Final Recommendation
**FREEZE_V22**

## 14. Invalid Record Review
- **Record ID**: LAB-UNKNOWN_79dcb12d
- **Classification**: METADATA_DEFECT
- **Retrieval Impact**: NO_RETRIEVAL_IMPACT
- **Authority Impact**: AUTHORITATIVE_EVIDENCE_UNUSABLE
- **Knowledge Content Usable**: False
- **Recommended Action**: Do nothing. Leave record in corpus for traceability. Retrieval impact is zero due to lack of substantive knowledge content.
