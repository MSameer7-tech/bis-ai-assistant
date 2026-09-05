# Compliance Chain Traversal Specification (Phase 5C)

**Document Version**: 1.0  
**Phase**: Phase 5 — Knowledge Graph Construction & Structured BIS Relationships  
**Scope**: Multi-Hop Graph Traversal, Mandatory Status Resolution, and Laboratory Mapping  

---

## 1. Compliance Chain Traversal Algorithm

When answering regulatory and technical inquiries, the assistant queries the graph traversal interface (`KnowledgeGraphTraversal.get_compliance_chain()`):

```python
chain = traversal.get_compliance_chain("Electric Ceiling Fans")
```

The algorithm executes the following multi-hop path:
1. **Product Entity Resolution**: Matches user query to `NodeType.PRODUCT` via exact ID, name, or alias list.
2. **Governing Standard Resolution**: Follows `COVERED_BY_STANDARD` edge to target `NodeType.INDIAN_STANDARD`.
3. **Statutory Mandate Evaluation**: Traverses incoming `MANDATES_CERTIFICATION_FOR` edges from `NodeType.QCO`. If an active QCO exists, marks `is_mandatory = True` and binds the issuing ministry order.
4. **Conformity Scheme Binding**: Follows `CERTIFIED_UNDER_SCHEME` edge to determine whether the product requires Scheme-I (ISI Mark), Scheme-II (CRS), Scheme-IV (Hallmark), or Scheme-X (MSME).
5. **Operational Guidance Linking**: Follows `HAS_PRODUCT_MANUAL` and `HAS_SIT_SCHEDULE` to fetch factory testing schedules.
6. **Testing Facilities Lookup**: Follows `TESTED_BY_LABORATORY` to fetch all BIS-recognized labs.
7. **Clause Evidence Retrieval**: Follows `CONTAINS_EVIDENCE_UNIT` to fetch chemical, mechanical, and safety requirements.
