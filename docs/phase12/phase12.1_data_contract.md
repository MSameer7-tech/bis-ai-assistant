# Phase 12.1: Data Contract

## 1. Derived Knowledge Schema (Versioned)
To support hybrid retrieval, raw JSONL records are mapped into the following derived schema. **The v22 schema remains immutable.** This schema applies strictly to the Derived Knowledge Layer.

```json
{
  "knowledge_id": "string (UUID or deterministic hash of content + source)",
  "source_record_id": "string (Foreign key to v22 record_id)",
  "corpus_version": "string (e.g., 'v22')",
  "domain": "enum (LABORATORIES, HALLMARKING, LICENCES, CONSUMER, FAQ, etc.)",
  "knowledge_type": "enum (DOCUMENT, STANDARD, PRODUCT, LABORATORY, FEE, QCO, PROCEDURE)",
  "title": "string (Clear, canonical title)",
  "subject": "string (Primary topic, e.g., 'Testing Fees for IS 1234')",
  "content": "string (The core knowledge payload for vectorization)",
  "entities": {
    "is_numbers": ["string"],
    "products": ["string"],
    "lab_codes": ["string"]
  },
  "relationships": [
    {
      "target_knowledge_id": "string",
      "relationship_type": "enum"
    }
  ],
  "authority": "enum (TIER_1_NORMATIVE, TIER_1_OFFICIAL_OPERATIONAL, TIER_2_OFFICIAL_EXPLANATORY)",
  "source": {
    "url": "string",
    "sha256": "string",
    "type": "string"
  },
  "provenance": {
    "status": "enum (COMPLETE, INCOMPLETE, MISSING)",
    "retrieved_at": "timestamp"
  },
  "effective_date": "string (ISO Date or UNKNOWN)",
  "validity": "string (ISO Date or UNKNOWN)",
  "supersession": {
    "is_superseded": "boolean",
    "superseded_by": "knowledge_id or UNKNOWN"
  },
  "accessibility": "enum (ACCESSIBLE, INACCESSIBLE)",
  "evidence_status": "enum (AVAILABLE_EVIDENCE, INSUFFICIENT_EVIDENCE, NOT_ESTABLISHED)"
}
```

## 2. Relationship Contract
Relationships between knowledge nodes are strictly evidence-based. If evidence is missing, the relationship must NOT be inferred or synthetically generated.

**Valid Relationships:**
- `PRODUCT -> STANDARD`: Explicit mapping from BIS product manual or QCO.
- `LABORATORY -> STANDARD`: Explicit testing capability listed in LIMS scope.
- `LABORATORY -> SCOPE`: LIMS structural hierarchy.
- `SCOPE -> TEST_PARAMETER`: Detailed test capability.
- `SCOPE -> TEST_METHOD`: Recognized testing method.
- `SCOPE -> TESTING_FEE`: Explicit fee associated with a test/standard.
- `STANDARD -> QCO`: Explicit Quality Control Order mandating an IS.
- `QCO -> EFFECTIVE_DATE`: The date a QCO takes effect.
- `STANDARD -> CERTIFICATION_SCHEME`: Scheme I, Scheme II, etc.
- `DOCUMENT -> SUPERSEDES_DOCUMENT`: Explicit text stating "supersedes X".

**Missing Evidence Rule:**
If a relationship cannot be established, its value resolves to `UNKNOWN` or `NOT_ESTABLISHED`. The absence of a relationship does not mean the relationship is impossible, only that the corpus lacks authoritative evidence for it.
