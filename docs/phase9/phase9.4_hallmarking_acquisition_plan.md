# Phase 9.4: Hallmarking Knowledge Acquisition Plan

## 1. Objective
**Objective:** Acquire authoritative BIS Hallmarking knowledge and preserve it as deterministic acquisition/catalog artifacts. The phase must explicitly cover the six existing Hallmarking subdomains:
- **009A:** Hallmarking standards
- **009B:** Hallmarking regulations
- **009C:** Mandatory hallmarking orders/notifications
- **009D:** HUID and consumer verification
- **009E:** Assaying and Hallmarking Centres
- **009F:** Jeweller/refinery registrations

*Note: Exhaustive coverage will not be claimed unless the authoritative BIS discovery mechanism explicitly establishes completeness.*

## 2. Authoritative Source Discovery
All relevant official BIS mechanisms will be investigated:
- BIS Hallmarking overview and regulations
- BIS Hallmarking orders/notifications
- BIS Manakonline Hallmarking services
- BIS HUID / consumer verification services
- BIS Assaying & Hallmarking Centre information
- BIS jeweller and refinery registration information
- Official BIS publications/guides relating to hallmarking
- Official BIS pages exposing downloadable hallmarking documents
- Official BIS/LIMS information where relevant to hallmarking centres

Discovery will check HTML, PDF, JSON/API, registry/search endpoints, tables, AJAX, WebForms, and session-gated/WAF-protected portals. 
For every source, we will document: `URL, source family, authority level, content type, discovery method, access behavior, pagination, AJAX/API behavior, WAF/session behavior, completeness characteristics, update behavior`.

## 3. Hallmarking Domain Classification
Every discovered document/record must receive an explicit domain classification from the following list:
- `HALLMARKING_STANDARD`
- `HALLMARKING_REGULATION`
- `MANDATORY_HALLMARKING_ORDER`
- `HUID_CONSUMER_VERIFICATION`
- `ASSAYING_HALLMARKING_CENTRE`
- `JEWELLER_REGISTRATION`
- `REFINERY_REGISTRATION`
- `HALLMARKING_GUIDANCE`
- `OTHER_SUPPORTING_CONTENT`

*Generic BIS navigation or unrelated material will not be classified as Hallmarking knowledge.*

## 4. Identity Model
Reusing the existing identity architecture. Identity priority:
1. Explicit authoritative BIS document/record identity
2. Explicit regulation/order/notification number
3. Explicit registration/certificate identifier
4. Explicit standard number and edition/year
5. Deterministic candidate identity (`HALLMARK-CANDIDATE-{SHA256_PREFIX}`) only when authoritative identity cannot be established.

If identity cannot be established, state is `IDENTITY_UNRESOLVED`. A SHA-256 hash is byte identity only and will NOT be treated as an authoritative revision identifier.

## 5. SHA State Machine
Strict adherence to the four-way state machine:
- `SAME ID + SAME SHA` -> `UNCHANGED`
- `SAME ID + DIFFERENT SHA` -> `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`
- `DIFFERENT ID + SAME SHA` -> `DUPLICATE_REPRESENTATION_ALIAS`
- `DIFFERENT ID + DIFFERENT SHA` -> `DISTINCT_DOCUMENT`

*Immutable raw artifacts will never be overwritten.*

## 6. Hallmarking Structured Data
Deterministic schemas will be enforced per domain:
- **Standards:** `standard_number, part/section, edition_year, title, status/lifecycle, provenance`
- **Regulations/Orders:** `identity, title, issuing_authority, notification/order_number, issue_date, effective_date, referenced_standards, amendments/revisions, lifecycle, provenance`
- **HUID:** `service_name, verification_workflow, required_inputs, verification_result_fields, official_conditions/instructions, source/version, provenance`
- **Centres:** `centre_identity, centre_name, location, status, scope/services, applicable_standards, effective/update_date, source_url, source_sha, provenance`
- **Jeweller Registrations:** `registration_identity, entity_name, location, registration/status, effective/update_information, provenance`
- **Refinery Registrations:** `registration_identity, entity_name, location, status, effective/update_information, applicable_scope, provenance`

## 7. Relationships
Capture ONLY explicitly supported relationships (e.g., `STANDARD -> REGULATION -> MANDATORY ORDER -> APPLICABLE SCOPE` or `HUID -> VERIFICATION SERVICE`). 
No inferences will be made based on names, locations, or semantic similarity. Conflicting evidence between sources triggers `CONFLICTING_EVIDENCE` without silent reconciliation.

