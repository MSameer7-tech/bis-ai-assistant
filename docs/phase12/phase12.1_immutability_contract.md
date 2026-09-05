# Phase 12.1: Immutability Contract

## 1. Core Immutability Principles
The BIS AI Assistant project operates under strict auditability constraints. Data must never be silently mutated, overwritten, or assumed.

### Baseline Immutability
- **The Phase 11.3B `v22` dataset is FROZEN.**
- Its byte identity and SHA-256 (`68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe`) must remain exactly identical in all future phases.
- The record count (1,135) cannot change.
- Defective records (like `LAB-UNKNOWN_79dcb12d`) MUST remain in the corpus for historical traceability. They are handled at the extraction/retrieval layer via metadata filtering, never by deletion.

### Frozen Artifact Immutability
Previously frozen artifacts must not be silently rebuilt or modified. Any historical artifact from the following phases must be preserved exactly as they were at the time of their freezing:
- Phase 6 indexes
- Phase 8 retrieval artifacts
- Phase 8.11 structured retrieval artifacts
- Phase 8.12 integrated retrieval artifacts
- Phase 8.13 validation artifacts
- Phase 8.14 coverage artifacts
- Phase 9 validated acquisition artifacts
- Phase 10 production-hardening artifacts

*Rule: If a new embedding model, index architecture, or parsing logic is implemented, it MUST be written to a new derived path (e.g., `Phase 12.x_indices`). Old artifacts remain untouched.*

## 2. Update and Freshness Model
The corpus update mechanism relies on **Append-Only Versioning**, not in-place modification.

When new BIS data is acquired (e.g., an amended hallmarking order):
1. **New Acquisition**: The new document is fetched.
2. **Change Detection**: The pipeline identifies differences against the previous baseline.
3. **New Corpus Version**: A new immutable dataset (e.g., `v23.jsonl`) is created incorporating the new record and marking the old record with a supersession pointer.
4. **Derived Knowledge Update**: The Phase 12 extraction pipeline is run against `v23`.
5. **Retrieval Index Update**: The vector and lexical indexes are built against the `v23` derived knowledge.

**Prohibited Actions:**
- Do NOT retrain the language model to inject new facts.
- Do NOT delete the old version of the document from the historical index. It must remain accessible for queries asking "What was the rule in 2024?", managed via effective dates.

## 3. Cryptographic Verification
Any future architectural operation that relies on the baseline must perform a cryptographic check against the input dataset before proceeding. If the dataset's SHA-256 does not match the frozen signature, the operation must abort.
