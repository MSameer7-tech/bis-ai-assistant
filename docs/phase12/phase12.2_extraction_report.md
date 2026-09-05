# Phase 12.2: Structured Knowledge Extraction Report

## Objective
Execute the deterministic structural extraction defined by the Phase 12.1 contracts. This transforms the immutable `v22` baseline into a versioned derived dataset that explicitly models BIS domains (Documents, Laboratories, Lab Scopes, Testing Fees) as distinct, related knowledge objects rather than homogeneous vectors.

## Execution Immutability
- **v22 SHA256 before extraction**: `68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`
- **v22 SHA256 after extraction**: `68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`
- **v22 record count**: 1135
- **Frozen Artifact Modification**: None. All Phase 6, Phase 8, and Phase 10 artifacts were rigorously untouched.

## Extraction Results

### I/O Integrity
- **Input Corpus**: `data/bootstrap/bis_missing_domains_dataset_v22.jsonl`
- **Derived Dataset**: `data/derived/phase12/structured_knowledge_v1.jsonl`
- **Derived Dataset SHA256**: `c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486`

### Summary Statistics
- **Input Records**: 1135
- **Derived Entities**: 1179
- **Extraction Failures**: 0

### Entity Counts
- **DOCUMENT**: 910
- **LABORATORIES**: 180
- **LAB_SCOPE**: 44
- **TESTING_FEE**: 44
- **UNKNOWN**: 1 (Explicitly preserved `LAB-UNKNOWN_79dcb12d`)

### Relationship Counts
- **TESTS_STANDARD**: 16
- **BELONGS_TO_LAB**: 44
- **HAS_FEE**: 44
- **FEE_FOR_SCOPE**: 44

## Validation Rules Implemented
1. **One-to-Many Provenance**: LIMS records successfully exploded into distinct Laboratory, Scope, and Testing Fee objects. Every generated object retains the exact `source_record_id` and provenance chain of the parent.
2. **Missing Evidence & Invalid Records**: `LAB-UNKNOWN_79dcb12d` yielded 1 `UNKNOWN` entity with exactly 0 fabricated attributes, relationships, or accessibility states.
3. **No Arbitrary LLM Inference**: Relationships were mapped via explicit schema-to-schema structural mappings. No vectors, semantic inferences, or LLM calls occurred.
4. **Determinism**: Running the exact same code repeatedly produced the exact same derived JSONL outputs with identical hash checksums.
