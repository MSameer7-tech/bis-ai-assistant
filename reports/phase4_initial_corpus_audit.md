# Phase 4 Initial Corpus & Architecture Audit Report

**Date**: September 1, 2026  
**Auditor**: Antigravity Assistant (SIH 2026)  
**Scope**: Bureau of Indian Standards (BIS) Complete Knowledge Acquisition & Data Pipeline  
**Baseline State**: Phase 3 Retrieval Safety & Grounding Complete (201/201 pytest, 22/22 retrieval safety, 100/100 golden, 2719/2719 master benchmark)

---

## 1. Executive Summary & Inventory Counts

| Artifact / Entity Family | Current Count | Location / File Path | Notes / Status |
|---|---|---|---|
| **Raw Standards PDFs** | **144** files | `data/raw/` | 110 unique document IDs (`DOC-001` to `DOC-110`), plus amendments & versioned variants |
| **Processed JSONs** | **110** files | `data/processed/*.json` | Full page/clause extractions from PyMuPDF/pdfplumber |
| **Normalized Document Specs** | **220** files | `data/normalized/*.json` | Canonical schema with requirements, tables, definitions, and KG edges |
| **Individual Chunks** | **3,922** chunks | `data/chunks/*.json` | 1,961 active production chunks across 110 standards |
| **Indexed Vector Store Embeddings** | **1,961** vectors | `data/vector_store/chroma/` | ChromaDB collection + BM25 inverted lexical index |
| **Discovered Standards in Catalog** | **663** records | `data/registry/standards_catalog.jsonl` | Discovered standards across 8 BIS domains |
| **Unique IS Numbers in Scope** | **110** normative | `data/metadata/documents.json` | 107 distinct standards actively referenced in benchmarks |
| **Discovered Products** | **560** records | `data/registry/products.jsonl` | 560 products mapped directly to Indian Standards |
| **Active Entity Relationships** | **2,266** edges | `data/registry/relationships.jsonl` | Multi-relational graph (Lab, Product, Committee, Amendment, SIT, QCO) |
| **Source Registry Entries** | **116** URLs | `data/metadata/source_registry.json` | Active BIS portals & source documents |
| **BIS Source Families** | **9** registered | `data/registry/bis_sources.jsonl` | Portals for KYS, Standards, QCOs, Product Manuals, SIT, Labs, etc. |
| **Mandatory QCO Relationships** | **27** edges | `data/registry/relationships.jsonl` | Verified gazette-mandated QCO relationships |
| **Product Manual Edges** | **105** edges | `data/registry/relationships.jsonl` | Standards with linked product manual specs |
| **SIT (Scheme of Inspection) Edges** | **105** edges | `data/registry/relationships.jsonl` | Testing frequencies & sampling schemes |
| **Laboratory Testing Edges** | **840** edges | `data/registry/relationships.jsonl` | IS-to-Lab recognition mappings |

---

## 2. Existing Acquisition & Data Pipeline Architecture

```
                                  OFFICIAL BIS PORTALS
 (Know Your Standard / e-BIS / Manakonline / Gazette / LIMS / CRS / Hallmarking)
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    BIS Source Registry & Discovery   │
                      │  (ai/acquisition/sources/*.py)       │
                      │  - know_your_standard.py             │
                      │  - product_manuals.py                │
                      │  - sit.py, qco.py, laboratories.py   │
                      │  - bis_standards.py, committees.py   │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Automated Downloader & Deduplicator  │
                      │  - ai/acquisition/downloader.py      │
                      │  - ai/acquisition/deduplicator.py    │
                      │  - SHA-256 Content Hashing           │
                      │  - Quarantine Gate (invalid PDFs)    │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Structured Registries & Taxonomies   │
                      │  - data/registry/standards.jsonl     │
                      │  - data/registry/products.jsonl      │
                      │  - data/registry/qcos.jsonl          │
                      │  - data/registry/product_manuals.    │
                      │  - data/registry/sit.jsonl           │
                      │  - data/registry/laboratories.jsonl  │
                      │  - data/registry/licences.jsonl      │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │        Unified Knowledge Graph       │
                      │  - data/graph/nodes.jsonl            │
                      │  - data/graph/relationships.jsonl    │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Processing, Chunking & RAG Indexing  │
                      │  - Enriched Provenance Metadata      │
                      │  - Temporal Validity & Normative Force
                      │  - BM25 Sparse + Dense Vector Store  │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Phase 3 Grounding & Safety Gates     │
                      │  - Tier-0 IS Precedence              │
                      │  - Material Entity Compatibility     │
                      │  - Cross-Domain Trap Protection      │
                      │  - Atomic Claim Entailment (100%)    │
                      └──────────────────────────────────────┘
```

---

## 3. Detailed Breakdown of Existing Components

