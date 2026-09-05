# Problem Statement Scope Boundaries & Non-Specifications

**Document Version**: 1.1  
**Phase**: Phase 1 — SIH PS Requirements & System Scope  
**Purpose**: Explicitly define what the Smart India Hackathon Problem Statement does NOT specify to prevent engineering over-fitting and false assumptions.

---

## 1. What the Problem Statement Does NOT Specify

To maintain engineering rigor and avoid hallucinating constraints, we document explicitly that the provided SIH Problem Statement does **NOT** specify:

1. **A Fixed Number of Products**: The PS does not restrict the assistant to 10, 25, 50, or 100 products. The assistant must be architecturally designed as a general-purpose, scalable regulatory system capable of covering the full breadth of Indian Standards.
2. **A Fixed List of 25 Products**: The 25 commodities used in our benchmark represent a **Representative Product Benchmark**, not an exhaustive or mandated product limit.
3. **Specific Indian Standards for Each Product**: The PS requires the assistant to recommend and identify standards dynamically from authorized sources, rather than hardcoding static standard lists.
4. **A Specific Large Language Model (LLM)**: The PS is vendor-neutral and does not mandate Gemini, Claude, LLaMA, or OpenAI.
5. **A Specific Vector Database**: The PS does not mandate ChromaDB, Pinecone, Qdrant, Milvus, or Weaviate.
6. **A Specific Embedding Model**: The PS does not mandate a specific embedding dimensionality or vendor embedding model.
7. **A Specific Programming Language / Stack**: The PS does not mandate Python, Rust, Go, Node.js, Next.js, or React.
8. **A Specific Relational or Graph Database**: The PS does not mandate SQLite, PostgreSQL, Neo4j, or NetworkX.
9. **A Specific Fixed Number of Documents or Chunks**: The system's scale is determined by the corpus requirements of the domain, not an arbitrary document count.

---

## 2. Distinction: Broad Corpus Architecture vs Representative Benchmark

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CORPUS & BENCHMARK TERMINOLOGY                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 1. Broad Authorized Knowledge Base (Phases 2–4):                             ║
║    - Open, extensible regulatory registry spanning all BIS source families. ║
║    - Dynamically ingests standards, QCOs, manuals, SITs, labs, licences.    ║
║                                                                              ║
║ 2. Representative Product Benchmark (Phase 9):                               ║
║    - A curated benchmark suite (e.g., 25 diverse products × 460 test cases) ║
║      used for regression testing, precision auditing, and gate verification. ║
║    - Serves as proof-of-capability, NOT as the system's boundary limit.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Engineering Implications

- **Decoupled Architecture**: All pipelines (discovery, ingestion, graph traversal, retrieval) must operate on generic data schemas (`StandardRecord`, `QCORecord`, `ProductManualRecord`, `EvidenceRecord`) rather than product-specific hardcodes.
- **Dynamic Extensibility**: Ingesting a new standard or gazette order must be a zero-code pipeline operation.
- **Safe Out-of-Scope Handling**: The system must cleanly recognize whether a requested topic is governed by BIS, providing safe refusal when queried on non-BIS domains (e.g. quantum processors, aerospace alloys).
