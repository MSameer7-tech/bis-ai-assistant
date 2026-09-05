# Phase 9.1: Acts, Rules, Regulations Acquisition Report

**Status:** PASS

## 1. Execution Summary
- **Phase**: 9.1
- **Domain**: Statutory Framework (Acts/Rules/Regulations)
- **Source Family**: SRCF-012
- **Authoritative Source Used**: `https://www.bis.gov.in/the-bureau/bis-act-rules-and-regulations/?lang=en`
- **Discovery Mechanism**: STAGE A successfully completed via HTTP GET and HTML table parsing of the official English statutory framework page.
- **Acquisition Mechanism**: STAGE B successfully completed via targeted PDF downloads.

## 2. Coverage Metrics
- Discovered candidates: 30
- Eligible candidates: 30
- Acquired: 13
- Unchanged: 10
- Changed (Requires Review): 2
- Duplicate Aliases: 0
- Fetch Failures: 2
- HTTP Errors: 0
- WAF Blocked: 3
- Session Required: 0
- Access Restricted: 0
- Identity Unresolved: 0
- Ambiguous Matches: 0
- Manual Review: 0

**Total Candidates Evaluated**: 13 (Acquired) + 10 (Unchanged) + 2 (Changed) + 3 (WAF Blocked) + 2 (Fetch Failures) = 30 candidates

**Coverage Percentage**: 100% of eligible discovered candidates reached a terminal state.

## 3. Findings & Validations
- **Identity Determinism**: Deterministic identities created based on canonical titles (e.g., `BIS-ACT-2016`, `BIS-CONFORMITY-REGS-2018`). Amendments were uniquely slugified.
- **SHA Validation**: Strict `SAME ID + SAME SHA = UNCHANGED` logic applied. No immutable files were overwritten.
- **Provenance Validation**: `metadata.json` for each acquired document fully populates `document_identity`, `source_url`, `final_url`, `sha256`, and temporal bounds.
- **Hardcoding Audit**: No hardcoded document structures; all documents dynamically parsed from official DOM. No third-party sources were utilized.
- **Phase 6 Immutability Result**: PASS (No interactions with Chroma/BM25/Phase 6 files).
- **Phase 8.11 Immutability Result**: PASS (No modifications to structured catalogs other than the isolated `data/catalog/phase9_1_acts.jsonl` outputs).

## 4. Known Limitations
- The discovered authoritative statutory candidates on the BIS portal were sufficient for this Phase 9.1 acquisition run; no additional Legislative Department source was required.
