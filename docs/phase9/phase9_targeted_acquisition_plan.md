# Phase 9: Targeted BIS Knowledge Acquisition Plan (Revised)

## 1. Objective
Acquire the missing authoritative BIS knowledge identified by Phase 8.14 (SIT, Laboratories, Hallmarking, QCO/Gazette, Licences, Consumer/BIS Care, Acts/Rules, FAQs) into the existing source architecture. This acquisition must be highly targeted, evidence-driven, provenance-preserving, version-aware, and built to support incremental updates.

**CRITICAL IMMUTABILITY CONSTRAINT:**
This phase strictly focuses on **discovery and acquisition into immutable raw storage**. It will NOT integrate documents into the frozen RAG layers. The following layers remain 100% frozen during Phase 9:
- Phase 6 Chroma
- Phase 6 BM25
- Phase 6 corpus fingerprint
- Phase 8.11 structured retrieval indexes
- Phase 8.12 IntegratedRetrievalOrchestrator
- Phase 8.13 E2E validation
- Phase 8.14 coverage audit

---

## 2. Storage Architecture
Phase 9 will strictly reuse and extend the exact existing storage architecture. No parallel namespaces (e.g., `data/phase9_acquisition/`) will be created.

Every acquired artifact must retain immutable raw bytes and complete provenance in:
- `data/candidates/`: Discovered URLs/endpoints and initial metadata before validation.
- `data/raw/immutable/`: Raw bytes (PDF/HTML/JSON) indexed deterministically by identity and SHA-256.
- `data/acquisition/manifests/`: Audit logs, terminal failure states, and run metrics.
- `data/catalog/`: Processed structured metadata datasets, updated post-reconciliation.
- `docs/phase9/`: Subphase reports and documentation.

---

## 3. Source Authority Model
We strictly enforce the defined authority classes without introducing third-party sources:
- **PRIMARY_NORMATIVE**: Legally binding standard specifications, statutory QCOs, Hallmarking Orders.
- **OFFICIAL_OPERATIONAL**: Official guidelines, Product Manuals, SITs, Lab Registers, Licence ledgers.
- **OFFICIAL_INFORMATIVE**: FAQs, portal booklets, consumer advisory.
- **STATUTORY_FRAMEWORK**: BIS Act, Rules, Regulations.

---

## 4. Phase Breakdown & Execution Order
Execution will be strictly sequential. **Each subphase must be independently audited and accepted before the next begins. Do NOT automatically chain all eight.**

Proposed order:
1. **9.1** Acts / Rules / Regulations
2. **9.2** QCO / Gazette
3. **9.3** Testing / SIT
4. **9.4** Hallmarking
5. **9.5** Laboratories
6. **9.6** Licences / Registrations
7. **9.7** Consumer / BIS Care
8. **9.8** FAQs / Guides / Booklets

For EVERY Phase 9 subphase, execution uses two explicit stages:
- **STAGE A: Source Discovery / Mechanism Investigation**
- **STAGE B: Acquisition**

---

### PHASE 9.1: ACTS / RULES / REGULATIONS (SRCF-012)
**STAGE A: Source Discovery**
- *Authoritative Source*: `bis.gov.in/the-bis-act-rules-regulations/` and Legislative Department.
- *Mechanism*: Investigate static HTML vs API; determine PDF extraction requirements, language options, WAF blocks.

**STAGE B: Acquisition**
- *Strategy*: HTTP GET of identified URLs.
- *Preserve*: Document title, Act/Rule/Regulation type, year, notification/amendment identity, publication date, effective date, amendment relationships, lifecycle, source URL, raw SHA-256, retrieval timestamp.
- *Distinction*: Explicitly distinguish BIS Act vs Rules vs Regulations vs Amendments. Do NOT treat as FAQs.

### PHASE 9.2: QCO / GAZETTE (SRCF-003)
**STAGE A: Source Discovery**
- *Authoritative Source*: e-Gazette and BIS Compulsory Certification Portal.
- *Mechanism*: Determine actual public discovery (search API, HTML lists). Identify if session or CAPTCHA required. If restricted, log controlled failure (`ACCESS_RESTRICTED`).

