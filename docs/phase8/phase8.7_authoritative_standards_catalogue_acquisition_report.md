# Phase 8.7: Authoritative Indian Standards Catalogue Acquisition Report

Authoritative metadata was acquired for standards referenced by the Phase 8.6 compulsory-certification catalogue.

## 1. Input Dataset Statistics
- **Input File:** `data/catalog/compulsory_certification/product_standard_relationships.jsonl`
- **Total Relationships Processed:** 960
- **Total Attempted:** 822 (821 unique standards + 1 explicit validation case for IS 15750)

## 2. Acquisition Results
- **Unique Standards Acquired (Successful):** 58
- **Total Failures:** 764
- **Idempotent (Unchanged):** 0

### Success Rates
- **Resolver Success Rate:** 7.4% (61 / 822)
- **Metadata Retrieval Success Rate:** 100% (of those resolved)
- **Parse Success Rate:** 95.1% (58 / 61)
- **Validation Success Rate:** 100% (of those parsed)

## 3. Failure Categories
- **Resolution Failed (761):** The vast majority of standard string values extracted during Phase 8.6 from SRC-005 were messy, missing the "IS " prefix, contained embedded filenames, or referred to clauses instead of pure standard numbers. The strict SRC-002 autocomplete API correctly declined to resolve these invalid identities.
- **Parse Failed (3):** HTML structure for the metadata page did not match the expected schema for standard number extraction.
- **Validation Failed (0):** No identity mismatches were observed.
- **Metadata Fetch Failed (0):** No WAF or connection issues occurred for valid IDs.

## 4. Metadata Fields Actually Available
The authoritative SRC-002 records provided the following fields:
- `standard_number`
- `internal_bis_id`
- `title`
- `technical_committee`
- `status`
- `reaffirmed_year`
- `superseded_by`
- `amendments`

**Note:** Structured product mappings (e.g., "refrigerator -> IS 15750") are **NOT** present in the metadata. The product mapping is exclusively maintained by the Scheme data in SRC-005.

## 5. IS 15750 Validation Result
- **Resolved via `GetStdNo_Bis`:** YES
- **Internal BIS ID:** `8074`
- **`BIS_SearchStandard.aspx` Retrieved:** YES
- **HTTP Status:** 200
- **Extracted Metadata:** Title ("Household frost-free refrigerating appliances..."), Committee ("MED 3"), Status ("withdrawn"), Reaffirmed Year ("2022").
- **Source SHA-256:** `752923519d8b9d4780fe359e0eb69c922b7323054fae8e993f4c769f5f21c681`
- **Acquisition Status:** `SUCCESS`
- **Source URL:** `https://standardsbis.bsbedge.com/BIS_SearchStandard.aspx?Standard_Number=IS+15750&id=8074`

## 6. Provenance Validation
Every successful record retained:
- `source_id`: "SRC-002"
- `exact source URL`: `https://standardsbis.bsbedge.com/`
- `resolver URL`: `https://standardsbis.bsbedge.com/popupextender.aspx/GetStdNo_Bis`
- `metadata URL`: The precise lookup URL for the standard.
- `retrieval timestamp`: UTC ISO format.
- `HTTP status`: 200
- `SHA-256`: Hash of the authoritative HTML content.

## 7. Idempotency / Hash Behavior
The script successfully implements content-hash tracking in the manifest. Although this was a first-run (0 unchanged records), the architecture prevents silent overwriting or duplicate generation for existing content.

## 8. Regression Verification
The following Phase 6 artifacts were verified pre- and post-acquisition via SHA-256 hashing.
**Result: REGRESSION CHECK PASSED**
- `Phase 6 Chroma` -> UNCHANGED (`68d2942b`)
- `Phase 6 BM25` -> UNCHANGED (`7367e658`)
- `candidate_documents.json` -> UNCHANGED (`ceea4adc`)
- `acquisition_manifest.json` -> UNCHANGED (`8071ac85`)

## 9. Remaining Gaps
The 761 resolution failures indicate a severe data quality issue in the raw Phase 8.6 Scheme Data. The string values listed as "Standard Number" in the compulsory scheme tables are highly irregular. A future phase is required to parse, sanitize, and extract the actual IS numbers from these verbose strings (e.g. `10322 (Part 5/Sec 1)` -> `IS 10322 (Part 5/Sec 1)`) before resolution against the authoritative catalogue can succeed for the entire set.
