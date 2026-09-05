# Phase 9.5: Laboratories / Testing Laboratory Knowledge Acquisition Plan

## 1. Objective
Build a deterministic acquisition plan for authoritative BIS laboratory knowledge required by the SIH BIS Assistant. The system must distinctly capture:
1. BIS-owned laboratories
2. BIS-recognized testing laboratories
3. BIS-empanelled laboratories (where authoritative BIS source exists)
4. NABL-accredited laboratories (only where relevant to BIS testing/certification workflows)
5. Other officially recognized laboratory categories (only where authoritative BIS evidence establishes relevance)

*Do NOT assume any laboratory listed on a third-party website is BIS-recognized. Do NOT infer recognition from names, addresses, or search-engine results.*

## 2. Authoritative Source Discovery
Investigate and document all relevant official BIS mechanisms before execution, including:
- BIS Central / Regional Laboratories directory
- BIS Recognized Testing Laboratories directory/register
- BIS LIMS laboratory pages (e.g., `https://lims.bis.gov.in/home/bis_labs/`, `https://lims.bis.gov.in/home/labs/`)
- BIS Product Certification laboratory information
- BIS scheme/product-specific laboratory information
- BIS laboratory recognition/scope documents (PDFs)
- BIS testing laboratory search/filter mechanisms
- BIS-recognized lists embedded in official documents
- NABL sources (only where explicitly required to establish a BIS-relevant relationship)

For every mechanism, determine: `authority, source URL, source family, content type (HTML/PDF/JSON/API/registry), pagination, AJAX/DataTables, WebForms, session requirements, WAF/anti-bot behavior, dynamic endpoint behavior, update mechanism, completeness characteristics`, and the specific fields available. (Browser blocks circumvented via normal HTTP must be accurately documented, not deemed "bypassing WAF").

## 3. Laboratory Record Model
Structured record schema:
- `laboratory_id`
- `laboratory_name`
- `laboratory_category`
- `ownership_type`
- `recognition_status`
- `accreditation_status`
- `BIS_recognition_number` (if explicitly available)
- `NABL_accreditation_number` (if explicitly available)
- `address`, `city`, `state`
- `contact_information` (only where appropriately/officially published)
- `scope_document_reference` & `scope_document_url`
- `standards_supported`
- `product_categories`
- `test_methods`, `test_parameters`
- `validity_start`, `validity_end`
- `current_status`
- `source_url`, `final_url`, `source_sha256`, `retrieved_at`
- `acquisition_method`, `extraction_method`, `provenance`, `lifecycle_status`

## 4. Laboratory Category Rules
Do NOT collapse all laboratories into a single generic category. Preserve explicit distinctions: `BIS-owned`, `BIS-recognized`, `BIS-empanelled`, `NABL-accredited`, `Other officially recognized`.
If a laboratory appears in multiple authoritative sources, preserve relationships rather than creating contradictory duplicates. If recognition status cannot be established, classify as unresolved rather than inferred.

## 5. Scope Model
Where authoritative scope information exists, strictly preserve:
`Laboratory -> Scope Document -> Standard -> Part/Section -> Product -> Test Method -> Test Parameter -> Status/Validity -> Provenance`
Do not infer testing capability simply because a name appears in a product-related document. Do not infer standard coverage from name similarity. Create `laboratory -> standard/product/test` relationships **only** when supported by authoritative evidence.

## 6. Discovery and Acquisition
Define deterministic discovery for: HTML directories, searchable registries, AJAX/DataTables, JSON responses, PDF scopes, downloadable documents, and BIS LIMS records.
Preserve raw artifacts immutably (no overwriting existing raw content). Use existing architecture. Process includes candidate discovery, validation, acquisition, hashing, identity, deduplication, provenance, lifecycle, incremental update detection, and failure handling.

## 7. Identity Model
Do not invent IDs based on names. Identity hierarchy:
1. Explicit BIS laboratory/recognition identifier
2. Explicit BIS LIMS identifier
3. Explicit NABL identifier (where applicable)
4. Deterministic normalized identity from authoritative fields
5. Candidate SHA identity (`LAB-CANDIDATE-{SHA256}`) only when authoritative identity cannot be established.

If records represent the same lab through different official representations: `DUPLICATE_REPRESENTATION_ALIAS`. Ambiguous identities must become `AMBIGUOUS`. No silent merging.

