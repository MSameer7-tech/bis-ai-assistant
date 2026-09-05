# Phase 9.3: SIT / Scheme of Inspection and Testing Acquisition Plan

## 1. Objective and Scope
**Objective:** Acquire authoritative BIS SIT / Product Manual documents and extract explicit testing requirements deterministically, maintaining strict alignment with Phase 6, Phase 8.11, Phase 8.12, Phase 8.13, and Phase 8.14 immutable artifacts.
**Domain:** Scheme of Inspection and Testing (SIT) / Product Specific Guidelines (PSG) / Product Manuals.
**Source Family:** SRCF-004 (SIT)

## 2. Discovery and Source Architecture
### Authoritative BIS Source Discovery
Do not assume the Product Manual Directory is the only authoritative mechanism. All authoritative BIS SIT mechanisms must be investigated:
- Product Manual directory
- Scheme-I, Scheme-II, Scheme-IV
- FMCS / product-specific guidelines
- SIT-specific catalogs/directories if present
- Other official BIS certification catalogs/pages exposing SIT/Product Manual documents

For each source, the discovery phase will determine:
- Which source is authoritative
- Whether sources duplicate one another
- Which source provides completeness
- Pagination / AJAX / API behavior
- Source update behavior
- WAF / session behavior

*Note: Exhaustive coverage will only be claimed if the authoritative discovery mechanism explicitly supports that claim.*

## 3. SIT Identity Model
### Identity Hierarchy
1. Explicit BIS Product Manual/SIT document identity (e.g., `Doc: PM/IS XXXXX/YYYY` preserved exactly).
2. Explicit revision/version/date from the document.
3. Deterministic candidate identity (`SIT-CANDIDATE-{SHA256_PREFIX}`) marked as `identity_status = IDENTITY_UNRESOLVED` if authoritative version identity is unavailable.

**Crucial:** Do NOT automatically treat "same IS + different SHA" as a new SIT revision. A SHA change initially means `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`. Do not invent a revision from a SHA hash.

### Product Manual Content Domains
A Product Manual is not automatically classified entirely as normative SIT. Classify document/content domains separately, preserving `document_type = PRODUCT_MANUAL`.
At minimum, support classification for:
- SIT / testing requirements
- Sampling guidelines
- Grouping guidelines
- Levels of control
- Certification requirements
- Inspection requirements
- Product-specific guidance
- Other supporting content

### Test Requirement Identity
REQ identity must not rely only on a parameter hash. It must include enough deterministic context to distinguish repeated parameters:
- `SIT identity` + `table/clause context` + `normalized parameter/method`
Do not collapse distinct requirements merely because they share a parameter name.

### Explicit QCO / Standard / SIT Linkage
Where authoritative sources explicitly support the relationship, preserve the chain:
`QCO -> IS -> Product Manual / SIT -> Testing Requirements`
- Valid evidence includes: explicit IS number in Product Manual, explicit QCO reference, explicit BIS scheme relationship, explicit product scope.
- Do not infer relationships from semantic similarity.
- If sources disagree, mark as `CONFLICTING_EVIDENCE` and do not silently reconcile.

## 4. Deterministic PDF Extraction
Only deterministic extraction via `pypdf`/`pdfplumber` will be used. **No LLM extraction.**
Preserve the raw extracted table structure BEFORE normalization.
**Model:**
`PDF -> page -> table -> row -> raw cells -> normalized cells -> provenance`

For every extracted requirement, preserve (where available):
- `raw_test_parameter`, `normalized_test_parameter`
- `raw_test_method`, `normalized_test_method`
- `raw_sampling`, `normalized_sampling`
- `raw_frequency`, `normalized_frequency`
- `raw_acceptance_criterion`, `normalized_acceptance_criterion`
- `clause`, `table`, `page`

Handle merged cells, continuation rows, repeated cells, multi-line test parameters/methods, and table headers repeated across pages. Do not destroy original cell values during normalization.

