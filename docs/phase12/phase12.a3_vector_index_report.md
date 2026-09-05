# Phase 12.A.3: Production Vector Index Report

## Decision
`PHASE_12_A3_STATUS: PASS`

## 1. Objective
Generate a deterministic local semantic vector index for all 1,187 Phase 12.3 retrieval units using the provisioned `all-MiniLM-L6-v2` embedding model.

## 2. Inputs
- **v22 corpus**: `data/bootstrap/bis_missing_domains_dataset_v22.jsonl`
- **Phase 12.2 structured knowledge**: `data/derived/phase12/structured_knowledge_v1.jsonl`
- **Phase 12.3 entity index**: `data/derived/phase12/entity_relationship_index_v1`
- **Retrieval units**: `data/derived/phase12/retrieval_index_foundation_v1/retrieval_units.jsonl`
- **Embedding model**: `data/models/embeddings/all-MiniLM-L6-v2`

## 3. Input Fingerprints
| Artifact | SHA256 |
|----------|--------|
| v22 | `68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe` |
| Phase 12.2 | `c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486` |
| Phase 12.3 | `ebb5f102d872246f82b534a4182624d6d9c0f5cac7697dfe887d1d237f3b135a` |
| BM25 | `4d6a07b644b5a9d172ee5c7acd34ff017746aaf58321424f462908ba87a54df6` |

