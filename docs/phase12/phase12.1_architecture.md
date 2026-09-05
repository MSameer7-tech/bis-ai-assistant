# Phase 12.1: Frozen Corpus Contract + RAG Architecture Baseline

## 1. Corpus Layer
The foundational layer is the immutable Phase 11.3B `v22` corpus. This dataset (`data/bootstrap/bis_missing_domains_dataset_v22.jsonl`) contains 1,135 strictly validated JSONL records. The retrieval system treats this as a read-only data store.

## 2. Derived Knowledge Layer
To answer complex BIS queries, raw JSONL records are mapped to structured, typed entities:
- **Documents**: FAQs, guides, booklets, official orders.
- **Standards**: Indian Standards (IS), mapped to their components (parts, years).
- **Products**: Mapped to standard applicability via strict evidence.
- **Laboratories**: Mapped to scopes, addresses, and fees.
- **Testing Parameters / Fees**: Independent structured entities linked to Labs/IS.
- **QCOs**: Quality Control Orders and effective dates.
- **Licenses / Registrations**: Procedural entities (e.g., Jeweller Registration, CRS).
- **Hallmarking Entities**: AHCs and Jewellers.
- **Consumer Procedures**: Complaints and verification flows.

*Rule: Explicit relationships only. If evidence is missing, use `UNKNOWN`.*

## 3. Retrieval Layer
The Phase 12 architecture implements a **Hybrid Fusion Engine**:
- **Structured Retrieval**: Filters by exact matches (e.g., IS Number, Lab Code, Product Name).
- **Lexical Retrieval (BM25)**: Keyword-based document matching for dense procedural texts.
- **Vector Retrieval**: Semantic search for natural language queries (e.g., "How do I file a complaint?").
- **Hybrid Fusion**: Combines scores from lexical and vector retrieval, strictly gated by structured filters.

## 4. Ranking Layer
Retrieved candidates are ranked based on:
1. **Authority Score**: Tier 1 Normative > Tier 1 Official Operational > Tier 2 Explanatory (Weights `TO_BE_VALIDATED`).
2. **Freshness**: Newer effective dates outrank older ones.
3. **Supersession**: Explicitly superseded documents receive a heavy penalty or are filtered entirely unless historical queries demand them.
4. **Exact-Match Relevance**: Direct hits on IS numbers or Lab names.
5. **Semantic Relevance**: Vector cosine similarity.
6. **Evidence Completeness**: Records with full provenance score higher than records with partial provenance.

## 5. Evidence Layer
Every piece of knowledge supplied to the Answer Layer MUST retain:
- `source_url`
- `source_title`
- `issuing_authority`
- `source_type`
- `acquisition_timestamp`
- `source_sha256`
- `corpus_version` (e.g., v22)
- `record_id`
- `document_identity`
- `relevant_section`
- `effective_date`
- `supersession_status`

## 6. Answer Layer (Generation)
The generation layer is strictly a grounded synthesizer. It must NOT treat its language model weights as an authority.
- **Hallucination Safeguards**: The system must explicitly cite evidence.
- **Gaps**: If the retrieval layer yields `UNKNOWN`, `INSUFFICIENT_EVIDENCE`, or `INACCESSIBLE_SOURCE`, the Answer Layer must explicitly inform the user that the BIS corpus does not establish the answer. Fabrications of dates, fees, IS numbers, or lab capabilities are strictly prohibited.
