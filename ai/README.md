# AI + BIS Knowledge Module

This module forms the intelligence and knowledge core of the **BIS AI Assistant for Indian Standards**. It handles document ingestion, structural parsing, hybrid retrieval, deterministic reasoning, grounded answer generation, and citation tracking.

---

## 🎯 Purpose

To provide accurate, traceable, and source-backed answers to natural-language questions about Indian Standards, QCOs, certification schemes, testing requirements, and recognized laboratories.

The system enforces a **retrieval-grounded, rule-backed architecture** rather than relying on ungrounded LLM completions.

---

## 🛠️ Core Responsibilities

The AI module is responsible for:

1. **BIS Data Ingestion (`ai/ingestion/`)**:
   - Fetching and tracking official BIS standards, QCOs, and regulatory documents.
   - Preserving source metadata (Standard Number, Version, Edition, Amendments, Retrieval Date, Source URL).

2. **Document Processing (`ai/processing/`)**:
   - High-fidelity PDF parsing preserving page boundaries.
   - Structural extraction (Sections, Clauses, Subclauses, Tables, Annexes).
   - Text cleaning and structured JSON generation.

3. **Knowledge Representation & Chunking (`ai/processing/`)**:
   - Structure-aware chunking preserving hierarchy and clause/page metadata.
   - Metadata normalization and schema enforcement.

4. **Retrieval Engine (`ai/retrieval/`)**:
   - Keyword search (BM25 / exact matches on standard numbers, clauses, and technical terms).
   - Dense semantic vector search.
   - Metadata filtering & hybrid search combination.
   - Reranking to select the most relevant authoritative evidence.

5. **Reasoning & Applicability Engine (`ai/reasoning/`)**:
   - Deterministic rule evaluation (e.g., Product $\to$ Applicable QCO $\to$ Mandatory Certification Requirement).
   - Safe uncertainty handling & abstention ("Insufficient evidence" vs hallucination).

6. **Grounded RAG & Generation (`ai/rag/`)**:
   - Building grounded prompts with retrieved BIS evidence chunks.
   - LLM generation for synthesis, explanation, and multilingual translation.
   - Enforcing system safety and prompt injection defense.

7. **Standard Recommendation Engine (`ai/recommendation/`)**:
   - Mapping natural-language product descriptions to candidate Indian Standards with evidence-based justification.

8. **Citation & Evidence System**:
   - Mapping every factual claim to exact Document ID, Standard Number, Clause, Page Number, and Source URL.

9. **Evaluation & Quality Assurance (`ai/evaluation/`)**:
   - Benchmark datasets covering standard lookup, recommendations, QCOs, testing, and multilingual queries.
   - Metrics for retrieval recall, factual grounding, citation accuracy, and safe abstention.

10. **Service Integration (`ai/services/`)**:
    - Clean interface for backend consumption (`ai_service.py`).

---

## 🚫 Non-Responsibilities (Developer B / Platform Scope)

The following components are handled by the Backend / Platform layer and are outside the scope of this module:

* **Frontend UI / UX**: Web application interface, chat UI, responsive layouts, PDF source viewer.
* **Authentication & Authorization**: User login, JWT/OAuth, role-based access control.
* **User Management & Sessions**: Session storage, chat history persistence.
* **Infrastructure & Deployment**: PostgreSQL/pgvector database hosting, Render/Vercel deployment pipelines, cloud monitoring.

---

## 📂 Subpackage Overview

```text
ai/
├── ingestion/       # PDF parsing, document cleaning, structure extraction
├── processing/      # Structure-aware chunker, metadata normalization
├── retrieval/       # Keyword, semantic, hybrid search, rerankers
├── rag/             # Grounded prompt construction, LLM response generators
├── reasoning/       # Deterministic rule engine, intent parser, applicability checks
├── recommendation/  # Product-to-standard recommendation logic
├── evaluation/      # Benchmark datasets, evaluation runner, scoring metrics
├── services/        # Clean AI service interface for backend integration
├── config.py        # Settings & environment configuration
└── logging_config.py# Structured logging setup
```
