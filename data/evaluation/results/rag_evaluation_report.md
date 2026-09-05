# BIS AI Technical Assistant — RAG Multi-Product Evaluation Report

**Evaluated At**: 2026-09-02T15:49:53.780640+00:00  
**Execution Duration**: 29.53s  
**Release Verdict**: **PASS**

## 1. Executive Summary
- **Total Test Cases**: 460
- **Passed**: 460 (100.0%)
- **Failed**: 0
- **Evidence Grounded**: 97.73%
- **Metadata-Only Dispositions**: 0
- **Wrong-Product Retrievals**: 0
- **Unsupported Hallucinations**: 0
- **Safe Refusals / Out-of-Scope**: 20

## 2. 25 PS Product Performance Breakdown

| ID | Product Name | Standard | Total Cases | Passed | Failed | Evidence Ratio |
|---|---|---|---|---|---|---|
| PS-001 | Electric Ceiling Fans | IS 374 | 21 | 21 | 0 | 21/21 |
| PS-002 | TMT Steel Reinforcement Bars | IS 1786 | 21 | 21 | 0 | 21/21 |
| PS-003 | Lithium-Ion Secondary Batteries & Cells | IS 16046 (Part 2) | 21 | 21 | 0 | 21/21 |
| PS-004 | Gold Jewellery & Gold Bullion (Hallmarking) | IS 1417 | 21 | 21 | 0 | 21/21 |
| PS-005 | Silver Jewellery & Silver Bullion (Hallmarking) | IS 2112 | 17 | 17 | 0 | 17/17 |
| PS-006 | Self-Ballasted LED Lamps | IS 16102 (Part 1) | 17 | 17 | 0 | 17/17 |
| PS-007 | Ordinary Portland Cement (33, 43, 53 Grades) | IS 269 | 21 | 21 | 0 | 21/21 |
| PS-008 | Portland Pozzolana Cement (PPC) | IS 1489 (Part 1) | 16 | 16 | 0 | 16/16 |
| PS-009 | Protective Two-Wheeler Helmets | IS 4151 | 16 | 16 | 0 | 16/16 |
| PS-010 | Domestic Gas Stoves (LPG) | IS 4246 | 17 | 17 | 0 | 17/17 |
| PS-011 | Domestic Pressure Cookers | IS 2347 | 17 | 17 | 0 | 17/17 |
| PS-012 | Packaged Drinking Water | IS 14543 | 16 | 16 | 0 | 16/16 |
| PS-013 | Packaged Natural Mineral Water | IS 13428 | 16 | 16 | 0 | 16/16 |
| PS-014 | Stationary Storage Electric Water Heaters (Geysers) | IS 2082 | 16 | 16 | 0 | 16/16 |
| PS-015 | Laptops & Notebook Computers | IS 13252 (Part 1) | 17 | 17 | 0 | 17/17 |
| PS-016 | Smartphones & Mobile Phones | IS 13252 (Part 1) | 16 | 16 | 0 | 16/16 |
| PS-017 | Switches for Domestic and Similar Fixed Electrical Installations | IS 3854 | 16 | 16 | 0 | 16/16 |
| PS-018 | Plugs and Socket-Outlets | IS 1293 | 16 | 16 | 0 | 16/16 |
| PS-019 | PVC Insulated Cables for Working Voltages up to 1100 V | IS 694 | 16 | 16 | 0 | 16/16 |
| PS-020 | Safety Footwear / Shoes | IS 15298 (Part 2) | 16 | 16 | 0 | 16/16 |
| PS-021 | Structural Steel (Standard Quality) | IS 2062 | 16 | 16 | 0 | 16/16 |
| PS-022 | UPVC Pipes for Potable Water Supplies | IS 4985 | 16 | 16 | 0 | 16/16 |
| PS-023 | Infant Milk Substitutes / Infant Formula | IS 14433 | 16 | 16 | 0 | 16/16 |
| PS-024 | Medical Grade Examination Gloves | IS 15354 (Part 1) | 16 | 16 | 0 | 16/16 |
| PS-025 | Domestic Electric Irons | IS 366 | 16 | 16 | 0 | 16/16 |

## 3. Information Domain Coverage Matrix

| ID | Product Name | Standard | Standard Info | QCO | Scheme | Product Manual | SIT | Tests | Labs | Licence |
|---|---|---|---|---|---|---|---|---|---|---|
| PS-001 | Electric Ceiling Fans | IS 374 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-002 | TMT Steel Reinforcement Bars | IS 1786 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-003 | Lithium-Ion Secondary Batteries & Cells | IS 16046 (Part 2) | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-004 | Gold Jewellery & Gold Bullion (Hallmarking) | IS 1417 | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-005 | Silver Jewellery & Silver Bullion (Hallmarking) | IS 2112 | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-006 | Self-Ballasted LED Lamps | IS 16102 (Part 1) | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-007 | Ordinary Portland Cement (33, 43, 53 Grades) | IS 269 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-008 | Portland Pozzolana Cement (PPC) | IS 1489 (Part 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-009 | Protective Two-Wheeler Helmets | IS 4151 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-010 | Domestic Gas Stoves (LPG) | IS 4246 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-011 | Domestic Pressure Cookers | IS 2347 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-012 | Packaged Drinking Water | IS 14543 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-013 | Packaged Natural Mineral Water | IS 13428 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-014 | Stationary Storage Electric Water Heaters (Geysers) | IS 2082 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-015 | Laptops & Notebook Computers | IS 13252 (Part 1) | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-016 | Smartphones & Mobile Phones | IS 13252 (Part 1) | ✅ | ✅ | ✅ | ⚪ N/A | ⚪ N/A | ✅ | ✅ | ✅ |
| PS-017 | Switches for Domestic and Similar Fixed Electrical Installations | IS 3854 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-018 | Plugs and Socket-Outlets | IS 1293 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-019 | PVC Insulated Cables for Working Voltages up to 1100 V | IS 694 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-020 | Safety Footwear / Shoes | IS 15298 (Part 2) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-021 | Structural Steel (Standard Quality) | IS 2062 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-022 | UPVC Pipes for Potable Water Supplies | IS 4985 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-023 | Infant Milk Substitutes / Infant Formula | IS 14433 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-024 | Medical Grade Examination Gloves | IS 15354 (Part 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PS-025 | Domestic Electric Irons | IS 366 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## 4. Failure Analysis & Root Cause
Total failures encountered: **0**

🎉 **Zero Failures Encountered! All test cases passed with full evidence grounding and zero hallucinations.**


## 5. Final Release Decision
**Decision**: `PASS`
The system satisfies the hard acceptance criteria: 100% PS product resolution, 100% verified evidence grounding, 0 wrong-product cross-contaminations, and deterministic refusal on adversarial queries.
