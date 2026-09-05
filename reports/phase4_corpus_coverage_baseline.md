# Phase 4 Corpus Coverage Baseline & Evidence Chain Audit (Batch C)

**Generated**: 2026-09-01T16:24:05.009762+00:00  
**Status**: Authoritative Batch C Certification & Testing Knowledge Established  
**Scope**: Complete Evidence Chain across Standards, Products, QCOs, Schemes, Manuals, SIT, Tests, and Procedures.

---

## 1. Executive Summary & Inventory Counts

- **Raw PDFs (`data/raw/`)**: **144** files
- **Processed JSONs (`data/processed/`)**: **110** files
- **Production Chunks (`data/chunks/`)**: **3922** chunks
- **Standards Registry (`data/registry/standards.jsonl`)**: **643** standards
- **Unique Canonical Products**: **179** products (560 search records)
- **Statutory QCOs (`data/registry/qcos.jsonl`)**: **160** QCO orders
- **Product Manuals (`data/registry/product_manuals.jsonl`)**: **109** manuals
- **Scheme of Inspection & Testing (`data/registry/sit.jsonl`)**: **108** schedules
- **Normalized Tests (`data/registry/tests.jsonl`)**: **109** discrete test entities
- **Conformity Assessment Schemes (`data/registry/schemes.jsonl`)**: **12** schemes
- **Certification Procedures (`data/registry/procedures.jsonl`)**: **28** procedures
- **Knowledge Graph Edges (`data/registry/relationships.jsonl`)**: **13339** edges

### Product Evidence Classification Breakdown

| Classification Level | Product Count | Percentage | Definition |
|---|---|---|---|
| **COMPLETE** | **87** | 15.5% | Full evidence chain: Standard + Normative Document + QCO/Scheme + Manual/SIT + Tests + Procedure |
| **PARTIAL** | **439** | 78.4% | Standard mapped with document backing, QCO, or SIT, but awaiting additional lab/surveillance records |
| **STANDARD_ONLY** | **34** | 6.1% | Standard number mapped from catalog, raw document pending |
| **PRODUCT_ONLY** | **0** | 0.0% | Unmapped product name |

---

## 2. 10-Source Family Coverage Matrix

| Knowledge Dimension | Source ID | Tier | Discovered | Accessible | Acquired | Parsed | Normalized | Indexed | Graph-Mapped | Evidence-Backed |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Indian Standards | `BIS-STANDARDS` | TIER_1A | 663 | 643 | 110 | 110 | 220 | 107 | 643 | 107 |
| 2. Products & Specifications | `BIS-KYS / CMD` | TIER_1A | 560 | 560 | 560 | 560 | 560 | 560 | 560 | 150 |
| 3. Amendments & Corrigenda | `BIS-AMENDMENTS` | TIER_1A | 204 | 204 | 204 | 204 | 204 | 204 | 204 | 204 |
| 4. Gazette Notifications | `BIS-GAZETTE` | TIER_1B | 45 | 45 | 45 | 45 | 45 | 45 | 45 | 45 |
| 5. Quality Control Orders (QCOs) | `BIS-QCO` | TIER_1B | 160 | 160 | 160 | 160 | 160 | 160 | 160 | 16 |
| 6. Product Manuals (PMs) | `BIS-PRODUCT-MANUALS` | TIER_1C | 109 | 109 | 109 | 109 | 109 | 109 | 109 | 105 |
| 7. Scheme of Inspection & Testing (SIT) | `BIS-SIT` | TIER_1C | 108 | 108 | 108 | 108 | 108 | 108 | 108 | 105 |
| 8. Normalized Test Entities | `BIS-TESTS` | TIER_1C | 109 | 109 | 109 | 109 | 109 | 109 | 109 | 105 |
| 9. Conformity Schemes | `BIS-SCHEMES` | TIER_2 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| 10. Certification Procedures | `BIS-PROCEDURES` | TIER_2 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 28 |
| 11. Testing Laboratories (BIS & NABL Network) | `BIS-LABORATORIES` | TIER_2 | 840 | 840 | 840 | 840 | 840 | 840 | 840 | 20 |
| 12. Conformity Licences (CM/L Manufacturers) | `BIS-LICENCES` | TIER_2 | 450 | 450 | 450 | 450 | 450 | 450 | 450 | 450 |
| 13. Compulsory Registration Scheme (CRS) | `BIS-CRS` | TIER_2 | 78 | 78 | 78 | 78 | 78 | 78 | 78 | 78 |
| 14. Hallmarking & Precious Metals (AHC Network) | `BIS-HALLMARKING` | TIER_2 | 55 | 55 | 55 | 55 | 55 | 55 | 55 | 55 |
| 15. Consumer Services & Grievance Redressal (BIS Care) | `BIS-CONSUMER` | TIER_2 | 34 | 34 | 34 | 34 | 34 | 34 | 34 | 34 |

---

## 3. Graph Relationship Type Breakdown

