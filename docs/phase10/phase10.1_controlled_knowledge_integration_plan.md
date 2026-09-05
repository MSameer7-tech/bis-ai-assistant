# Phase 10.1: Controlled Knowledge Integration Architecture & Plan (Corrected)

## 1. Record-Level Integration Readiness
Phases 9.1, 9.2, and 9.3 are NOT uniformly ready. Integration eligibility is strictly at the record level.
- **Phase 9.1**: Eligible ONLY when authoritative source, valid identity, valid SHA, provenance complete, no unresolved content review, and no extraction/fetch failure. Explicitly excluded: `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`, `FETCH_FAILED`, `ACCESS_RESTRICTED`, `EXTRACTION_FAILED`, `IDENTITY_UNRESOLVED`, `AMBIGUOUS`.
- **Phase 9.2**: Eligible ONLY when authoritative QCO identity is validated, PDF successfully acquired and extracted, referenced standard identity resolved, no conflicting evidence, and provenance complete. Explicitly excluded: `IDENTITY_UNRESOLVED`, `CONFLICTING_EVIDENCE`, `EXTRACTION_FAILED`, `FETCH_FAILED`, `AMBIGUOUS_RELATIONSHIP`.
- **Phase 9.3**: Standard -> SIT integration eligible ONLY when SIT identity is authoritative, standard identity is authoritative, relationship is explicit, and provenance complete. Records relying on SHA-based fallback identities without authoritative resolution are excluded and marked `IDENTITY_REVIEW_REQUIRED`.

## 2. Exact SHA Semantics
The 4-way rules are strictly enforced and dictate integration eligibility:
- `same identity + same SHA` → `UNCHANGED` (Keep existing active evidence)
- `same identity + different SHA` → `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW` (Excluded from automated active integration until manually reviewed)
- `different identity + same SHA` → `DUPLICATE_REPRESENTATION_ALIAS` (Integrate alias pointer)
- `different identity + different SHA` → `DISTINCT_DOCUMENT` (New evidence integration)

## 3. Evidence Role Model
- **STANDARD_METADATA**: Authority: BIS Index. Allowed: Standard metadata. Prohibited: Technical parameters/normative text. Retrieval: Identity resolution.
- **PRODUCT_STANDARD_RELATIONSHIP**: Authority: BIS Index. Allowed: Explicit product linkage. Prohibited: Proving technical requirements. Retrieval: Bridging product to IS.
- **DOCUMENT_EVIDENCE**: Authority: Normative IS standard. Allowed: Technical text.
- **STATUTORY_EVIDENCE**: Authority: BIS Acts/Rules. Allowed: Statutory power, jurisdiction, penalties. Prohibited: Inferring technical testing. Retrieval: Legal questions.
- **QCO_EVIDENCE**: Authority: Gazette. Allowed: Mandatory status, effective dates. Prohibited: Product applicability not explicitly stated, testing methods. Retrieval: Mandatory certification queries.
- **SIT_EVIDENCE**: Authority: Product Manuals. Allowed: Tabular test methods, frequencies. Prohibited: Missing fields (no guessing). Retrieval: Technical testing questions.

## 4. Structured Data Must Not Masquerade
Structured data (`STANDARD_METADATA`, `PRODUCT_STANDARD_RELATIONSHIP`, QCO metadata, SIT structured rows) CANNOT replace authoritative document text when answering questions requiring normative proof. They only establish identity or relationship edges.

## 5. Query Routing (Claim-Driven)
- **A. "What is IS X?"** → `STANDARD_METADATA`
- **B. "Which standard applies to product X?"** → `PRODUCT_STANDARD_RELATIONSHIP` → `STANDARD_METADATA`
- **C. "Is product X mandatory under BIS?"** → `PRODUCT_STANDARD_RELATIONSHIP` → QCO metadata/evidence → lifecycle/effective-date validation
- **D. "When does the QCO become effective?"** → `QCO_EVIDENCE` → effective-date validation
- **E. "What tests are required for product X?"** → exact standard relationship → `SIT_EVIDENCE` → relevant standard/document evidence
- **F. "What is the sampling frequency?"** → `SIT_EVIDENCE` (ONLY if exact evidence exists)
- **G. "What does the BIS Act say about X?"** → `STATUTORY_EVIDENCE`
- **H. "What penalty applies?"** → authoritative statutory/regulatory evidence
- **I. Historical question** → lifecycle-aware historical evidence
- **J. Conflicting evidence** → conflict state / controlled abstention

