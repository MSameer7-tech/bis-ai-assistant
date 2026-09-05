# Phase 8.12: Structured Retrieval + Phase 6 Evidence Integration

## Executive Summary
Phase 8.12 successfully integrated the Phase 8.11 structured retrieval layer with the frozen Phase 6 `DOCUMENT_EVIDENCE` layer, forming a unified `IntegratedRetrievalOrchestrator`. This architecture provides zero-hallucination routing by ensuring that structured identity and catalogue mappings are NEVER treated as technical evidence, while simultaneously making them available to the Phase 7 RAG pipeline through strict adapter boundaries.

## Architectural Implementation

### 1. Unified Output Schema
Introduced `IntegratedRetrievalResult` and `EvidenceRole` in `integrated_retrieval_models.py`. 
These encapsulate distinct retrieval provenance constraints:
- `IDENTITY_EVIDENCE`
- `RELATIONSHIP_EVIDENCE`
- `NORMATIVE_EVIDENCE`
- `PROCEDURAL_EVIDENCE`

### 2. Integrated Retrieval Orchestrator
Implemented `IntegratedRetrievalOrchestrator` in `integrated_retrieval.py` which executes deterministic routing:
- **Exact Standard Identifiers** map to `STANDARD_METADATA` → `IDENTITY_EVIDENCE`.
- **Product-to-Standard queries** map to `PRODUCT_STANDARD_RELATIONSHIP` → `RELATIONSHIP_EVIDENCE`.
- **Normative Clause queries** bypass structured identity (or use it solely for deterministic cross-linking). They invoke Phase 6 retrieval, but retrieved chunks must explicitly pass a **Relevance Validation Gate** before they are classified as `NORMATIVE_EVIDENCE`.
  - **Intent Classification** determines if the user is asking a technical/normative question.
  - **Evidence Relevance** determines if a retrieved Phase 6 chunk actually matches the requested clause and standard identity.
  - **Evidence Role** classifies the verified relevant chunk as `NORMATIVE_EVIDENCE`.
  - **Evidence Sufficiency** determines if the accepted normative evidence is sufficient to generate a grounded answer, resulting in controlled abstention if not.

### 3. Pipeline Integration and Adapter
Modified `RAGPipeline` (in `ai/rag/pipeline.py`) to swap out the Phase 6 retriever for the new orchestrator. The pipeline translates `IntegratedRetrievalResult` into the Phase 7 `RetrievedChunk` schema via `to_retrieved_chunk()`.

To fulfill the strict mandate that metadata never be treated as normative, `ContextBuilder` (`ai/rag/context_builder.py`) was updated to append explicit system warnings to non-normative chunks:
- `STATUS: [IDENTITY METADATA ONLY - DO NOT USE AS NORMATIVE EVIDENCE]`
- `STATUS: [CATALOGUE RELATIONSHIP ONLY - DO NOT USE AS NORMATIVE EVIDENCE]`

## Testing and Verification

### Deterministic Test Suite
Created 25 deterministic test cases in `test_phase8_12_integrated_retrieval.py`. All tests passed, specifically validating the user-provided negative cases:

1. **Negative Test 1**: Metadata exists but normative evidence absent → Handled. Orchestrator returns `IDENTITY_EVIDENCE`. LLM/Evidence Gate will abstain from any technical claims.
2. **Negative Test 2**: Product relationship resolves to standard X, but Phase 6 returns evidence from standard Y → Handled. The Orchestrator retains distinct `standard_number` fields. They are not merged silently.
3. **Negative Test 3**: Product relationship resolves to a withdrawn standard → Handled. `lifecycle_status` correctly sets to `Withdrawn`.
4. **Negative Test 4**: Clause query retrieves irrelevant chunks → Handled. Irrelevant evidence fails deterministic relevance/evidence sufficiency validation and results in controlled abstention. It is NEVER passed to the LLM.
5. **Negative Test 5**: Metadata title contains technical language → Handled. Mapped correctly as `IDENTITY_EVIDENCE` and blocked from normative generation by the ContextBuilder banner.

### Audits
- **Phase 6 Immutability Check**: `scratch/verify_phase6_regression.py check` returned exit code 0 (`REGRESSION CHECK PASSED: No changes to Phase 6 artifacts.`).
- **Phase 8.11 Integration Check**: `pytest tests/phase8/test_phase8_11_structured_retrieval.py` passed 12/12 tests.
- **Hardcoding Check**: Confirmed 0 instances of `15750`, `8074`, `refrigerator`, or `60947` in the integration layer routing logic.

## Conclusion
The retrieval bridge is complete. The system now supports strictly grounded routing with deterministic abstention safeguards, natively capable of querying the authoritative BIS structured catalogue and Phase 6 document evidence corpus in tandem.