## 8. Existing SHA State Machine
- `SAME ID + SAME SHA` -> `UNCHANGED`
- `SAME ID + DIFFERENT SHA` -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`
- `DIFFERENT ID + SAME SHA` -> `DUPLICATE_REPRESENTATION_ALIAS`
- `DIFFERENT ID + DIFFERENT SHA` -> `DISTINCT_DOCUMENT`

## 9. Scope Document Extraction
Use deterministic extraction (`pypdf`, `pdfplumber`, `PyMuPDF`) for PDFs. Preserve:
`PDF -> page -> table -> row -> raw cells -> normalized cells -> scope relationship -> provenance`
Handle merged cells, repeated headers, continuation rows, multi-line standards, multi-page tables, and part/section references.
**No LLM Extraction. No OCR.** 
Scanned/unparsable -> `EXTRACTION_FAILED`. Partially reliable -> `MANUAL_REVIEW`. Preserve the recovery queue.

## 10. Provenance
Minimum provenance fields:
`source_url`, `final_url`, `source_sha256`, `retrieved_at`, `acquisition_method`, `extraction_method`, `laboratory_id`, `document_id` (where applicable), `page_number`, `table_index`, `row_index`, `clause/reference`, `source_record_identifier`.
*Records without authoritative provenance are invalid.*

## 11. Relationship Model
Explicit relationships only:
`LABORATORY -> SCOPE_DOCUMENT`, `LABORATORY -> STANDARD`, `LABORATORY -> PRODUCT`, `LABORATORY -> TEST_METHOD`, `LABORATORY -> TEST_PARAMETER`, `STANDARD -> LABORATORY`.
Do not infer `LABORATORY -> PRODUCT` from `LABORATORY -> STANDARD` unless explicitly linked by an authoritative source. Conflicting authoritative evidence maps to `CONFLICTING_EVIDENCE`.

## 12. Failure States
All candidates must reach a terminal state (No silent drops):
`ACQUIRED, UNCHANGED, CONTENT_CHANGED_REQUIRES_VERSION_REVIEW, DUPLICATE_REPRESENTATION_ALIAS, DISTINCT_DOCUMENT, FETCH_FAILED, HTTP_ERROR, WAF_BLOCKED, SESSION_REQUIRED, ACCESS_RESTRICTED, IDENTITY_UNRESOLVED, EXTRACTION_FAILED, MANUAL_REVIEW, AMBIGUOUS, CONFLICTING_EVIDENCE`

## 13. Storage
Reuse existing architecture. 
- `data/candidates/phase9_5_laboratory_candidates.json`
- `data/catalog/phase9_5_laboratory_catalog.json`
- `data/raw/immutable/laboratories/`
- `data/acquisition/manifests/phase9_5_laboratory_manifest.json`

**Mock/test fixtures MUST be isolated under `tests/fixtures/phase9_5/`. Never count mock data as authoritative.**

## 14. Incremental Updates
Candidate-level incremental behavior:
- Unchanged laboratory/document -> `UNCHANGED`
- Changed bytes under same identity -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`
- Same bytes under different representation -> `DUPLICATE_REPRESENTATION_ALIAS`
- Genuinely distinct record -> `DISTINCT_DOCUMENT`

## 15. Coverage Metrics
Report must measure: source mechanisms (authoritative vs mock), candidate laboratories, unique laboratories, labs by category (BIS-owned, BIS-recognized, empanelled, NABL, other), state counts (acquired, unchanged, changed, alias, distinct), access failures (fetch, WAF, session, restricted), extraction failures (manual, ambiguous, conflict), unique scope docs, standards covered, products covered, test methods/parameters, relationships mapped, and scope provenance completeness.

## 16. Mock / Test Data Policy
All mock endpoints, registries, synthetic scopes, or fake payloads must be clearly separated.
Execution reports MUST contain separate sections:
- `AUTHORITATIVE PRODUCTION ACQUISITION`
- `TEST/MOCK VALIDATION ARTIFACTS`
Mock records will never contribute to authoritative metrics.

## 17. Hard-Coding Prohibition
Do not hardcode: laboratory names, IDs, addresses, standards, products, methods, or relationships. Test fixtures are allowed but must remain outside production paths. A production-vs-test hardcoding audit will be executed.

## 18. Frozen-Layer Protection
Phase 9.5 must not modify Phase 6 Chroma, BM25, corpus, or Phases 8.11–8.14 artifacts. Phase 9.5 outputs are strictly catalog data and will not integrate into RAG yet. Fingerprint verification will be strictly enforced.

## 19. Test Plan
26 deterministic tests covering: source discovery, source validation, category classifications (BIS-owned, recognized, empanelled, NABL), lab identity, duplicate representation, SHA state machine, scope extraction, multi-page tables, merged cells, continuation rows, part/section handling, relationships (standard/product), provenance, inaccessible sources, WAF/session handling, scanned PDF handling, extraction failure, ambiguity, conflicting evidence, mock-data isolation, hardcoding audit, and frozen-layer regression.

## 20. Execution Sequence
A. Source discovery
B. Source validation
C. Candidate discovery
D. Candidate normalization
E. Identity resolution
F. Raw acquisition
G. SHA validation
H. Scope extraction
I. Relationship extraction
J. Provenance validation
K. Deduplication
L. Coverage audit
M. Tests
N. Hardcoding audit
O. Frozen-layer regression
P. Final report
*(STOP AFTER PHASE 9.5. Do not start Phase 9.6)*

## 21. Final Acceptance Criteria
- Authoritative sources correctly identified.
- No mock data counted as production.
- Deterministic acquisition with immutable raw storage.
- Correct SHA state machine & deterministic identity handling.
- Scope provenance complete.
- Explicit relationships only; ambiguity/conflict preserved.
- Every candidate terminally classified (no silent drops).
- Hardcoding audit clean.
- Phase 6 regression clean; Phases 8.11–8.14 unchanged.
- Tests passing and coverage limitations explicitly reported.