## 6. Deterministic Relationship Chain
`PRODUCT` → `PRODUCT_STANDARD_RELATIONSHIP` → `STANDARD_METADATA` → `QCO relationship/evidence` → `SIT relationship/evidence`
*Only exact standard identity, explicit internal IDs, and explicitly published relationships are allowed.* LLM fuzzy matching, title similarity, and inferred applicability are strictly prohibited. Ambiguity yields controlled abstention.

## 7. QCO Version and Effective-Date Logic
QCOs track Notification, Publication, Effective, and Amendment dates. For current compliance questions, RAG must use evidence strictly applicable to the requested date. For conflicting QCOs or future effective dates, do NOT silently select one; expose the conflict or abstain.

## 8. SIT Version Alignment
SIT evidence must align perfectly with the standard number, part, section, and edition/year. If a SIT matches a different standard edition, it cannot be silently combined. Unresolvable identities trigger `IDENTITY_REVIEW_REQUIRED`. Multiple applying SITs trigger `AMBIGUOUS_MATCH`.

## 9. Acts / Rules / Regulations
Legal evidence supports only explicitly stated powers, obligations, and procedural provisions. If exact applicability is unclear, the system executes controlled abstention rather than hallucinating legal interpretations.

## 10. Provenance Contract
Every integrated record MUST retain: `source_url`, `final_url`, `source_sha256`, `document_identity`, `version/lifecycle`, `retrieved_at`, `extraction_method`, `page`, `clause`, `table_index`, `row_index`, and `relationship_id`. No provenance drop is permitted at any stage from raw to citation.

## 11. Allowed / Prohibited Claims
(Formally mapped in the JSON Integration Contract). Evidence is rigidly bound to allowable claim boundaries. Missing fields in SITs cannot be inferred. Acts cannot support technical testing.

## 12. Indexing Design
- **Structured Indexes**: `STANDARD_METADATA`, `PRODUCT_STANDARD_RELATIONSHIP`, validated QCO relationships, validated SIT structured rows.
- **Normative Document Retrieval (Chroma/BM25)**: Acts/Rules full text, QCO full text, SIT full text. (Only embedded where text retrieval provides value; not every structured row is embedded).

## 13. Incremental Indexing
- Unchanged → no update.
- New Document → validate → integrate.
- Same Identity + Changed SHA → Version review (do not auto-replace).
- Duplicate Representation → alias relationship.
- Distinct Identity → new evidence.
- Withdrawn/Superseded → Retain historical evidence but update active retrieval eligibility.

## 14. Release Gate (16-Point)
Record entry to production requires ALL checks to pass:
1) Authoritative source 2) Identity 3) SHA integrity 4) Schema 5) Provenance 6) Lifecycle 7) Relationship 8) Ambiguity 9) Conflict 10) Extraction 11) Retrieval relevance 12) Citation validity 13) Claim-role compatibility 14) Phase 8.13 regression 15) Phase 8.14 regression 16) Hardcoding audit. (Any failure = DO NOT RELEASE).

## 15. Missing Domains
Hallmarking, Laboratories, Licences/Registrations, Consumer/BIS Care, and FAQs/Guides/Booklets remain UNSUPPORTED. No fallback mappings. No mock data in production.

## 16. Immutability
Phase 10.1 modifies absolutely no indexes, RAG pipelines, or Phase 6-9 datasets. It produces only this plan, the contract JSON, and isolated unit tests.

## 17. Final Decision Review
1. **What is integration-ready at RECORD LEVEL:** Only fully verified Phase 9.1, 9.2, and 9.3 records passing the 16-point gate.
2. **What requires review:** `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW` items and `IDENTITY_REVIEW_REQUIRED` items.
3. **What is excluded:** Fetch/extraction failures, ambiguous records.
4. **What remains unsupported:** Domains 9.4 through 9.8.
5. **Exact evidence roles:** STATUTORY, QCO, SIT, STANDARD, PRODUCT_STANDARD, DOCUMENT.
6. **Exact routing:** Claim-driven (A through J).
7. **Exact relationship rules:** Strict identity equivalence; zero fuzzy inference.
8. **Exact lifecycle rules:** Date-gated and strictly version-tied.
9. **Exact version rules:** 4-way SHA machine.
10. **Exact release gates:** 16-point check.

**PHASE_10_1_STATUS = PASS**
*(DO NOT IMPLEMENT PHASE 10.2)*
