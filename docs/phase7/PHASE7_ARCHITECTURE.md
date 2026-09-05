# Phase 7 Architecture: End-to-End Grounded BIS RAG Assistant

## 1. Existing-Component Inventory
Based on the repository inspection, the following components are already in place:
- **Phase 6 Retriever (`ai/vectorstore/hybrid_search.py` & `ai/rag/retriever.py`)**: 
  - `HybridSearchEngine` orchestrates retrieval via Chroma vector DB (`bis_phase6_baseline`), BM25, and Exact Match indices.
  - `RAGRetriever` acts as an adapter, fetching results and mapping them into strongly-typed `RetrievedChunk` Pydantic models.
- **RAG Pipeline Orchestrator (`ai/rag/pipeline.py`)**: 
  - An extensive 18-stage pipeline including Query Understanding, Intent Classification, Product Resolution, Retrieval, Parameter Evidence Pre-Validation, Grounded Generation, Citation Extraction, Atomic Claim Verification, Numerical Verification, and Confidence Calculation.
- **Models & Schemas (`ai/rag/models.py`, `ai/rag/schema.py`, `backend/schemas_v5.py`)**: 
  - `RAGAnswer`, `ProductionAnswerPayload`, `Citation`, `NumericalVerification`, and `AtomicClaim`.
- **Generators (`ai/rag/generator.py`)**:
  - `DeterministicGroundedGenerator` (rule-based offline generator).
  - `OllamaLLMProvider` (local LLM via API).
- **Verifiers (`ai/verification/numerical_verifier.py`, `ai/verification/claim_verifier.py`)**: 
  - `NumericalVerifier` runs deterministic parameter-against-chunk checks.
  - `ClaimVerifier` runs entailment logic on claims.
- **Guardrails (`ai/rag/guardrails.py`, `ai/rag/evidence_gate.py`)**:
  - `ComplianceGuardrails` and `RefusalBuilder`.

## 2. Integration Points with Phase 6
- **Index Loading**: `HybridSearchEngine` loads the persistent indices located in `data/indexes/`.
- **Chunk Representation**: The output from the retriever conforms strictly to `RetrievedChunk`, ensuring all chunk metadata (standard number, clause, document id, temporal status, normative force, and evidence text) is propagated into the RAG pipeline.
- **Document Identity & Source Family**: Represented via `document_id` and `source_id` within the `RetrievedChunk`, directly linking back to Phase 5's frozen `EvidenceUnits`.
- **Pre-Flight Validation Gates**: Phase 6 fingerprint (17,167 EvidenceUnits, 18,045 chunks) is strictly maintained. The retriever uses the locked vectors and BM25 index built during Phase 6.

## 3. Proposed File Changes
- **`ai/rag/generator.py`**:
  - Introduce `CloudLLMProvider` (e.g., integrating Gemini 1.5 Pro, Claude 3.5 Sonnet, or OpenAI gpt-4o) to replace or supplement `DeterministicGroundedGenerator` and `OllamaLLMProvider` for production answer generation.
- **`ai/rag/pipeline.py`**:
  - Refine Step 9 (Grounded Generation) and Step 10 (Citation Extraction) to enforce the "generate-then-verify" paradigm robustly with a live cloud LLM.
- **`ai/rag/citation.py`**:
  - Improve strict quote-matching verification to guarantee 100% provenance chain: `answer -> citation -> retrieved chunk -> EvidenceUnit`.
- **`config.py` or `.env`**:
  - Add API keys and configuration for the production LLM provider.

## 4. Proposed Test Plan
- **Unit Testing**: Inject fixed `RetrievedChunk` payloads into the generator and verify deterministic LLM adherence to citations.
- **Integration Testing**: Execute the End-to-End RAG query for a subset of queries covering SUFFICIENT, INSUFFICIENT, and CONFLICTING evidence, asserting the correct `status` (verified vs. refused).
- **Adversarial Testing**: Test "trap" queries (e.g., asking for unsupported materials like titanium or unrelated knowledge like weather) to confirm the pipeline abstains appropriately (Zero-Hallucination).

## 5. LLM/Provider Configuration Requirements
- We will support cloud provider integrations (e.g., Gemini via `google-genai` or `vertexai`). 
- Requirements:
  - Strict generation instructions to ONLY use provided chunks.
  - Forced schema output for structured claims.
  - API Keys injected via environment variables (e.g., `GEMINI_API_KEY`).

## 6. Grounding and Citation Design
- **Verification Workflow**:
  1. Retrieve top `k` chunks via Phase 6 hybrid search.
  2. The LLM generates a draft response accompanied by embedded citations.
  3. The `CitationExtractor` and `NumericalVerifier` act as post-generation deterministic validators.
  4. If a citation cannot be strictly matched to the text of the `RetrievedChunk`, it is marked as `verified=False`.
  5. The `ComplianceGuardrails` module evaluates the verified citations and numerical claims. If there is a mismatch or hallucinated value, the pipeline falls back to a grounded refusal.

## 7. Phase 7 Execution Order
1. **Implement Cloud LLM Provider**: Update `ai/rag/generator.py`.
2. **Refine Citation Pipeline**: Harden `ai/rag/citation.py` and pipeline steps.
3. **End-to-End Testing**: Validate API endpoints in `backend/app.py`.
4. **Final Acceptance**: Execute the benchmark test suite to ensure RAG performance.
