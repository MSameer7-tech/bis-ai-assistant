# Phase 5: Final EvidenceUnit Quality Audit

## PHASE_5_STATUS = PASS

The PASS gate requires:
- SHA provenance: PASS
- source_url provenance: PASS
- document coverage: PASS
- manual-review preservation: PASS
- EvidenceUnit identity/location integrity: PASS
- duplicate investigation: PASS
- short-unit investigation: PASS
- extraction failures explicitly accounted for: PASS

All primary integrity gates passed clean.

## CHECK 1: Cryptographic Provenance
- Total Units: 17167
- Units with Valid SHA: 17167
- Units with Invalid SHA: 0
- Units with Source URL: 17167
- Units missing Source URL: 0
- Units with Complete Provenance: 17167

## CHECK 2: Document Coverage
- Extraction Eligible Documents: 646
- Extraction Attempted: 646
- Extraction Success: 640
- Extraction Failed: 6
- Documents with Zero EvidenceUnits: 0

## CHECK 3: EvidenceUnit Quality
- Empty Units: 0
- Whitespace-only Units: 0
- Extremely Short Units (<10 chars): 4
- Duplicate Units: 3311
- Near-Duplicate Units: 3786
- Malformed Identifiers: 0
- Missing Location Metadata: 0
- Missing Document Identity: 0
- Missing Provenance: 0

## CHECK 4: Document Type Coverage
| Type | Eligible | Attempted | Success | Failed | EvidenceUnits | Zero-Unit Docs |
|---|---|---|---|---|---|---|
| AMENDMENT | 2 | 2 | 2 | 0 | 99 | 0 |
| CONSUMER_GUIDE | 6 | 6 | 2 | 4 | 25 | 0 |
| HALLMARKING_ORDER | 2 | 2 | 2 | 0 | 63 | 0 |
| PRODUCT_MANUAL | 636 | 636 | 634 | 2 | 16980 | 0 |

## CHECK 5: Source Family Coverage
| Family | Eligible | Attempted | Success | Failed | EvidenceUnits | Zero-Unit Docs |
|---|---|---|---|---|---|---|
| SRCF-001 | 1 | 1 | 1 | 0 | 4 | 0 |
| SRCF-004 | 639 | 639 | 637 | 2 | 17064 | 0 |
| SRCF-008 | 4 | 4 | 0 | 4 | 0 | 0 |
| SRCF-011 | 2 | 2 | 2 | 0 | 99 | 0 |

## CHECK 6: Extraction Failure Audit
Explicit accounting for the 6 terminal extraction failures:
| Document ID | Type | Source Family | Reason |
|---|---|---|---|
| SRC-013-28-7131116-HITECHLAB-HEALTHCARE-RESEARCH | CONSUMER_GUIDE | SRCF-008 | Extraction failed: Expecting value: line 2 column 1 (char 1) |
| SRC-013-43-8127706-BUREAU-VERITAS-CONSUMER-PRODU | CONSUMER_GUIDE | SRCF-008 | Extraction failed: Expecting value: line 2 column 1 (char 1) |
| SRC-013-423-8198324-EMC-EMI-TESTING-LAB-HLL-LIFE | CONSUMER_GUIDE | SRCF-008 | Extraction failed: Expecting value: line 2 column 1 (char 1) |
| SRC-013-99-7120616-ENVIROCARE-LABS-PVT-LTD-THANE | CONSUMER_GUIDE | SRCF-008 | Extraction failed: Expecting value: line 2 column 1 (char 1) |
| PM-SRC-006-230-IS-9020-2002-POWER-THRESHERS-SAFETY- | PRODUCT_MANUAL | SRCF-004 | EXTRACTION_FAILED: Empty or scanned PDF with no extractable text layer |
| PM-SRC-006-IS-14806-2021-AZOSPIRILLUM-INOCULANTS | PRODUCT_MANUAL | SRCF-004 | EXTRACTION_FAILED: Empty or scanned PDF with no extractable text layer |

## CHECK 7: Table/Clause/Definition Quality (Metadata Presence)
- Clause Metadata: 17167
- Section Metadata: 0
- Heading Metadata: 17167
- Table Metadata: 1720
- Definition Metadata: 18
- Page Metadata: 17167
- Requirement Language: 4037
- Cross-Reference Language: 809

## CHECK 8: Duplication
- Exact Duplicates: 3311
- Near Duplicates: 3786

## CHECK 9: Manual Review Preservation
- ACQUISITION_MANUAL_REVIEW: 229
- PRESERVED_IN_CORPUS_INVENTORY: 229
- DROPPED: 0
