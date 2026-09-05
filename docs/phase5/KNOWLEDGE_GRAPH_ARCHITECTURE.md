# BIS Knowledge Graph Architecture (Phase 5)

**Document Version**: 1.0  
**Phase**: Phase 5 — Knowledge Graph Construction & Structured BIS Relationships  
**Scope**: Heterogeneous Graph Schema, Adjacency Indexing, and End-to-End Compliance Traversal  

---

## 1. System Overview

The BIS Knowledge Graph represents the unified relational backbone of the assistant. It bridges raw evidence units, standards catalogs, statutory orders, schemes, manuals, and test facilities into a queryable semantic graph.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                             PRODUCT ENTITY                                 │
│                       (e.g. Electric Ceiling Fans)                         │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │ COVERED_BY_STANDARD
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            INDIAN STANDARD                                 │
│                             (IS 374:2019)                                  │
└───┬─────────────┬─────────────┬─────────────┬──────────────┬───────────┬───┘
    │             │             │             │              │           │
    │ AMENDED_BY  │ HAS_MANUAL  │ HAS_SIT     │ TESTED_BY    │ CERTIFIED │ CONTAINS
    ▼             ▼             ▼             ▼              ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌──────┐
│ Amendment │ │  Product  │ │    SIT    │ │  Testing  │ │  Scheme  │ │Evidence│
│  Slip A1  │ │  Manual   │ │ Schedule  │ │Laboratories│ │ (Scheme-I│ │Units │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └──────────┘ └──────┘
      ▲
      │ MANDATES_CERTIFICATION_FOR
┌─────┴──────────────────────────────────────────────────────────────────────┐
│                      STATUTORY QUALITY CONTROL ORDER                       │
│      (Electrical Appliances Quality Control Order 2023 - DPIIT)            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Entities & Statistics

- **Total Nodes**: 488 (Products, Indian Standards, Amendments, QCOs, Schemes, Manuals, SIT Schedules, Laboratories, Licences, CRS Registrations, Hallmarking Centres, Evidence Units).
- **Total Edges**: 687 directed, typed, validated relationships.
- **Dangling Edges**: 0 (100% referential integrity).
- **Persistence Location**: `data/processed/knowledge_graph/`.