**STAGE B: Acquisition**
- *Strategy*: Deterministic PDF download based on candidate list.
- *Preserve*: QCO/order/notification number, issuing ministry/department, publication date, effective/enforcement date, referenced Indian Standard number(s), product/category, amendment/revision relationship, Gazette identifier, source publication, source URL, SHA-256, retrieved_at, lifecycle.
- *Relationship*: Represent QCO → IS relationships explicitly. Do NOT treat a QCO itself as an IS.

### PHASE 9.3: TESTING / SIT (SRCF-005)
**STAGE A: Source Discovery**
- *Authoritative Source*: BIS CMD Portal (`bis.gov.in/product-certification/scheme-of-inspection-and-testing/`).
- *Mechanism*: Analyze HTML tables/XHR for product/standard mappings to SIT documents. Determine duplicate representations.

**STAGE B: Acquisition**
- *Strategy*: Targeted PDF download of SIT schedules.
- *Preserve*: Parent Indian Standard, standard edition/year, SIT revision/version, product/category, test parameter, test method, sampling requirement, test frequency, acceptance criteria, clause, subclause, table, page, amendment references, source URL, raw SHA-256, lifecycle, retrieval timestamp.

### PHASE 9.4: HALLMARKING (SRCF-009)
**STAGE A: Source Discovery**
- *Authoritative Sources*: BIS Hallmarking Overview, Manakonline.
- *Mechanism*: Individually map discovery mechanisms for 6 distinct subdomains. Evaluate HTML parsing, JSON APIs, and potential session blocks.

**STAGE B: Acquisition**
- *Strategy*: Execute tailored extraction for all existing subdomains without collapsing them:
  - `009A`: Standards
  - `009B`: Regulations
  - `009C`: Mandatory Orders
  - `009D`: HUID / Consumer Verification (Preserve official workflow/instructions, do not infer rules).
  - `009E`: Assaying / Hallmarking Centres (Preserve authoritative centre identity, location, scope, status).
  - `009F`: Jeweller / Refinery Registrations.
- *Preserve*: Subdomain-specific structured fields, document identity, lifecycle, provenance.

### PHASE 9.5: LABORATORIES (SRCF-008)
**STAGE A: Source Discovery**
- *Authoritative Source*: BIS LPCD Directory (`bis.gov.in/laboratories/`).
- *Mechanism*: Analyze HTML/API directory for pagination, WAF restrictions.

**STAGE B: Acquisition**
- *Strategy*: Acquire and preserve explicit laboratory categories without merging them (`BIS_OWNED`, `BIS_RECOGNIZED`, `BIS_EMPANELLED`, `NABL_ACCREDITED`, `OTHER_RECOGNIZED`).
- *Preserve*: Lab identity/code, name, location (address only where appropriate), status, recognition/validity, testing scope, applicable standards, scope document identity, source URL, SHA-256, retrieved_at, lifecycle.
- *Relationships*: Lab-to-standard relationships must use authoritative identifiers. Do NOT infer from name similarity.

### PHASE 9.6: LICENCES / REGISTRATIONS (SRCF-007)
**STAGE A: Source Discovery**
- *Authoritative Source*: BIS Licence Search / CRS portals.
- *Mechanism*: Determine publicly accessible information required for SIH. Check for CAPTCHA/session tokens. If inaccessible, record `SESSION_REQUIRED` or `ACCESS_RESTRICTED` without bypassing.

**STAGE B: Acquisition**
- *Strategy*: Do NOT default to a full CM/L sweep. Acquire only required public data.
- *Preserve*: Licence/registration type (distinguishing BIS product, CRS, Hallmarking), identifier, manufacturer/entity, product/standard, status, validity, scope, source, retrieval time, SHA-256, lifecycle. Avoid unnecessary PII.

### PHASE 9.7: CONSUMER / BIS CARE (SRCF-010)
**STAGE A: Source Discovery**
- *Authoritative Source*: BIS Consumer Affairs portal.
- *Mechanism*: Locate HTML guidelines and workflow documentation.

**STAGE B: Acquisition**
- *Strategy*: Extract authoritative consumer workflows.
- *Preserve*: Workflow steps, service type (BIS Care, complaint, verification, etc.), eligibility, conditions, official source, version/date, provenance. Do NOT treat as normative technical evidence unless explicitly defined.

