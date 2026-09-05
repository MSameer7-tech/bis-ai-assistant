# Phase 9.2: QCO / Gazette / Mandatory Product Orders Acquisition Report

**Status:** PASS

## 1. Execution Summary
- **Phase**: 9.2
- **Domain**: QCO / Gazette / Mandatory Product Orders
- **Source Family**: SRCF-003
- **Discovery Mechanism**: Track A (BIS Catalogues) & Track B (QCO PDFs). HTML tables from Schemes I, II, IV, and X were parsed. PDFs were acquired and deterministic metadata extraction (including PDF parsing) was executed.

## 2. Coverage Metrics
- BIS catalogue candidates discovered (HTML rows): 382
- Unique notification/QCO URLs discovered: 149
- Unique QCO identities: 129
- QCO PDFs acquired: 121
- Unchanged: 8
- Changed/Requires version review: 0
- Duplicate aliases: 0
- Fetch failures: 20
- WAF/Session failures: 0
- PDF extraction failures: 14
- Identity unresolved: 33
- Ambiguous: 0
- Conflicting Evidence: 31

## 3. Findings & Validations
- **Identity Determinism**: `QCO-{MINISTRY}-{NOTIFICATION_NUMBER}-{YEAR}` was derived from deterministic PDF parsing where possible. Scanned PDFs defaulted to `QCO-GAZETTE-{SLUG}` and were classified as `IDENTITY_UNRESOLVED`.
- **SHA Validation**: Strict `SAME ID + SAME SHA = UNCHANGED` logic applied. No immutable artifacts were overwritten.
- **Provenance Validation**: Explicit `QCO -> IS` relationships preserved natively from HTML and PDF contexts.
- **Phase 6 & 8.11 Immutability Result**: PASS (No modifications to structured catalogs other than isolated `data/catalog/phase9_2_*` outputs).

## 4. Known Limitations
- Many QCO PDFs from the BIS server are scanned images, resulting in `EXTRACTION_FAILED` states for textual parsing.
- Some URLs return `403 Forbidden` due to BIS WAF rules, resulting in `WAF_BLOCKED` terminal states.
