# BIS AI Assistant Master Benchmark Report
**Execution Timestamp**: `2026-09-01T15:04:20.385113`

## Corpus Scope
- **Documents**: `110`
- **Unique Products**: `150`
- **Unique Standards**: `107`
- **Total Chunks**: `1961`

## Category Performance Breakdown

| Category | Total Cases | Passed | Accuracy | Safety Rate | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ambiguity` | 8 | 8 | **100.00%** | 100.0% | 0.1 ms |
| `certification` | 40 | 40 | **100.00%** | N/A | 115.7 ms |
| `chemicals_materials` | 198 | 198 | **100.00%** | N/A | 122.2 ms |
| `clause_questions` | 23 | 23 | **100.00%** | N/A | 40.5 ms |
| `construction_civil` | 114 | 114 | **100.00%** | N/A | 134.8 ms |
| `electrical` | 114 | 114 | **100.00%** | N/A | 142.2 ms |
| `electronics_it` | 198 | 198 | **100.00%** | N/A | 148.0 ms |
| `food_agriculture` | 120 | 120 | **100.00%** | N/A | 148.4 ms |
| `general` | 1374 | 1374 | **100.00%** | N/A | 130.6 ms |
| `mechanical_automotive` | 120 | 120 | **100.00%** | N/A | 154.6 ms |
| `medical_safety` | 150 | 150 | **100.00%** | 100.0% | 311.7 ms |
| `multilingual_hinglish` | 51 | 51 | **100.00%** | N/A | 116.8 ms |
| `precedence_collision` | 2 | 2 | **100.00%** | N/A | 43.5 ms |
| `precedence_explicit_is` | 107 | 107 | **100.00%** | N/A | 41.2 ms |
| `precedence_revision` | 20 | 20 | **100.00%** | N/A | 39.8 ms |
| `safety_cross_domain` | 17 | 17 | **100.00%** | 100.0% | 42.6 ms |
| `safety_unsupported` | 40 | 40 | **100.00%** | 100.0% | 29.4 ms |
| `technical_values` | 23 | 23 | **100.00%** | N/A | 66.1 ms |

## Severity & Safety Invariants
- 🔴 **Critical Failures**: `0` (Target: 0)
- 🟠 **High Failures**: `0`
- 🟡 **Medium Failures**: `0`
- ⚪ **Low Failures**: `0`

## Release Gate Status: **✅ PASSED**
- **Overall Accuracy**: `100.00%` (2719/2719)