## 8. Product/Scope Handling
Explicit hallmarking applicability (product category, material, fineness, article type, geographical applicability, effective date, exemption, scope condition) will be preserved as structured fields exactly as supported by authoritative sources.

## 9. PDF / HTML Extraction
Use deterministic extraction only (`pypdf`, `pdfplumber`, HTML DOM parsing, structured JSON/API parsing). **No LLM extraction.**
- **PDFs:** Preserve `PDF -> page -> table/section -> raw values -> normalized values -> provenance`
- **Tables:** Preserve `table_index, row_index, raw_cells, normalized_cells, page, clause/section`
- **HTML:** Preserve `source_url, final_url, DOM evidence, table/index/row, retrieval_timestamp, source_sha`

## 10. Scanned Document Policy
No OCR in Phase 9.4. Scanned/unparsable documents are marked `EXTRACTION_FAILED`. Partial extraction failing validation is marked `MANUAL_REVIEW`. Content will never be fabricated and documents will be placed in a recovery queue.

## 11. Access Failure States
Explicit terminal states supported:
`ACQUIRED, UNCHANGED, CONTENT_CHANGED_REQUIRES_VERSION_REVIEW, DUPLICATE_REPRESENTATION_ALIAS, DISTINCT_DOCUMENT, FETCH_FAILED, HTTP_ERROR, WAF_BLOCKED, SESSION_REQUIRED, ACCESS_RESTRICTED, IDENTITY_UNRESOLVED, EXTRACTION_FAILED, MANUAL_REVIEW, AMBIGUOUS, CONFLICTING_EVIDENCE`.
Candidates will never be silently discarded.

## 12. Provenance
Minimum provenance fields: `source_url, final_url, source_sha256, document/record identity, retrieved_at, acquisition_method, extraction_method`.
- Documents: `page_number, table_index, row_index, clause/section`
- Registries: `registry endpoint/page, record_identifier, query_parameters, retrieval_timestamp`

## 13. Immutable Storage
Existing architecture is strictly reused: `data/candidates/`, `data/raw/immutable/`, `data/acquisition/manifests/`, `data/catalog/`, `docs/phase9/`, `tests/phase9/`.
Artifacts are NOT to be consumed by RAG or Phase 8.11 until future integration.

## 14. Incremental Update Model
Candidate-level incremental updates: Unchanged remain unchanged, changed bytes do not overwrite old raw files, duplicate representations are linked, new versions get new identities only if supported by authoritative metadata, unresolved remain unresolved, disappeared records are marked according to lifecycle semantics (no silent deletion).

## 15. Coverage Metrics
Final report will separate:
- **Discovery:** Source mechanisms, candidates, unique documents/records, standards, regulations/orders, HUID workflows, centres, jeweller/refinery registrations.
- **Acquisition:** Acquired, unchanged, changed, aliases, fetch failures, WAF/session, unresolved identities.
- **Extraction:** Success/failures, manual review, ambiguous, conflicts.
- **Structured Semantics:** Extracted standards, regulations, orders, HUIDs, centres, registrations, explicit relationships, provenance completeness percentage.

## 16. Tests
25 deterministic tests will be written in `tests/phase9/` covering source discovery, domain classification, identity extraction across domains, 4-way SHA states, deterministic extraction (PDF/HTML), HUID/centre/registration structures, relationship tracking, scanned PDF failures, immutable storage, incremental reruns, and hardcoding audits.

## 17. Safety Against Hardcoding
No specific hallmarking product mappings, standard numbers, centre/jeweller names, registration numbers, or HUID results will be hardcoded. Production code will strictly derive from authoritative sources.

## 18. Frozen-Layer Protection
Fingerprints for Phase 6 Chroma, BM25, corpus, Phase 8.11, 8.12, 8.13, and 8.14 artifacts will be preserved and verified for immutability before and after execution.

## 19. Execution Order
Execution will proceed sequentially ONLY after this PLAN ONLY is approved:
A. Source mechanism investigation
B. Authoritative Hallmarking discovery
C. Candidate generation
D. Identity normalization
E. Acquisition
F. SHA classification
G. Deterministic extraction
H. Domain classification
I. Structured record extraction
J. Explicit relationship extraction
K. Provenance validation
L. Incremental rerun validation
M. Tests
N. Frozen-layer regression
O. Hardcoding audit
P. Final report (`docs/phase9/phase9.4_hallmarking_acquisition_report.md`)
*(Execution STOPS after Phase 9.4)*
