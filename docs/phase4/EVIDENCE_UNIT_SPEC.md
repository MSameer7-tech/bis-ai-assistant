# Evidence Unit Data Specification (Phase 4D)

**Document Version**: 1.0  
**Phase**: Phase 4 — Document Extraction, Normalization & Evidence Formatting  
**Scope**: Schema, Attributes, and Types for Atomic Evidence Containers  

---

## 1. Evidence Unit Schema

Every Evidence Unit conforms to the Pydantic data model in `ai/processing/evidence_unit_builder.py`:

```json
{
  "evidence_unit_id": "EV-IS-1786-2008-CL-4.2",
  "document_id": "IS-1786-2008",
  "document_family_id": "IS-1786",
  "document_type": "INDIAN_STANDARD",
  "authority_class": "PRIMARY_NORMATIVE",
  "section_or_clause": "4.2",
  "heading": "Mechanical Properties",
  "content_text": "The mechanical properties of high strength deformed bars and wires shall conform to Table 2...",
  "content_type": "CLAUSE",
  "structured_data": {
    "clause_type": "REQUIREMENT"
  },
  "parent_raw_sha256": "0c336cf23c23f277359f6565e33f0c993d155b24b2f9c196a45f71341fe301f0",
  "unit_content_sha256": "8a7b6c5d4e3f...",
  "citation_anchor": "IS-1786-2008, Clause 4.2 (Mechanical Properties)",
  "page_number": null,
  "created_at": "2026-09-02T01:06:04Z"
}
```

---

## 2. Content Type Classifications

- `CLAUSE`: Normative requirement clause.
- `TABLE`: Tabular chemical, physical, or frequency schedule.
- `DEFINITION`: Technical definition or terminology entry from Clause 3.
- `TEST_METHOD`: Standardized testing procedure and laboratory verification protocol.
- `SAMPLING_PLAN`: Lot sizing and sampling frequency rules.
- `MARKING_RULE`: Standard mark (ISI / CRS / Hallmark) application and tagging guidelines.
- `STATUTORY_ORDER`: Legal enforcement clauses from Gazette Quality Control Orders.
