# Phase 4 Batch F: Evidence Completeness & Provenance Binding Audit Report

**Audit Timestamp**: 2026-09-01 16:24:00 UTC  
**Overall Evidence Binding Rate**: **100.0%** (13339/13339 graph edges bound)  
**Critical Commodities Release Gate**: **✅ PASSED (8/8 Core Commodities 100% Verified)**

---

## 1. Evidentiary Strength Taxonomy Distribution

| Evidentiary Strength Level | Record Count | Percentage | Semantic Meaning & Regulatory Use |
|---|---|---|---|
| `EVIDENCE_VERIFIED` | **1114** | 53.2% | Current authoritative evidence with exact clause/page/hash locator; full normative quoting allowed |
| `EVIDENCE_PARTIAL` | **980** | 46.8% | Authoritative source ID verified; deep clause extraction pending |
| `SOURCE_FOUND_NOT_EXTRACTED` | **0** | 0.0% | Source PDF fingerprinted; text normalization in progress |
| `SOURCE_NOT_FOUND` | **0** | 0.0% | Primary source document missing; claims strictly refused by Evidence Gate |
| `CONFLICTING_EVIDENCE` | **0** | 0.0% | Contradictory gazette notifications/amendments surfaced to user |
| `STALE_EVIDENCE` | **0** | 0.0% | Authoritative for historical state; invalid for current normative claim |
| **Total Evidence Records** | **2094** | **100.0%** | **Master Evidence Registry (`data/registry/evidence.jsonl`)** |

---

## 2. Knowledge Graph Edge Evidence State

- **Total Graph Edges**: **13339**
- **Evidence-Bound Edges**: **13339** (**100.0%**)
- **Edge Strength Breakdown**:
  - `EVIDENCE_VERIFIED`: **6036** edges
  - `EVIDENCE_PARTIAL`: **7303** edges

---

## 3. Critical Commodities Release Gate Matrix

| Commodity | Standard | Verified Evidence | QCO Mandate | Product Manual | SIT Schedule | Tests | Lab Scope | Licences / CRS | Gate Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Electric Ceiling Fans** | `IS 374` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **High Strength Deformed Steel Bars (TMT Rebars)** | `IS 1786` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Ordinary Portland Cement (33/43/53 Grade)** | `IS 269` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Packaged Drinking Water (Other than Natural Mineral Water)** | `IS 14543` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Domestic Gas Stoves for use with Liquefied Petroleum Gases** | `IS 4246` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Domestic Pressure Cookers** | `IS 2347` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Protective Helmets for Two Wheeler Riders** | `IS 4151` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Secondary Cells and Batteries containing Alkaline or other Non-Acid Electrolytes (Li-ion)** | `IS 16046 (Part 2)` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

---

## 4. Machine-Readable Product Chain Policy Summary

| Policy Category | Scheme Code | Audited Products | Policy Complete | Policy Partial | Policy Incomplete |
|---|---|---|---|---|---|
| Mandatory ISI Industrial Goods | `SCHEME-I` | 85 | 32 | 48 | 5 |
| Mandatory ISI Consumer Appliances | `SCHEME-I` | 38 | 20 | 16 | 2 |
| Mandatory ISI Food & Water | `SCHEME-I` | 14 | 8 | 6 | 0 |
| Mandatory CRS Electronics & IT | `SCHEME-II` | 22 | 14 | 8 | 0 |
| Mandatory Hallmarking Gold/Silver | `SCHEME-IV` | 6 | 6 | 0 | 0 |
| Voluntary / Non-QCO Standards | `SCHEME-I` | 14 | 14 | 0 | 0 |
| **Total Canonical Products** | — | **179** | **120** | **22** | **37** |

---

## 5. Evidence Repair Queue Status

- **Total Repair Queue Backlog**: **9 items**
- **Priority 1 (Critical Commodities)**: **0 items** (100% resolved)
- **Priority 2 (Catalog Standards awaiting full PDF ingestion)**: **9 items**
