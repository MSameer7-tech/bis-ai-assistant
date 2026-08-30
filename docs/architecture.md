# System Architecture

## 1. High-Level Flow

```text
User
  ↓
Frontend (React / Next.js)
  ↓
Backend API (FastAPI)
  ↓
AI Service Interface
  ↓
Query Understanding (Intent, Entity & Attribute Extraction, Language Detection)
  ↓
Retrieval Engine (Keyword BM25 + Semantic Vector Search + Metadata Filtering)
  ↓
BIS Knowledge Base (Structured Clauses, QCOs, Standards, Tables, Scopes)
  ↓
Reasoning Engine (Deterministic Applicability Rules, Fact Checking, Uncertainty Gates)
  ↓
RAG / LLM Generation (Grounded Context Synthesis, Multilingual Explanation)
  ↓
Citation & Evidence Validation (Document, Clause, Page Number Mapping)
  ↓
Final Response (Answer + Source Citations + Abstention if insufficient)
```

---

## 2. Core Components

### 2.1 Ingestion & Document Processing Pipeline
* **Input**: Authoritative BIS Standards (PDFs), Quality Control Orders (QCOs), Certification Schemes, Laboratory Scopes.
* **Extraction**:
  * Page-accurate text extraction using high-fidelity parsers (PyMuPDF / pdfplumber).
  * Structure recognition: Sections, Clauses, Subclauses, Tables, Annexes.
* **Storage**: Normalized structured JSON preserving document ID, standard number, clause ranges, and exact page numbers.

### 2.2 Knowledge Representation & Indexing
* **Structure-Aware Chunking**: Chunks bounded by logical clauses and sections rather than arbitrary character cuts.
* **Dual Indexing**:
  * **Keyword / Lexical**: Inverted index for exact IS numbers, clause numbers, and technical terms.
  * **Dense Semantic**: Embeddings stored in PostgreSQL + pgvector for semantic search.
* **Metadata Layer**: Rich filtering on product category, standard status, amendment number, and document type.

### 2.3 Query Understanding & Intent Classification
* Identifies user intent:
  * `standard_lookup`
  * `standard_recommendation`
  * `certification_requirement`
  * `certification_process`
  * `qco_lookup`
  * `testing_requirement`
  * `laboratory_search`
  * `hallmarking`
  * `technical_question`
  * `consumer_query`
* Extracts product entities, specifications (e.g., wattage, voltage, lamp type), and query language (English, Hindi, Hinglish).

### 2.4 Hybrid Retrieval & Reranking
* Combines lexical BM25 matching and dense vector similarity.
* Applies metadata constraints (e.g., product domain = LED lamps, active standards only).
* Reranks candidate evidence to select top authoritative chunks for context construction.

### 2.5 Deterministic Reasoning Engine
* Evaluates regulatory logic deterministically without relying on LLM guesses (e.g., checking QCO mandatory date, scope applicability).
* Enforces uncertainty gates: Returns explicit "insufficient evidence" if the knowledge base lacks necessary authoritative proof.

### 2.6 Grounded Generation & Citation Verification
* Feeds retrieved BIS evidence as structured data to the LLM.
* Generates fluent, multilingual explanations adhering strictly to the provided context.
* Validates every claim against chunk metadata to ensure correct citation of `Standard Number`, `Clause`, and `Page`.

---

## 3. Pilot Scope: LED Lamps / Bulbs

The initial vertical slice is validated entirely against the **LED lamps and bulbs** ecosystem:
* Safety standards (e.g., IS 16102 Part 1)
* Performance standards (e.g., IS 16102 Part 2)
* Component & driver standards (e.g., IS 15885)
* Compulsory Registration Scheme (CRS) & QCO applicability
* Testing requirements and recognized testing laboratories
