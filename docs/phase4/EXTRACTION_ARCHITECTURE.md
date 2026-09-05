# Document Extraction & Evidence Formatting Architecture

**Document Version**: 1.0  
**Phase**: Phase 4 — Document Extraction, Normalization & Evidence Formatting  
**Scope**: Multi-Format Parsing, Normative Clause Hierarchy, Table Extraction, and Atomic Evidence Units  

---

## 1. Pipeline Overview

Phase 4 transforms raw immutable PDF, HTML, and JSON files from `data/raw/immutable/` into atomic, structured, cryptographically anchored **Evidence Units** (`data/processed/evidence_units/`).

```
       IMMUTABLE RAW STORAGE (data/raw/immutable/<doc_id>/)
                              │
                              ▼
      [4A. MULTI-FORMAT EXTRACTION] (document_extractor.py)
      Extracts text, hierarchy, clauses, tables from PDF/HTML/JSON
                              │
                              ▼
      [4B. REQUIREMENT & ENTITY PARSING] (requirement_extractor.py)
      Extracts mandatory provisions, physical/chemical ranges
                              │
                              ▼
      [4C. NORMALIZATION] (normalizer.py, table_normalizer.py)
      Standardizes units (MPa, N/mm², %), normalizes numeric ranges
                              │
                              ▼
      [4D. EVIDENCE UNIT FORMULATION] (evidence_unit_builder.py)
      Generates typed EvidenceUnit records with citation anchors
                              │
                              ▼
      [4E. AUTHORITATIVE MANIFEST] (extraction_manifest.json)
```

---

## 2. Core Principles

1. **Zero Data Loss on Clauses**: Standard specifications retain exact clause numbers (`1. Scope`, `4.1`, `4.2`, `5.1.2`) and verbatim legal text.
2. **2D Tabular Grid Preservation**: Tables retain column headers, row alignments, unit labels, and numerical limit ranges.
3. **Cryptographic Provenance**: Every Evidence Unit links back to its parent raw document's SHA-256 digest and carries its own SHA-256 content hash.
4. **Citation Anchors**: Every unit has a human-readable and machine-verifiable citation anchor (e.g. `IS 1786:2008, Clause 4.2 (Mechanical Properties)`).
