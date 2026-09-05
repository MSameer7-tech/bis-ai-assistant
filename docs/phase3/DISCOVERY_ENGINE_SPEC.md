# Discovery Engine Specification (Phase 3A)

**Document Version**: 1.0  
**Phase**: Phase 3 — Bulk BIS Data Discovery & Acquisition  
**Scope**: Specifications of Discovery Mechanisms Across Official Source Families  

---

## 1. Discovery Protocols by Source Family

1. **Indian Standards (`SRCF-001`)**:
   - Queries `SRC-001` (Know Your Standard) and `SRC-002` (Publishing Portal).
   - Extracts standard number, multi-part designator, publication year, title, and product scope.
2. **Amendments & Revisions (`SRCF-002`)**:
   - Queries `SRC-003` (Amendments Registry).
   - Links amendment slip numbers to parent standard canonical IDs.
3. **Quality Control Orders (`SRCF-003`)**:
   - Queries `SRC-004` (The Gazette of India) and `SRC-005` (Compulsory Certification Directory).
   - Extracts issuing ministry acronym, S.O. gazette number, and enforcement dates.
4. **Product Manuals (`SRCF-004`)**:
   - Queries `SRC-006` (Product Manuals Directory).
   - Discovers grouping guidelines and factory testing facility requirements.
5. **Schemes of Inspection and Testing (`SRCF-005`)**:
   - Queries `SRC-007` (SIT Directory).
   - Discovers routine and acceptance testing schedules.
6. **Conformity Assessment Schemes (`SRCF-006`)**:
   - Queries `SRC-008` (Product Certification Overview) and `SRC-009` (CRS Portal).
7. **Licences & Registrations (`SRCF-007`)**:
   - Queries `SRC-010` (Manakonline Licence Search) and `SRC-011` (CRS Registrations).
8. **Testing Laboratories (`SRCF-008`)**:
   - Queries `SRC-012` (Central/Regional Labs) and `SRC-013` (Recognized Labs).
9. **Hallmarking Ecosystem (`SRCF-009`)**:
   - Queries `SRC-014` (Hallmarking Regulations) and `SRC-015` (Manakonline Hallmarking).
10. **Consumer Services & BIS Care (`SRCF-010`)**:
    - Queries `SRC-016` (Consumer Affairs).
11. **FAQs & Publications (`SRCF-011`)**:
    - Queries `SRC-017` (Publications & FAQs).
12. **Acts & Regulations (`SRCF-012`)**:
    - Queries `SRC-018` (Acts, Rules & Regulations Portal).

---

## 2. Output Candidate Contract

All discovered candidates conform to the Pydantic model in `ai/acquisition/discovery_engine.py`:
- `candidate_id`: Unique identifier (e.g. `CAND-IS-1786-2008`)
- `source_id`: Origin endpoint (e.g. `SRC-001`)
- `source_family_id`: Governing family (e.g. `SRCF-001`)
- `source_url`: Download / access URL
- `discovered_from_url`: Parent catalog entry
- `document_type`: Document classification
- `title`: Extracted document title
- `discovery_method`: Protocol code
- `discovered_at`: ISO-8601 UTC timestamp
