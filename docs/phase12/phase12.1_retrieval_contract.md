# Phase 12.1: Retrieval Contract

## 1. Retrieval Interface Specification
The RAG system's retrieval engine will expose an API contract designed for deterministic query execution. It will accept structured and semantic filters to avoid over-reliance on pure vector similarity.

### Input Request Structure
```json
{
  "query": "string (Natural language user query)",
  "filters": {
    "domain": "enum or null",
    "standard_number": "string or null",
    "product": "string or null",
    "laboratory_code_or_name": "string or null",
    "location": "string or null",
    "effective_date": "string (ISO Date) or null",
    "intent": "enum (e.g., FIND_FEE, FIND_PROCEDURE, CHECK_COMPLIANCE)"
  }
}
```

### Output Response Payload
The engine will return a ranked list of evidence blocks. Each block must carry its full provenance.

```json
{
  "results": [
    {
      "knowledge_id": "string",
      "relevance_score": "float",
      "authority": "enum",
      "freshness": "string (ISO Date or UNKNOWN)",
      "evidence_status": "enum (e.g., AVAILABLE_EVIDENCE)",
      "content_snippet": "string",
      "provenance": {
        "source_url": "string",
        "source_type": "string",
        "source_sha256": "string",
        "corpus_version": "string (e.g., 'v22')"
      },
      "citation_string": "string (Formatter for LLM generation)"
    }
  ],
  "system_status": "enum (SUCCESS, INSUFFICIENT_EVIDENCE, INACCESSIBLE_SOURCE)"
}
```

## 2. Target Query Classes
The retrieval architecture is explicitly designed to handle exact-evidence queries.

### Structured Relationships (Requires Hard Filtering)
- **Product compliance**: "What BIS standard applies to this product?"
- **QCO applicability**: "Which QCO makes this standard mandatory?"
- **Laboratory**: "Which BIS-recognized laboratories can test this standard?"
- **Lab scope**: "Does this laboratory have this IS in its scope?"

### Value Extraction (Requires Field-Level Precision)
- **Testing fee**: "What is the testing charge?"
- **Testing parameters**: "What tests are required?"
- **Temporal**: "What was applicable on a particular date?"

### Procedural / Semantic (Requires Vector + BM25)
- **Hallmarking**: "How do I get jewellery hallmarked?"
- **Consumer**: "How do I file a BIS complaint?"
- **Licence**: "How do I apply for a BIS licence?"
- **Regulations**: "Which regulation governs this?"

## 3. Empty States & Missing Evidence
If the retrieval index finds zero matching records for a given filter (e.g., an unmapped product or missing fee):
1. The engine MUST NOT return generic fallback documents just because they match the query semantically.
2. The engine MUST return a system status of `INSUFFICIENT_EVIDENCE` or `INACCESSIBLE_SOURCE` (if the underlying source was known to exist but failed to download).
3. The LLM must generate an answer stating the gap explicitly based on the `system_status`.
