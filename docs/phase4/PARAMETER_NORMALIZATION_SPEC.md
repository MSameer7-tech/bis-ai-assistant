# Parameter & Unit Normalization Specification (Phase 4C)

**Document Version**: 1.0  
**Phase**: Phase 4 — Document Extraction, Normalization & Evidence Formatting  
**Scope**: SI Unit Conversions, Interval Normalization, and Cross-Standard Reference Standardization  

---

## 1. Unit Standardization

| Raw Unit Representation | Canonical Standardized Unit | Domain |
|---|---|---|
| `N/mm²`, `n/mm2`, `MPa`, `mega pascal` | `N/mm²` (or `MPa`, $1:1$ equivalence) | Mechanical Stress |
| `%`, `percent`, `pct` | `%` | Chemical / Elongation |
| `ppm`, `parts per million` | `ppm` | Impurity / Trace element |
| `mm`, `millimetre`, `mm.` | `mm` | Dimensional |
| `m³/min`, `m3/min`, `cu.m/min` | `m³/min` | Air Delivery |
| `W`, `Watt`, `watts` | `W` | Power |
| `V`, `Volt`, `volts` | `V` | Voltage |
| `Mohm`, `Megaohms`, `MΩ` | `MΩ` | Electrical Insulation |

---

## 2. Interval & Threshold Parsing

- `"415 to 500 MPa"` $\longrightarrow$ `{"min": 415.0, "max": 500.0, "unit": "N/mm²"}`
- `"Not less than 210 m³/min"` $\longrightarrow$ `{"min": 210.0, "max": null, "unit": "m³/min"}`
- `"Shall not exceed 0.040%"` $\longrightarrow$ `{"min": null, "max": 0.040, "unit": "%"}`
