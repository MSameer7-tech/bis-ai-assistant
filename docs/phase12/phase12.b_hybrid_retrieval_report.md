# Phase 12.B: Hybrid Retrieval Intelligence Report
## Decision
`PHASE_12_B_STATUS: PASS`
## 1. Retrieval Architecture
```
USER QUERY → Query Normalization → Identifier Extraction
  ├── Structured Retrieval (exact field match)
  ├── BM25 Retrieval (lexical)
  └── Vector Retrieval (semantic, all-MiniLM-L6-v2)
        ↓
  Candidate Union (deduplicated by retrieval_unit_id)
        ↓
  Reciprocal Rank Fusion (k=60, equal weights)
        ↓
  Exact Identifier Boost (×2.0)
        ↓
  Authority Adjustment (BIS_PUBLISHED=1.0, BIS=0.95, USER=0.8, UNKNOWN=0.6)
        ↓
  Inaccessible Evidence Penalty (×0.5)
        ↓
  Freshness Signals (date-aware, no inference)
        ↓
  Supersession Handling (explicit evidence only)
        ↓
  Final Deterministic Sort (score desc → authority asc → ID asc)
```
## 2. Fusion Formula
Reciprocal Rank Fusion:
```
RRF_score(d) = Σ w_channel × 1/(k + rank_channel(d))
             × exact_match_boost (if applicable)
             × authority_weight
             × inaccessible_penalty (if applicable)
             × superseded_penalty (if applicable)
```
- k = 60
- Channel weights: structured=1.0, bm25=1.0, vector=1.0
- Exact match boost: 2.0

