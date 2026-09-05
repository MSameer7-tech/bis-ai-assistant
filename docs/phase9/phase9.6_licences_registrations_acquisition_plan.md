# Phase 9.6: Licences / Registrations Knowledge Acquisition Plan

## 1. Objective
Build a deterministic acquisition plan for authoritative BIS licence and registration knowledge. The system must distinctly separate:
1. BIS Product Certification licences
2. BIS licence search records
3. BIS registration records
4. BIS CRS manufacturer registrations
5. Hallmarking-related registrations (where explicitly relevant)
6. Other BIS registrations explicitly supported by authoritative BIS sources

*Licenses and registrations must not be collapsed into one entity. Licence holding will NOT be inferred from third-party directories, product pages, search engine results, or laboratory listings.*

## 2. Authoritative Source Discovery
Prior to execution, all authoritative BIS mechanisms will be investigated, including:
- BIS Manakonline Licence Search
- BIS Product Certification licence directory/search
- BIS CRS Registered Manufacturers Registry
- BIS CRS portal records (where publicly accessible)
- BIS Hallmarking registration mechanisms
- BIS licence/registration verification pages
- BIS product certification public registries
- Official downloadable BIS licence/registration documents
- Scheme/product-specific registration lists

For each mechanism, document: `authority, source URL, source family, content type (HTML/PDF/JSON/API/registry), search mechanism, pagination, AJAX/DataTables, WebForms, dynamic endpoints, session requirements, WAF/anti-bot behavior, authentication requirements, public/private fields, update mechanism, and completeness characteristics`.

## 3. Entity Model
Separate, deterministic models for:
**A. LICENCE**
`licence_id, licence_number, licence_type, status, holder_name, manufacturer_name, product, standard_number, standard_part, scheme, certification_scope, issue_date, valid_from, valid_until, cancellation/suspension_date, source_url, final_url, source_sha256, retrieved_at, acquisition_method, extraction_method, provenance, lifecycle_status`

**B. REGISTRATION (Generic BIS)**
`registration_id, registration_number, entity_name, scheme, status, validity_dates, source_provenance`

**C. CRS MANUFACTURER REGISTRATION**
`registration_id, manufacturer_name, brand, product_category, applicable_standard, registration_status, registration_date, validity_dates, official_identifier, source_provenance`

**D. HALLMARKING REGISTRATION**
Distinctions between `jeweller registration`, `refinery registration`, and `assaying centre records` must be preserved. Do not duplicate/silently merge Phase 9.4 entities.

## 4. Privacy / Data Minimization
Unnecessary personal data collection is prohibited. 
Do not collect: personal phone numbers, personal email addresses, personal names (unless representing the official organization), or residential addresses. Rely exclusively on organization-level information required for BIS compliance.

## 5. Licence VS Registration Semantics
- **LICENCE:** Authorization under BIS product certification.
- **REGISTRATION:** Registration under a specific BIS scheme.
- **CRS REGISTRATION:** Under the BIS Compulsory Registration Scheme.
- **HALLMARKING REGISTRATION:** Applicable to jewellers/refineries.
*Equivalence will not be inferred. A registered manufacturer is not automatically "licensed".*

## 6. Identity Model
Hierarchies must remain deterministic:
**Licences:** 
1) Explicit BIS licence number -> 2) Official record ID -> 3) Deterministic source ID -> 4) `LIC-CANDIDATE-{SHA256}`
**CRS:** 
1) CRS registration number -> 2) BIS registration ID -> 3) Deterministic source identity
**Organizations:** Multiple licences/products may belong to one manufacturer. Organization name alone is NOT an authoritative identity.
*Ambiguous identity -> `AMBIGUOUS`. Unresolvable -> `IDENTITY_UNRESOLVED`.*