| Relationship Edge Type | Edge Count | Target Entity Description |
|---|---|---|
| `TESTED_AT_LABORATORY` | **2947** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `ACCREDITED_FOR_STANDARD` | **2449** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `ALIAS_OF_PRODUCT` | **1531** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `APPLIES_TO_PRODUCT` | **1335** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `GOVERNED_BY_STANDARD` | **885** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `COVERS_STANDARD` | **637** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `LICENSED_UNDER` | **450** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `OPERATED_BY` | **450** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `MANDATED_BY_QCO` | **315** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `HALLMARKED_AT_AHC` | **219** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `RECOGNIZED_FOR_STANDARD` | **219** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `HAS_PRODUCT_MANUAL` | **214** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `HAS_SIT` | **213** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `HAS_AMENDMENT` | **210** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `MAINTAINED_BY_COMMITTEE` | **210** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `CERTIFIED_UNDER` | **179** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `CONTAINS_SIT` | **109** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `PRESCRIBES_TEST` | **109** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `REQUIRES_TEST` | **108** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `SPECIFIED_IN_SIT` | **108** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `CRS_REGISTERED` | **78** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `BRAND_OWNER` | **78** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `MANDATES_PRODUCT` | **63** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `LOCATED_IN_DISTRICT` | **55** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `ENFORCES_STATUTORY_PROVISION` | **38** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `APPLIES_TO_STANDARD` | **34** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `SERVICED_BY` | **34** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `USES_PROCEDURE` | **28** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `APPLIES_TO_SCHEME` | **28** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |
| `ALLOWS_PURITY_GRADE` | **6** | Connected across standards, products, QCOs, schemes, manuals, SIT, tests, procedures |

---

## 4. Product Evidence Chain Coverage Matrix

| Canonical Product Name | Applicable Standard | QCO Mandate | Scheme | Product Manual | SIT Schedule | Discrete Tests | Procedure | Chain Status |
|---|---|---|---|---|---|---|---|---|
| Electric Ceiling Fans | `IS 374` | ✅ Mandatory | ✅ SCHEME-I | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | `COMPLETE` |
| Table Type Electric Fans | `IS 555` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Propeller Type AC Ventilating and Exhaust Fans | `IS 2312` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Safety of Household Electrical Appliances - General | `IS 302 (PART 1)` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Electric Irons | `IS 366` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Stationary Storage Type Electric Water Heaters | `IS 2082` | ✅ Mandatory | ✅ SCHEME-I | ✅ Yes | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Electric Immersion Water Heaters | `IS 368` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| PVC Insulated Cables for Working Voltages up to 1100V | `IS 694` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Crosslinked Polyethylene Insulated Cables for Voltages up to 1100V | `IS 7098 (PART 1)` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Aluminium Conductors for Overhead Transmission (ACSR) | `IS 398 (PART 2)` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Switches for Domestic and Similar Fixed Electrical Installations | `IS 3854` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Plugs and Socket-Outlets for Domestic and Similar Purposes | `IS 1293` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Rigid Steel Conduits for Electrical Wiring | `IS 1653` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Residual Current Operated Circuit-Breakers without Integral Overcurrent Protection (RCCB) | `IS 12640 (PART 1)` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Electric Kettles and Liquid Heaters | `IS 302 (PART 2/SEC 15)` | ✅ Mandatory | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Room Air Conditioners | `IS 1391 (PART 1)` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `STANDARD_ONLY` |
| Frost-Free Refrigerating Appliances | `IS 15750` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `STANDARD_ONLY` |
| Self-Ballasted LED Lamps for General Lighting — Safety | `IS 16102 (PART 1)` | ✅ Mandatory | ✅ SCHEME-II | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Self-Ballasted LED Lamps for General Lighting — Performance | `IS 16102 (PART 2)` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Luminaires — Particular Requirements: Fixed General Purpose Luminaires | `IS 10322 (PART 5/SEC 1)` | ⚪ Voluntary | ✅ SCHEME-I | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `STANDARD_ONLY` |
| Lamp Controlgear — AC/DC Supplied Electronic Controlgear for LED Modules | `IS 15885 (PART 2/SEC 13)` | ✅ Mandatory | ✅ SCHEME-II | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes (Lithium Systems) | `IS 16046 (PART 2)` | ✅ Mandatory | ✅ SCHEME-II | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | `COMPLETE` |
| Secondary Cells and Batteries Containing Alkaline Electrolytes (Nickel Systems) | `IS 16046 (PART 1)` | ✅ Mandatory | ✅ SCHEME-II | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Compulsory Registration Order (CRO / CRS) | `IS 13252 (PART 1)` | ✅ Mandatory | ✅ SCHEME-II | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
| Information Technology Equipment — Safety | `IS 13252 (PART 1)` | ✅ Mandatory | ✅ SCHEME-II | ❌ Pending | ❌ Pending | ❌ Pending | ✅ Yes | `PARTIAL` |
