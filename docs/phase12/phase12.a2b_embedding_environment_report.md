# Phase 12.A.2B: Local Embedding Environment Provisioning via Host Machine

## Decision
`PHASE_12_A2B_STATUS: PASS`

## Environment Details
- **Selected Python version**: Python 3.13 (via Host `/usr/local/bin/python3.13`)
- **Environment path**: `scratch/embedding_venv`
- **Installation method**: Host Mac shell execution
- **Installed versions**:
  - PyTorch: `2.14.0`
  - Sentence Transformers: `6.0.1`
  - Transformers: `5.16.1`
  - Tokenizers: `0.23.2`
  - Hugging Face Hub: `1.30.0`
- **Selected backend**: Sentence Transformers + PyTorch CPU
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Model revision**: `PRESENT`
- **Local model path**: `data/models/embeddings/all-MiniLM-L6-v2`
- **Embedding dimension**: 384
- **Device**: `cpu` (Selected for maximum determinism across platforms)
- **Normalization**: `L2` (Required for Cosine Similarity)

## Validation Results
- **Cosine similarity validation**:
  - **Test A (Identical sentences)**: Identical representations? **True**
  - **Test B (Related sentences)**: Cosine similarity = **0.3405**
  - **Test C (Unrelated sentence)**: Cosine similarity = **0.0032**
  - *Result*: Test B > Test C confirms semantic alignment.
- **Offline validation**: PASSED. Model successfully loaded with `HF_HUB_OFFLINE=1` using `local_files_only`.
- **Determinism validation**: PASSED. Running the exact same text twice produced byte-identical embeddings. `NaN` and `Inf` checks passed.

## Tests
- **Immutability verification**: PASSED.
- **Environment provisioning test**: PASSED.

## Frozen Artifact Hashes
- **v22 unchanged**: YES (`68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`)
- **Phase 12.2 unchanged**: YES (`c91c1f0a46f235ff64738c9e1ea1fecedf9078b94076779ffd1635d95b068486`)
- **Phase 12.3 unchanged**: YES
- **BM25 unchanged**: YES (`4d6a07b644b5a9d172ee5c7acd34ff017746aaf58321424f462908ba87a54df6`)