## 7. SHA State Machine
- `SAME ID + SAME SHA` -> `UNCHANGED`
- `SAME ID + DIFFERENT SHA` -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`
- `DIFFERENT ID + SAME SHA` -> `DUPLICATE_REPRESENTATION_ALIAS`
- `DIFFERENT ID + DIFFERENT SHA` -> `DISTINCT_DOCUMENT`

## 8. Relationship Model
Explicitly preserved relationships:
- `LICENCE` -> `HOLDER, MANUFACTURER, PRODUCT, STANDARD, PART, SCHEME, STATUS, VALIDITY, PROVENANCE`
- `CRS REGISTRATION` -> `MANUFACTURER, BRAND, PRODUCT, STANDARD, STATUS, PROVENANCE`
- `HALLMARKING REGISTRATION` -> `ENTITY, TYPE, LOCATION, STATUS, VALIDITY, PROVENANCE`
*Do NOT infer manufacturer->licence from manufacturer->product or product->licence from product->standard.*

## 9. Status / Lifecycle Model
Lifecycle states must be preserved as explicitly sourced: `ACTIVE, SUSPENDED, CANCELLED, EXPIRED, WITHDRAWN, REVOKED, SUPERSEDED, UNKNOWN`. Unknowns will not be normalized to Active. Historical status must be preserved without overwriting prior raw artifacts.

## 10. Search / Registry Acquisition
Acquisition must deterministically support public forms, registry tables, AJAX, DataTables, and PDFs. Inaccessible sources get explicit terminal states: `SESSION_REQUIRED`, `ACCESS_RESTRICTED`, `FETCH_FAILED`, `HTTP_ERROR`. Synthetic records will NOT be created to compensate for blocked sources.

## 11. PDF / Document Extraction
`pypdf`, `pdfplumber`, `PyMuPDF` will be utilized to deterministically extract `page -> table -> row -> normalized field -> entity`. Merged cells, continuation rows, and multi-line headers will be addressed without LLM inference or OCR. Unparseable -> `EXTRACTION_FAILED`.

## 12. Provenance
Every authoritative record requires: `source_url, final_url, source_sha256, retrieved_at, acquisition_method, extraction_method, entity_id, source_record_identifier, page/table/row/clause` (where applicable). API/Registry responses will include endpoint/request hashes.

## 13. Incremental Updates
Candidate reruns enforce immutability: unchanged -> `UNCHANGED`, content changed -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`, different representation -> `ALIAS`, distinct entity -> `DISTINCT_DOCUMENT`. Historical raw artifacts are preserved.

## 14. Discovery Completeness
Each registry source will be classified by completeness (e.g., full catalog, query-only, paginated search, session-gated). Exhaustive claims will be avoided unless the authoritative source supports it.

## 15. Mock / Test Data Policy
Mock endpoints and payloads will be rigidly isolated under `tests/fixtures/phase9_6/`. Synthetic records MUST NOT contribute to authoritative counts. Execution reports will distinctly separate `AUTHORITATIVE PRODUCTION ACQUISITION` from `TEST/MOCK VALIDATION ARTIFACTS`.

## 16. Storage
- `data/candidates/phase9_6_licence_registration_candidates.json`
- `data/catalog/phase9_6_licence_registration_catalog.json`
- `data/raw/immutable/licences_registrations/`
- `data/acquisition/manifests/phase9_6_licence_registration_manifest.json`

## 17. Failure States
Mandatory terminal states for all candidates: `ACQUIRED, UNCHANGED, CONTENT_CHANGED_REQUIRES_VERSION_REVIEW, DUPLICATE_REPRESENTATION_ALIAS, DISTINCT_DOCUMENT, FETCH_FAILED, HTTP_ERROR, WAF_BLOCKED, SESSION_REQUIRED, ACCESS_RESTRICTED, IDENTITY_UNRESOLVED, EXTRACTION_FAILED, MANUAL_REVIEW, AMBIGUOUS, CONFLICTING_EVIDENCE`.

## 18. Coverage Metrics
Metrics explicitly separate authoritative vs mock: candidate totals, unique licences, registrations, CRS vs Hallmarking, lifecycle statuses, standards/products mapped, manufacturers/organizations, access failure categories, extraction failures, duplicate aliases, provenance completeness, and completeness classification.

## 19. Hard-Coding Prohibition
Production paths will contain ZERO hardcoded licence numbers, registration IDs, organization identities, or product mappings. A dedicated hardcoding audit script will run.

## 20. Frozen-Layer Protection
No modifications will be made to Phase 6 Chroma, BM25, embeddings, corpus, or Phase 8.11-8.14 retrieval/evaluation indices.

## 21. Test Plan
28 deterministic tests covering: discovery/validation, classification semantics, identity resolution, multiple-licence-to-manufacturer mappings, standard mappings, duplicate representations, SHA logic, historical status tracking, registry/API JSON extraction, PDF/DataTable processing, provenance preservation, WAF handling, mock-data isolation, privacy enforcement, and frozen-layer regression.

## 22. Execution Sequence
A. Source discovery
B. Source validation
C. Registry/search mechanism analysis
D. Candidate discovery
E. Entity classification
F. Identity resolution
G. Raw acquisition
H. SHA validation
I. Deterministic extraction
J. Relationship extraction
K. Status/lifecycle reconciliation
L. Provenance validation
M. Deduplication
N. Coverage audit
O. Privacy/data-minimization audit
P. Tests
Q. Hardcoding audit
R. Frozen-layer regression
S. Final report
*(STOP AFTER PHASE 9.6)*

## 23. Final Acceptance Criteria
- Explicit semantic distinction between Licence and Registration entities.
- No mock/synthetic data mixed into production counts.
- Strict data minimization enforcement (no unnecessary personal details).
- Accurate 4-way SHA immutability execution.
- Deterministic identity resolution and historical lifecycle preservation.
- Frozen layers remaining entirely untouched.
- Clean hardcoding audit and 28 passed tests.