### Scanned PDF Policy
- **No OCR:** If PDF text/table extraction is impossible (scanned), classify as `EXTRACTION_FAILED`.
- If partial extraction is possible but validation fails, classify as `MANUAL_REVIEW`.
- Do not fabricate fields. Preserve in a recovery queue for a possible future OCR recovery phase.

## 5. Storage Architecture and SHA State Machine
No parallel storage architecture will be created. We will strictly use existing directories:
`data/candidates/`, `data/raw/immutable/`, `data/acquisition/manifests/`, `data/catalog/`, `docs/phase9/`, `tests/phase9/`

Outputs are strictly acquisition/catalog artifacts. Do NOT modify Phase 6, Phase 8.11, 8.12, 8.13, 8.14 layers or integrate SIT into RAG.

### The Four-Way SHA State Machine
- `SAME ID + SAME SHA` -> `UNCHANGED`
- `SAME ID + DIFFERENT SHA` -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`
- `DIFFERENT ID + SAME SHA` -> `DUPLICATE_REPRESENTATION_ALIAS`
- `DIFFERENT ID + DIFFERENT SHA` -> `DISTINCT_DOCUMENT`

### Terminal Failure States
Must explicitly support and never silently discard:
`ACQUIRED`, `UNCHANGED`, `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`, `DUPLICATE_REPRESENTATION_ALIAS`, `DISTINCT_DOCUMENT`, `FETCH_FAILED`, `HTTP_ERROR`, `WAF_BLOCKED`, `SESSION_REQUIRED`, `ACCESS_RESTRICTED`, `IDENTITY_UNRESOLVED`, `EXTRACTION_FAILED`, `MANUAL_REVIEW`, `AMBIGUOUS`, `CONFLICTING_EVIDENCE`.

## 6. Provenance
Every testing requirement must preserve provenance. At minimum:
`source_url`, `final_url`, `source_sha256`, `document_id`, `page_number`, `table_index`, `row_index`, `clause_reference`, `retrieved_at`, `extraction_method`.
(If a value spans multiple pages, preserve all applicable page references.)

## 7. Coverage Metrics
Report separately for documents/discovery:
- source mechanisms discovered, candidates discovered
- unique SIT/Product Manual documents, unique IS numbers, acquired documents
- unchanged, changed/review, duplicates
- fetch failures, WAF/session failures, identity unresolved, extraction failures, manual review, ambiguous, conflicting evidence

Report for extracted testing semantics:
- testing requirements extracted, unique test parameters, unique test methods
- requirements with sampling, frequency, acceptance criteria, clause/table/page provenance
- provenance completeness percentage
- explicit IS -> SIT relationships, explicit QCO -> IS -> SIT chains
- content-domain classification

## 8. Tests
Deterministic tests will be written in `tests/phase9/` covering:
1. Product Manual discovery
2. SIT candidate discovery
3. identity extraction
4. identity-unresolved fallback
5. same ID + same SHA
6. same ID + different SHA
7. duplicate SHA
8. raw table preservation
9. merged-cell handling
10. continuation-row handling
11. test parameter extraction
12. test method extraction
13. sampling extraction
14. frequency extraction
15. acceptance criterion extraction
16. clause/table/page provenance
17. multiple requirements with same parameter name
18. QCO/IS/SIT explicit relationship
19. conflicting evidence
20. scanned PDF extraction failure
21. immutable raw preservation
22. incremental rerun
23. hardcoding audit

## 9. Execution Order
Execution will proceed sequentially ONLY after this plan is approved:
A. Source mechanism investigation
B. Authoritative SIT discovery
C. Candidate manifest generation
D. Identity normalization
E. Acquisition
F. SHA/version classification
G. deterministic PDF extraction
H. content-domain classification
I. SIT requirement extraction
J. QCO/IS/SIT relationship extraction where explicitly supported
K. provenance validation
L. incremental update validation
M. tests
N. frozen-layer regression
O. hardcoding audit
P. final report (`docs/phase9/phase9.3_sit_testing_acquisition_report.md`)

*Note: Execution will STOP after Phase 9.3. Phase 9.4 will not be started.*