## 4. Embedding Environment
- **Python**: 3.13
- **PyTorch**: 2.14.0
- **Sentence Transformers**: 6.0.1
- **Transformers**: 5.16.1
- **Tokenizers**: 0.23.2
- **NumPy**: 2.5.2
- **Device**: CPU
- **Offline mode**: Enforced (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`)

## 5. Model Information
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Local path**: `data/models/embeddings/all-MiniLM-L6-v2`
- **Embedding dimension**: 384
- **Normalization**: L2
- **Similarity metric**: Cosine (inner product on L2-normalized vectors)

## 6. Generation Methodology
- Retrieval unit texts extracted in canonical order from `retrieval_units.jsonl`.
- Encoded using `SentenceTransformer.encode()` with `normalize_embeddings=True`, `batch_size=64`, `convert_to_numpy=True`, CPU device, float32.
- Stored as `vectors.npy` (NumPy float32 matrix) with accompanying `vector_metadata.jsonl`.

## 7. Retrieval-Unit Accounting

| Metric | Expected | Actual |
|--------|-------:|------:|
| Phase 12.3 retrieval units | 1187 | 1187 |
| vectors generated | 1187 | 1187 |
| vector dimension | 384 | 384 |
| excluded units | 0 | 0 |
| missing vectors | 0 | 0 |
| orphan vectors | 0 | 0 |
| provenance mappings | 1187 | 1187 |
| duplicate vector IDs | 0 | 0 |

## 8. Vector Accounting
- **Shape**: `(1187, 384)`
- **dtype**: `float32`
- **NaN values**: 0
- **Inf values**: 0
- **Finite values**: 455808
- **Norm range**: [1.000000, 1.000000]
- **Generation time**: 4.73s

## 9. Domain Coverage

| Domain | Count |
|--------|------:|
| CONSUMER_BIS_CARE | 47 |
| FAQ_GUIDES_BOOKLETS | 41 |
| HALLMARKING | 44 |
| LABORATORIES | 253 |
| LICENCES_REGISTRATIONS | 63 |
| LIMS_SCOPE | 385 |
| OTHER | 354 |


## 10. Entity-Type Coverage

| Entity Type | Count |
|-------------|------:|
| DOCUMENT | 910 |
| LABORATORIES | 183 |
| LAB_SCOPE | 44 |
| STANDARD | 5 |
| TESTING_FEE | 44 |
| UNKNOWN | 1 |


## 11. Provenance Validation
- **All units have PROVENANCE_COMPLETE**: True
- **All units have source_record_id**: True
- **All units have phase12_2_object_id**: True

## 12. LIMS Preservation Validation
- LAB_SCOPE retrieval units: 44 (each embedded independently)
- TESTING_FEE retrieval units: 44 (each embedded independently)
- No scope/fee collapsing occurred during vector generation.

## 13. UNKNOWN Record Treatment
- `dk_LAB-UNKNOWN_79dcb12d`: text_length=14, text="UNKNOWN RECORD", embedded=True. Embedded with original text; UNKNOWN identity preserved in metadata.


## 14. Semantic Smoke Tests

### BIS product certification

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.8110 | DOCUMENT | LIC-SRC-001 | Apply for a BIS Licence Official BIS product certification licence application g |
| 2 | 0.7690 | DOCUMENT | SRC-a5e6107f4e5daee3 | BIS product certification licence process BIS explains that product certificatio |
| 3 | 0.7646 | DOCUMENT | GUIDE-002 | Apply for a licence BIS step-by-step guidance for product certification applicat |
| 4 | 0.7482 | DOCUMENT | LIC-001 | Product certification licence process BIS states that the application process be |
| 5 | 0.7136 | DOCUMENT | LIC-002 | Compulsory BIS certification BIS product certification FAQ states that products  |

### Laboratory testing scope

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.6657 | DOCUMENT | FAQ-TEST-009 | How do I find a laboratory that can test my product? Identify the applicable Ind |
| 2 | 0.6552 | DOCUMENT | LAB-SRC-002 | Recognized Lab-Wise Test Facilities BIS LIMS provides recognized-laboratory-wise |
| 3 | 0.6466 | DOCUMENT | LIC-011 | Testing facility search BIS product certification provides an IS-wise search fac |
| 4 | 0.6426 | DOCUMENT | LAB-SRC-009 | Recognized Laboratory Directory Official BIS LIMS directory of recognized testin |
| 5 | 0.6362 | DOCUMENT | LAB-SYS-008 | IS-wise laboratory search BIS provides an Indian Standard-wise list/search of re |

### Testing fee charges

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.7958 | DOCUMENT | FAQ-TEST-003 | Does every BIS-recognized laboratory charge the same testing fee? Do not assume  |
| 2 | 0.7801 | DOCUMENT | FAQ-TEST-004 | Can I know the testing cost before sending my product to a laboratory? Yes, wher |
| 3 | 0.7571 | DOCUMENT | FAQ-TEST-002 | Where can I find the current testing charge for a BIS test? Current testing char |
| 4 | 0.7395 | DOCUMENT | FAQ-TEST-019 | Can I ask for a complete testing-cost estimate? Yes, but the estimate must be as |
| 5 | 0.7264 | DOCUMENT | FAQ-TEST-006 | Can the BIS assistant give me a testing fee for my product? It should give a tes |

### Hallmarking

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.7239 | DOCUMENT | HM-001 | Hallmarking overview BIS provides the statutory hallmarking framework for precio |
| 2 | 0.7026 | DOCUMENT | HALLMARK-SRC-010 | Gold Monetization Scheme BIS provides information on the Gold Monetization Schem |
| 3 | 0.6743 | DOCUMENT | SRC-8033ffc95214e08c | Hallmarking consumer protection BIS provides consumer protection guidance coveri |
| 4 | 0.6706 | DOCUMENT | SRC-2a497491444bb91f | Hallmarking FAQ: applicable precious metals and standards BIS Hallmarking FAQ id |
| 5 | 0.6569 | DOCUMENT | GUIDE-005 | Hallmarking jeweller guidance BIS publishes guidance for jewellers dealing in ha |

### Licence registration

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.8638 | DOCUMENT | LIC-SRC-001 | Apply for a BIS Licence Official BIS product certification licence application g |
| 2 | 0.7344 | DOCUMENT | GUIDE-002 | Apply for a licence BIS step-by-step guidance for product certification applicat |
| 3 | 0.6820 | DOCUMENT | LIC-001 | Product certification licence process BIS states that the application process be |
| 4 | 0.6723 | DOCUMENT | SRC-a5e6107f4e5daee3 | BIS product certification licence process BIS explains that product certificatio |
| 5 | 0.6611 | DOCUMENT | CON-007 | Verify licence feature BIS Care provides a Verify Licence Details feature for ch |

### Consumer BIS Care

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.6627 | DOCUMENT | CON-001 | BIS Care application BIS provides the official BIS Care application as a consume |
| 2 | 0.6482 | DOCUMENT | SRC-faba08d26823b85d | Consumer grievance channel BIS maintains an official consumer grievance service  |
| 3 | 0.6456 | DOCUMENT | HM-010 | BIS Care application BIS provides the BIS Care application as an official consum |
| 4 | 0.6362 | DOCUMENT | SRC-5e893de978c0c1cb | BIS consumer grievance service BIS provides an official consumer grievance chann |
| 5 | 0.6360 | DOCUMENT | SRC-99823e1065dce0d0 | BIS Consumer Affairs BIS publishes consumer affairs information and services thr |

### IS number

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.5186 | STANDARD | SCOPE-112-01 | Standard IS 8978 IS 8978 IS 8978 IS 8978 IS 8978 (1992) |
| 2 | 0.4060 | LABORATORIES | SCOPE-840-01 | Laboratory 840 840 840 840 |
| 3 | 0.3742 | LAB_SCOPE | SCOPE-840-01 | Scope: IS 8978 (840) {"lab_code": "840", "standard": "IS 8978 (1992)", "test": " |
| 4 | 0.3687 | LAB_SCOPE | SCOPE-112-01 | Scope: IS 8978 (112) {"lab_code": "112", "standard": "IS 8978 (1992)", "test": " |
| 5 | 0.3651 | DOCUMENT | LIMS-FEE-63-034 | IS 7904 (2018) \| Dimensions & tolerances \| ₹500 Direct BIS LIMS testing-charge |

### Laboratory identifier

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.9060 | LABORATORIES | SCOPE-112-01 | Laboratory 112 112 112 112 |
| 2 | 0.6934 | LABORATORIES | SCOPE-840-01 | Laboratory 840 840 840 840 |
| 3 | 0.6313 | DOCUMENT | LAB-KB-003 | Laboratory recognition framework BIS laboratory-services information publishes t |
| 4 | 0.6205 | LABORATORIES | SCOPE-1435-01 | Laboratory 1435 1435 1435 1435 |
| 5 | 0.6133 | DOCUMENT | LAB-SRC-012 | Laboratory Services Official BIS laboratory-services page covering recognition,  |

### Testing fee

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.6722 | TESTING_FEE | V16-SCOPE-003 | Testing Fee: IS 1599 (1435) {"test_parameter": "Bend test", "amount_inr": 1000,  |
| 2 | 0.6722 | TESTING_FEE | SCOPE-1435-07 | Testing Fee: IS 1599 (1435) {"test_parameter": "Bend Test", "amount_inr": 1000,  |
| 3 | 0.6722 | TESTING_FEE | SCOPE-1435-03 | Testing Fee: IS 1599 (1435) {"test_parameter": "Bend Test", "amount_inr": 1000,  |
| 4 | 0.6658 | TESTING_FEE | V16-SCOPE-020 | Testing Fee: IS 8978 (840) {"test_parameter": "Electric instantaneous water heat |
| 5 | 0.6647 | TESTING_FEE | V16-SCOPE-019 | Testing Fee: IS 8978 (112) {"test_parameter": "Electric instantaneous water heat |

### Document

| Rank | Score | Entity Type | Source ID | Text Preview |
|-----:|------:|-------------|-----------|-------------|
| 1 | 0.8650 | DOCUMENT | CON-001 | BIS Care application BIS provides the official BIS Care application as a consume |
| 2 | 0.8284 | DOCUMENT | CONSUMER-SRC-006 | BIS Care App Official BIS information about the BIS Care application and its ver |
| 3 | 0.8043 | DOCUMENT | HM-010 | BIS Care application BIS provides the BIS Care application as an official consum |
| 4 | 0.7914 | DOCUMENT | HALLMARK-SRC-020 | BIS Apps Official BIS page describing BIS applications including BIS Care functi |
| 5 | 0.7434 | DOCUMENT | CONSUMER-KB-001 | BIS Care verification BIS Care provides consumer-facing verification and informa |


## 15. Determinism Test
- **Run 1 SHA256**: `ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad`
- **Run 2 SHA256**: `ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad`
- **Byte-identical**: True

## 16. Immutability Test
- **v22 unchanged**: True
- **Phase 12.2 unchanged**: True
- **Phase 12.3 unchanged**: True
- **BM25 unchanged**: True

## 17. Performance
- **Generation time**: 4.73s for 1187 units
- **Batch size**: 64
- **Vector matrix size**: 1780.6 KB
- **Metadata size**: 376.6 KB

## 18. Failures
None.

## 19. Limitations
- Semantic smoke tests demonstrate retrieval capability but do not establish production quality thresholds.
- Hybrid fusion, authority ranking, and reranking are deferred to later phases.

## 20. Artifacts
- Vector matrix: `data/derived/phase12/retrieval_index_foundation_v1/vector/vectors.npy`
- Vector metadata: `data/derived/phase12/retrieval_index_foundation_v1/vector/vector_metadata.jsonl`
- Manifest: `data/derived/phase12/retrieval_index_foundation_v1/vector_index_manifest.json`
- Vector matrix SHA256: `ca8d0ad4c614adf796713973c0205ee522331b3a8e848704d4726141c91660ad`
- Metadata SHA256: `f23e7a4c5ff5dc418921d4b576f4b9c4b10748c6d49cd9f1139a4cf3ffdbf0fb`