## 3. Test Query Results
### A_exact_IS: `IS 616`
- Structured candidates: 1
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 35
- Identifiers: {"is_numbers": ["IS 616"], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0973 | DOCUMENT | LIC-020 | BIS_PUBLISHED | UNKNOWN | structured,bm25,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0290 | STANDARD | SCOPE-1435-03 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0284 | STANDARD | SCOPE-1435-01 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0278 | STANDARD | SCOPE-112-01 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0270 | STANDARD | SCOPE-1435-04 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### B_laboratory: `Which laboratories can test cement products?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 37
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0306 | DOCUMENT | FAQ-TEST-009 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0286 | LABORATORIES | LAB-RECOGNIZED-9102335 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0250 | DOCUMENT | LIMS-SCOPE-15-001 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0159 | DOCUMENT | LIC-011 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0156 | DOCUMENT | FAQ-TEST-005 | BIS | UNKNOWN | bm25 | BM25_MATCH,AUTHORITATIVE_SOURCE |

### C_testing_fee: `What is the testing fee for IS 8978?`
- Structured candidates: 9
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 30
- Identifiers: {"is_numbers": ["IS 8978"], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0793 | TESTING_FEE | SCOPE-112-01 | BIS | UNKNOWN | structured,bm25,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0587 | TESTING_FEE | V16-SCOPE-020 | BIS | UNKNOWN | structured,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0586 | TESTING_FEE | V16-SCOPE-019 | BIS | UNKNOWN | structured,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0555 | TESTING_FEE | SCOPE-840-01 | BIS | UNKNOWN | structured,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0311 | LAB_SCOPE | SCOPE-112-01 | BIS | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |

### D_hallmarking: `How does BIS hallmarking work for gold jewellery?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 35
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0306 | DOCUMENT | HALLMARK-SRC-010 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0299 | DOCUMENT | HM-038 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0276 | DOCUMENT | FAQ-TEST-013 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0264 | DOCUMENT | SRC-2a497491444bb91f | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0262 | DOCUMENT | HM-017 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### E_licence: `How to apply for a BIS product certification licence?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 27
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0318 | DOCUMENT | GUIDE-002 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0309 | DOCUMENT | LIC-SRC-001 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0307 | DOCUMENT | GUIDE-001 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0299 | DOCUMENT | LIC-002 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0288 | DOCUMENT | LIC-KB-001 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### F_consumer: `How can I file a complaint through BIS Care?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 39
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0303 | DOCUMENT | CON-80147188-7f9c-4975-acaf-9242dcb98c11 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0164 | DOCUMENT | CON-001 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0156 | DOCUMENT | FAQ-TEST-009 | BIS | UNKNOWN | bm25 | BM25_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0154 | DOCUMENT | GUIDE-001 | BIS_PUBLISHED | UNKNOWN | bm25 | BM25_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0154 | DOCUMENT | HM-010 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### G_faq: `What is the process for getting a BIS certification mark?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 34
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0315 | DOCUMENT | LIC-001 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0297 | DOCUMENT | SRC-a5e6107f4e5daee3 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0292 | DOCUMENT | LIC-002 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0285 | DOCUMENT | GUIDE-002 | BIS_PUBLISHED | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0282 | DOCUMENT | LIC-SRC-001 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### H_date: `What are the current testing charges effective in 2026?`
- Structured candidates: 0
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 39
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0270 | DOCUMENT | FAQ-TEST-002 | BIS | UNKNOWN | bm25,vector | BM25_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0161 | DOCUMENT | LAB-SYS-009 | BIS_PUBLISHED | UNKNOWN | bm25 | BM25_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0156 | DOCUMENT | FAQ-TEST-015 | BIS | UNKNOWN | bm25 | BM25_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0156 | DOCUMENT | LIMS-FEE-48-018 | BIS | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0153 | DOCUMENT | LIMS-FEE-65-038 | BIS | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |

### I_version: `What is the latest revision of IS 8978?`
- Structured candidates: 9
- BM25 candidates: 20
- Vector candidates: 20
- Union candidates: 47
- Identifiers: {"is_numbers": ["IS 8978"], "lab_codes": [], "source_ids": []}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0604 | STANDARD | SCOPE-112-01 | BIS | UNKNOWN | structured,vector | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0311 | LAB_SCOPE | SCOPE-112-01 | BIS | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0306 | LAB_SCOPE | SCOPE-840-01 | BIS | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0302 | LAB_SCOPE | V16-SCOPE-019 | BIS | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0297 | LAB_SCOPE | V16-SCOPE-020 | BIS | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |

### J_unknown: `LAB-UNKNOWN_79dcb12d`
- Structured candidates: 1
- BM25 candidates: 0
- Vector candidates: 20
- Union candidates: 21
- Identifiers: {"is_numbers": [], "lab_codes": [], "source_ids": ["LAB-UNKNOWN_79dcb12d"]}

| Rank | Score | Entity Type | Source ID | Authority | Supersession | Channels | Reasons |
|-----:|------:|-------------|-----------|-----------|-------------|----------|--------|
| 1 | 0.0328 | UNKNOWN | LAB-UNKNOWN_79dcb12d | BIS_PUBLISHED | UNKNOWN | structured | EXACT_IDENTIFIER_MATCH,STRUCTURED_MATCH,AUTHORITATIVE_SOURCE |
| 2 | 0.0161 | LABORATORIES | LAB-R-064 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 3 | 0.0159 | LABORATORIES | LAB-B-001 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 4 | 0.0156 | LABORATORIES | SCOPE-840-01 | BIS | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |
| 5 | 0.0149 | LABORATORIES | LAB-B-002 | BIS_PUBLISHED | UNKNOWN | vector | VECTOR_MATCH,AUTHORITATIVE_SOURCE |

## 4. Determinism
- **Identical results on repeated query**: True

## 5. Immutability
- v22 unchanged: True
- Phase 12.2 unchanged: True
- Phase 12.3 unchanged: True
- BM25 unchanged: True
- Vectors unchanged: True

## 6. Frozen Artifact Hashes
- v22: `68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`
- Phase 12.2: `c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486`
- Vectors: `ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad`
- BM25: `4d6a07b644b5a9d172ee5c7acd34ff017746aaf58321424f462908ba87a54df6`

## 7. Limitations
- Channel weights and RRF constant are baseline defaults, not optimized.
- Freshness signals rely on explicit metadata; most records have UNKNOWN dates.
- Supersession is UNKNOWN for all records (no explicit supersession evidence in v22).
- Authority weights are reasonable defaults, not empirically calibrated.
- Production quality thresholds will be established in Phase 12.D.
