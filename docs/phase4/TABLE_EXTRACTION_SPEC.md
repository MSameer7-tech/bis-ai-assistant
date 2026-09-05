# Table Extraction & Numerical Structure Specification (Phase 4B & 4C)

**Document Version**: 1.0  
**Phase**: Phase 4 — Document Extraction, Normalization & Evidence Formatting  
**Scope**: Tabular Structure Representation and Parameter Extraction  

---

## 1. 2D Tabular Grid Model

Tables are extracted with full cell grid integrity:
- `headers`: List of column header names (e.g. `["Grade", "Carbon Max (%)", "Sulphur Max (%)"]`).
- `rows`: 2D matrix of cell text values aligned by column index.
- `table_number`: Explicit table designation (e.g. `Table 1`, `Table 2`).
- `title`: Table caption.

---

## 2. Parameter Normalization Rules

- Chemical tolerances: Values like `"0.040 Max"` normalized to `{"parameter": "Sulphur", "max_value": 0.040, "unit": "%"}`.
- Mechanical limits: Proof stress and tensile values like `"500.0 N/mm² Min"` normalized to `{"parameter": "0.2% Proof Stress", "min_value": 500.0, "unit": "N/mm²"}`.
- Elongation values: Standard percentage gauges normalized to `{"parameter": "Elongation", "min_value": 16.0, "unit": "%"}`.
