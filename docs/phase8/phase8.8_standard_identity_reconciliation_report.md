# Phase 8.8: Standard Identity Extraction, Normalization and Reconciliation Report

## 1. Phase 8.7 Problem
During Phase 8.7, we discovered that 761 out of 822 unique "standard numbers" supplied by the Phase 8.6 compulsory certification source failed to resolve against the authoritative SRC-002 catalogue. The raw values contained clauses, filenames, dual standards, and lacked the "IS " prefix required for precise API resolution.

## 2. Raw Value Classification
We implemented a strict classification parser to triage the raw strings without modifying the original Phase 8.6 product relationship artifacts:
- `CONFIDENT_STANDARD_CANDIDATE` (Explicit IS prefix present)
- `STANDARD_CANDIDATE_WITH_PART` (Explicit part structure detected)
- `STANDARD_CANDIDATE_WITH_SECTION` (Explicit section structure detected)
- `STANDARD_CANDIDATE_WITH_YEAR` (Explicit year colon structure detected)
- `DUAL_STANDARD_REFERENCE` (e.g. `IS 10322 / IEC 60598`)
- `CLAUSE_REFERENCE` (e.g. `Clause 4.14`)
- `FILENAME_REFERENCE` (e.g. `.pdf`)
- `FILENAME_CONTAINING_STANDARD_CANDIDATE`
- `NON_STANDARD_NUMERIC`
- `AMBIGUOUS`

## 3. Parser Rules
- **Rejection:** Strings with "Clause", HTTP links, or explicitly unextractable structures were rejected as invalid.
- **Extraction:** We explicitly parsed base numbers (`(?:IS\s*/\s*IEC|IS|IEC)?\s*([0-9]{3,})`), parts, sections, edition years, and amendments, without falsely treating all strings with "section" as rejections.

## 4. Normalization Rules
We did not manufacture elements. Normalization string building only included components legitimately extracted from the raw string (e.g., `IS {base_number} (Part {part}/Sec {sec}) : {year}`). Base numbers missing prefixes were conservatively assigned `IS` as a primary standard candidate.

## 5. Candidate Identity Schema
Extracted candidates follow a strict canonical schema:
```json
{
  "base_number": "10322",
  "standard_prefix": "IS",
  "part": "5",
  "section": "1",
  "edition_year": "2026",
  "amendment": null
}
```

## 6. Reconciliation Process
High and Medium confidence candidates were sent through the generic SRC-002 autocomplete resolver (`GetStdNo_Bis`) and authoritative detail page (`BIS_SearchStandard.aspx`) to validate their existence and extract the true `internal_bis_id`.

## 7. Metrics
- **Total Relationships:** 960
- **Unique Raw Values:** 821
- **Candidates Extracted:** 820
- **Candidates Rejected:** 2
- **Ambiguous:** 0
- **Clause References:** 2
- **Filename References:** 1
- **Dual Standards:** 32
- **Parser Extraction Rate:** 99.8% (820 / 821 valid candidates extracted)
- **Sent to SRC-002:** 819

## 8. SRC-002 Results
- **Sent to SRC-002:** 819
- **Matched (Authoritatively Reconciled):** 63
- **Did Not Reconcile Successfully:** 756
  - **Not Found:** 746
  - **Unresolved (HTTP/Parse Errors):** 10
- **Identity Mismatch:** 0

## 9. IS 15750 Control
- **Result:** `MATCHED`
- **Internal BIS ID:** `8074`
- **Matched Standard Number:** `IS 15750 : 2006`
- **Part/Section Validation:** N/A (`part_section_validated: False`)
- **Year Match:** N/A
- **Note:** This confirms that SRC-002 correctly resolves the standard. Importantly, the generic pipeline successfully preserved the lack of a "refrigerator -> IS 15750" product mapping, keeping product scheme metadata distinct from pure standard metadata.

## 10. Dual-Standard Handling
32 instances of Dual Standard References (e.g. `IS 10322 / IEC 60598`) were successfully parsed. The primary IS candidate was sent for SRC-002 reconciliation, and the IEC reference was preserved in the output dataset as `referenced_standards`.

## 11. Part/Section Validation
Zero Part/Section mismatches occurred among the 63 matched records. (Note: many part/section records failed to resolve entirely, contributing to the `Not Found` count).

## 12. Year Validation
Zero Edition Year mismatches occurred among the matched records. Original source years were preserved in the schema.

## 13. Provenance
Every reconciled record in `standard_identity_reconciliation.jsonl` contains the original `relationship_id`, `product_name`, `raw_standard_value`, and exact `source` dictionaries (including URLs and SHA256 hashes) from Phase 8.6.

## 14. Original-Data Preservation
The original Phase 8.6 artifact `data/catalog/compulsory_certification/product_standard_relationships.jsonl` was NOT mutated. The new reconciliation file operates strictly as an overlay layer.

## 15. Regression Verification
SHA-256 pre/post snapshots verify that all critical artifacts remain byte-for-byte unchanged:
- **Phase 6 Chroma:** UNCHANGED (`68d2942b`)
- **Phase 6 BM25:** UNCHANGED (`7367e658`)
- **Phase 6 Manifests:** UNCHANGED (`8071ac85`)
- **candidate_documents.json:** UNCHANGED (`ceea4adc`)

## 16. Remaining Unresolved Identities
While we successfully structured and cleaned 99.8% of the raw values into valid canonical candidates, **746 candidates still failed to resolve** against the `SRC-002` API. This suggests that the autocomplete API on the e-Sale portal is highly restrictive, strictly requiring exact format matching, or potentially failing to list older/inactive standards uniformly.

## 17. Recommended Next Phase
Since the vast majority of valid canonical Indian Standards (e.g. `IS 10322`) still return `NOT_FOUND` from the primary `GetStdNo_Bis` endpoint, we must conduct a **Phase 8.9 Search Parameter Analysis**. We need to investigate whether alternative search mechanisms on `SRC-002` (e.g. the Advanced Search form's POST parameters) yield matches for the valid canonical candidates that the AJAX autocomplete endpoint drops.