### PHASE 9.8: FAQs / GUIDES / BOOKLETS (SRCF-011)
**STAGE A: Source Discovery**
- *Authoritative Source*: BIS FAQs & Publications portals.
- *Mechanism*: Map static HTML listings.

**STAGE B: Acquisition**
- *Strategy*: Download PDFs/HTML.
- *Preserve*: Tag explicitly as `OFFICIAL_INFORMATIVE`. They must never silently become normative evidence. Preserve title, publication/version/date, topic/domain, source URL, SHA-256, retrieved_at, authority class, lifecycle.

---

## 5. Identity, Version, and Duplicate Rules
Reuse the existing identity architecture and SHA-256 hash rules deterministically:
- `SAME ID` + `SAME SHA` = **UNCHANGED**
- `SAME ID` + `DIFFERENT SHA` = **CONTENT_CHANGED_REQUIRES_VERSION_REVIEW**
- `DIFFERENT ID` + `SAME SHA` = **DUPLICATE_REPRESENTATION_ALIAS**
- `DIFFERENT ID` + `DIFFERENT SHA` = **DISTINCT_DOCUMENT**

Never overwrite immutable raw artifacts in `data/raw/immutable/`.

---

## 6. Incremental Update Design
We track multi-dimensional temporal changes for future runs:
- **Tracked State**: Source fingerprint, document identity, version, lifecycle, raw SHA-256, previous SHA (where applicable), retrieved_at, change classification, acquisition status.
- **Future Run Behavior**: Subsequent executions will discover new documents (new IDs), changed documents (same ID, changed SHA), withdrawn/superseded documents (via lifecycle field updates in metadata), amended documents (via relation chains), and removed/inaccessible records (via terminal HTTP 404s mapped to `NOT_ACCESSIBLE`).

---

## 7. Failure Taxonomy
Explicit terminal states assigned at the candidate level. Inaccessible data is NOT classified as absent data.
- `ACQUIRED`: Successfully downloaded and indexed.
- `UNCHANGED`: Matched existing immutable raw blob.
- `CONTENT_CHANGED_REQUIRES_VERSION_REVIEW`: Revision detected.
- `DUPLICATE_REPRESENTATION_ALIAS`: Alternate source yielding same payload.
- `FETCH_FAILED`: Network failure / timeout.
- `HTTP_ERROR`: 5xx errors.
- `WAF_BLOCKED`: Blocked by firewall / anti-bot.
- `SESSION_REQUIRED`: Login/Portal token expired.
- `ACCESS_RESTRICTED`: Hard restriction / CAPTCHA (do not bypass).
- `IDENTITY_UNRESOLVED`: Parsed metadata lacks valid identifiers.
- `AMBIGUOUS_MATCH`: Cannot map to a single entity.
- `MANUAL_REVIEW`: Out-of-bounds scenario requiring developer attention.

---

## 8. Coverage Metrics
Each subphase must report detailed metrics before being declared COMPLETE:
- Discovered candidates
- Eligible candidates
- Acquired
- Unchanged
- Changed
- Duplicate aliases
- Failed
- Manual review
- Unresolved identity
- Coverage percentage

*A subphase is NOT declared complete merely because the script finished. Explicit acceptance thresholds must be met.*

---

## 9. Testing Strategy
Every subphase requires automated verification:
- Source discovery tests
- Identity tests
- SHA tests
- Duplicate tests
- Provenance tests
- Negative tests
- Failure-state tests
- Incremental-update tests
- Hardcoding audit
- **Phase 6 Immutability Regression Test**: Run `scratch/verify_phase6_regression.py check`
- **Phase 8.11 Immutability Regression Test**

Verify that no Phase 9 process modifies Chroma, BM25, Phase 6 corpus, Phase 8.11 structured index, or the RAG pipeline.

---

## 10. Expected Artifacts
For every subphase:
- `data/candidates/`: Candidate manifests (JSONL).
- `data/raw/immutable/`: Raw PDFs, HTML, and JSON dumps.
- `data/catalog/`: Structured datasets (JSONL) with embedded provenance.
- `data/acquisition/manifests/`: Acquisition logs and failure traces.
- `docs/phase9/`: Phase-specific execution reports and validation logs.
- Unit/Validation test files in `tests/phase9/`.
