# Source Priority & Conflict Resolution Policy

**Document Version**: 1.0  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: Precedence Rules for Resolving Cross-Source Discrepancies  

---

## 1. Regulatory Precedence Hierarchy

When answering user queries where multiple source families mention a commodity or requirement, the reasoning engine must apply strict precedence:

```
[Level 1: STATUTORY / GAZETTE QCO (SRCF-003, SRCF-012)]
       │ (Governs whether certification is legally mandatory, penalty rules, effective dates)
       ▼
[Level 2: INDIAN STANDARDS SPECIFICATIONS (SRCF-001, SRCF-002, SRCF-009A)]
       │ (Governs technical limits, chemistry, dimensions, test parameters)
       ▼
[Level 3: SCHEMES OF INSPECTION & TESTING (SRCF-005)]
       │ (Governs routine test frequencies, sample batches, factory testing levels)
       ▼
[Level 4: BIS PRODUCT MANUALS & LAB REGISTERS (SRCF-004, SRCF-008)]
       │ (Governs product grouping, factory equipment guidelines, lab facilities)
       ▼
[Level 5: BIS INFORMATIVE FAQs & GUIDES (SRCF-011)]
         (Governs general procedural explanations and non-binding advice)
```

---

## 2. Conflict Resolution Principles

1. **QCO vs Standard Scope**: If an Indian Standard states *"This standard is voluntary in nature"*, but a Central Ministry Quality Control Order (QCO) published in the Gazette mandates compliance, the **QCO takes absolute legal precedence** (Certification is Mandatory).
2. **Amendment vs Base Standard**: An active Amendment Slip takes absolute precedence over original base standard text for modified clauses.
3. **Manual vs FAQ**: An official BIS Product Manual takes precedence over general public FAQ brochures.
