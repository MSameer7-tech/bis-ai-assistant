# Phase 12.2A: Structured Extraction Reconciliation Audit

## Objective
Reconcile and audit the Phase 12.2 derived dataset to ensure it accurately models explicit LIMS scope and testing fee structures from the immutable `v22` corpus, without fabricating data, omitting granular details, or collapsing distinct elements into lossy representations.

## 1. Input
- **v22 Records**: 1135
- **v22 SHA256**: `68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`

## 2. Derived Dataset Metrics
- **Total Derived Objects**: 1179
- **Source Records Producing Objects**: 1135
- **Source Records Producing NO Objects**: 0
- **Objects by Type**:
  - `DOCUMENT`: 910
  - `LABORATORIES`: 180
  - `LAB_SCOPE`: 44
  - `TESTING_FEE`: 44
  - `UNKNOWN`: 1

## 3. LIMS-Specific Reconciliation
- **LIMS Source Records**: 224 (includes records in LABORATORIES domain such as RECOGNIZED_LAB, LAB_SCOPE_TEST_CHARGE, etc.)
- **Laboratory Objects**: 180
- **Scope Objects**: 44
- **Fee Objects**: 44
- **Explicit Fee Structures in Source**: 44
- **Fee Structures Preserved**: 44
- **Fee Structures Collapsed**: 0 (Granularity successfully maintained)

## 4. Relationship Audit
- **TESTS_STANDARD**: 16
- **BELONGS_TO_LAB**: 44
- **HAS_FEE**: 44
- **FEE_FOR_SCOPE**: 44
- **Unsupported Relationships**: 0
- **Omitted Explicit Relationships**: 0

## 5. Provenance Audit
- **Valid Links to Source ID**: 1179
- **Invalid Links**: 0
- **Missing Provenance**: 0
- **Orphaned Derived Objects**: 0

## 6. Determinism Audit
The extractor was run deterministically in isolated temporary outputs to ensure perfect reproducibility.
- **Run 1 SHA256**: `c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486`
- **Run 2 SHA256**: `c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486`
- **Identical**: YES

## 7. Invalid Record Shielding
The known metadata defect record `LAB-UNKNOWN_79dcb12d` was specifically checked.
- **Derived Representation**: `[UNKNOWN]`
- **Fabricated Attributes**: NO (Zero fabricated laboratory features, scopes, fees, or relationships)

## 8. Conclusion
The audit demonstrates that the derived knowledge items mathematically and structural match the source evidence. The `LAB_SCOPE` and `TESTING_FEE` objects preserve the exact granularity expressed in the `v22` source records without collapsing fees or fabricating semantics.

**`PHASE_12_2A_STATUS: PASS`**
**`PHASE_12_2_RECONCILIATION: APPROVED`**