### A. Acquisition Framework (`ai/acquisition/`)
- `ai/acquisition/sources/base.py`: Uniform `BISSourceAdapter` abstract base class defining `discover() -> normalize() -> validate() -> emit()`.
- `ai/acquisition/sources/know_your_standard.py`: Scraper adapter for BIS KYS portal querying standards by number, title, and committee.
- `ai/acquisition/sources/product_manuals.py`: Adapter discovering sampling guidelines, test equipment, and grouping rules.
- `ai/acquisition/sources/sit.py`: Adapter parsing test frequencies, sample sizes, and inspection schedules.
- `ai/acquisition/sources/qco.py`: Adapter extracting mandatory certification orders, notifications, and issuing ministries.
- `ai/acquisition/sources/laboratories.py`: Adapter extracting BIS-recognized and NABL laboratories with test capabilities.
- `ai/acquisition/downloader.py` & `deduplicator.py`: Robust streaming HTTP downloader with SHA-256 deduplication and validation.
- `ai/acquisition/monitor.py`: Source freshness monitoring engine checking ETags and content hashes.

### B. Registries (`data/registry/`)
- `standards_catalog.jsonl` (663 records): High-level metadata (canonical ID, standard number, edition, title, status, department, committee).
- `products.jsonl` (560 records): Product canonical names, categories, aliases, and applicable Indian Standards.
- `relationships.jsonl` (2,266 edges): Active graph relations connecting products, standards, labs, amendments, SIT, and QCOs.
- `bis_sources.jsonl` (9 source definitions): Official portals for standards, manuals, QCOs, labs, CRS, etc.

### C. Chunking & Search Indexes (`ai/chunking/`, `ai/vectorstore/`)
- Chunks carry rich structural metadata (`document_id`, `standard_number`, `clause_number`, `page_start`, `page_end`, `normative_status`, `publication_date`, `edition`).
- `ai/vectorstore/hybrid_search.py`: Reciprocal Rank Fusion combining Chroma vector search, BM25 keyword matching, exact parameter inverted index, temporal filtering, and multi-factor RRF boosting.

---

## 4. Current Corpus Gaps & Deficiencies Identified

1. **Revisions & Amendments as Versioned Entities**:
   - Several historical revisions (e.g. 2008 vs 2024 editions) exist in raw files, but need formal versioning tables (`valid_from`, `valid_to`, `supersedes`, `superseded_by`) in `data/registry/amendments.jsonl` and `data/registry/standards.jsonl`.
2. **Dedicated Registries for Downstream Domains**:
   - While `relationships.jsonl` has 2,266 graph edges, standalone JSONL registries are needed for:
     - `data/registry/sources.jsonl` (comprehensive source catalog across all 18 BIS source types)
     - `data/registry/standards.jsonl` (master standards with full provenance)
     - `data/registry/amendments.jsonl` & `data/registry/gazette.jsonl`
     - `data/registry/product_manuals.jsonl`
     - `data/registry/sit.jsonl`
     - `data/registry/qcos.jsonl`
     - `data/registry/schemes.jsonl`
     - `data/registry/procedures.jsonl`
     - `data/registry/laboratories.jsonl` & `standard_lab_map.jsonl`
     - `data/registry/licences.jsonl`
     - `data/registry/crs/` (electronics registration)
     - `data/registry/hallmarking/` (standards, orders, jewellers, AHCs, HUID)
     - `data/registry/consumer/` (complaints, alerts, recalls, mark verification)
3. **Graph Materialization**:
   - `data/graph/nodes.jsonl` and `data/graph/relationships.jsonl` should formalize the 18 node types and 12 relationship types with strict provenance.
4. **Automated Coverage & Quality Auditing Scripts**:
   - Need dedicated `scripts/audit_corpus_coverage.py` and `scripts/audit_corpus_quality.py` to calculate exact coverage percentages, detect orphan records, and quarantine corrupt documents.
5. **Dynamic Data-Driven Benchmark Generator**:
   - The master benchmark generator should dynamically inspect all new registries to auto-generate hundreds/thousands of verified test cases across all new domains.

---

## 5. Architectural Reuse & Modification Strategy

| Component | Strategy | Actions |
|---|---|---|
| `BISSourceAdapter` (`ai/acquisition/sources/base.py`) | **REUSE & EXTEND** | Core adapter contract is solid; add adapters for Hallmarking, CRS, Consumer, Schemes, Procedures |
| `Downloader` & `Deduplicator` | **REUSE** | Keep SHA-256 hash checks and streaming HTTP client |
| `Quarantine Gate` (`ai/ingestion/quarantine.py`) | **REUSE & EXTEND** | Route invalid/corrupted PDFs into `data/quarantine/` |
| `Chunk Schema` (`ai/chunking/schema.py`) | **EXTEND** | Add `source_family`, `document_type`, `scheme_ids`, `qco_ids`, `product_manual_ids`, `sit_ids`, `laboratory_ids`, `licence_ids`, `authority_level` without breaking Phase 3 fields |
| `HybridSearchEngine` (`ai/vectorstore/hybrid_search.py`) | **REUSE & HARDEN** | Preserve Phase 3 safety gates (IS precedence, material compatibility, cross-domain trap) while indexing enriched metadata |
| `RAGPipeline` (`ai/rag/pipeline.py`) | **REUSE** | Maintain deterministic answer generation and verification |
