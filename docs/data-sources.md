# Pilot Dataset Specification: LED Lamps & Bulbs

This document specifies the authoritative pilot dataset for **LED lamps / LED bulbs**. It establishes the complete vertical slice of standards, QCOs, certification schemes, testing parameters, and laboratory scopes.

---

## 1. Pilot Domain Scope & Product Definition

* **Product Category**: Self-Ballasted LED Lamps for General Lighting Services
* **Voltage Rating**: Up to 250V a.c. 50Hz
* **Caps / Bases**: B22d, E27, E14
* **Common Industry Names**: LED bulb, 9W LED lamp, retro-fit LED bulb, self-ballasted LED lamp

---

## 2. Targeted Authoritative Knowledge Assets

```text
                                PILOT DATASET: LED LAMPS
                                           │
         ┌──────────────────┬──────────────┴─────┬─────────────────┬──────────────────┐
         ▼                  ▼                    ▼                 ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ Safety Standard │ │ Performance     │ │ Regulatory QCO  │ │ CRS Scheme  │ │ Testing & Lab   │
│ IS 16102 (Pt 1) │ │ IS 16102 (Pt 2) │ │ (MeitY CRO)     │ │ Guidelines  │ │ Scopes          │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘ └─────────────────┘
```

---

### Category A: Core Indian Standards

| Document ID | Official Standard Number | Title / Scope | Authority |
| :--- | :--- | :--- | :--- |
| **DOC-IS-16102-1** | `IS 16102 (Part 1) : 2012` | *Self-Ballasted LED Lamps for General Lighting Services — Part 1: Safety Requirements* | Tier 1B (Normative) |
| **DOC-IS-16102-2** | `IS 16102 (Part 2) : 2012` | *Self-Ballasted LED Lamps for General Lighting Services — Part 2: Performance Requirements* | Tier 1B (Normative) |
| **DOC-IS-15885-2-13** | `IS 15885 (Part 2/Sec 13) : 2012` | *Lamp Controlgear — Part 2-13: Particular Requirements for d.c. or a.c. Supplied Electronic Controlgear for LED Modules* (Normative reference for LED drivers) | Tier 1B (Normative) |
| **DOC-IS-16103-1** | `IS 16103 (Part 1) : 2012` | *Led Modules for General Lighting — Part 1: Safety Requirements* | Tier 1B (Normative) |

---

### Category B: Quality Control Orders (Statutory Mandates)

| Document ID | Regulatory Instrument | Issuing Authority | Regulatory Impact |
| :--- | :--- | :--- | :--- |
| **DOC-QCO-MEITY-CRO** | *Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order* | Ministry of Electronics & IT (MeitY) / Gazette of India | **Mandatory CRS Registration** required prior to manufacture, import, or sale of self-ballasted LED lamps in India. |

---

### Category C: Certification & Licensing Schemes

| Document ID | Scheme Title | Scope & Applicable Procedures | Authority |
| :--- | :--- | :--- | :--- |
| **DOC-SCHEME-CRS-LED** | *Compulsory Registration Scheme (Scheme II) Guidelines for LED Lamps* | Self-declaration of conformity based on test reports from BIS-recognized labs. Portal: `crsbis.in`. | Tier 1A / Tier 2 |
| **DOC-GUIDE-SERIES-LED** | *Series Guidelines for Grouping of Self-Ballasted LED Lamps* | Technical criteria for grouping wattage variants (e.g., up to 25W), driver topologies, and lamp caps under a single test report / registration. | Tier 2 (Official Guidelines) |

---

### Category D: Testing Requirements & Critical Clauses

| Standard | Clause / Section | Test Name & Evaluation Scope |
| :--- | :--- | :--- |
| **IS 16102 (Part 1)** | `Clause 6` | **Marking Requirements**: Rated wattage, rated voltage, manufacturer trademark, safety warnings, and CRS mark format. |
| **IS 16102 (Part 1)** | `Clause 7` | **Interchangeability**: Dimensional compatibility and cap fitment (B22d, E27) under mechanical torque. |
| **IS 16102 (Part 1)** | `Clause 8` | **Insulation Resistance & Electric Strength**: Dielectric withstand at 4000V after humidity pre-conditioning. |
| **IS 16102 (Part 1)** | `Clause 9` | **Mechanical Strength**: Torsion resistance of cap and axial pull strength tests. |
| **IS 16102 (Part 1)** | `Clause 11` | **Resistance to Heat and Fire**: Glow-wire test at 650°C / 750°C and needle-flame test on insulating material. |
| **IS 16102 (Part 1)** | `Clause 12` | **Fault Conditions**: Component failure simulation (driver short-circuit, diode open-circuit) without fire or electric shock hazard. |
| **IS 16102 (Part 2)** | `Clause 7` | **Luminous Flux & Efficacy**: Minimum lumen output and energy efficiency threshold (lm/Watt). |
| **IS 16102 (Part 2)** | `Clause 8` | **Color Characteristics**: Correlated Color Temperature (CCT) and Color Rendering Index (CRI $\ge 80$). |
| **IS 16102 (Part 2)** | `Clause 9` | **Life & Lumen Maintenance**: 1,000-hour and 6,000-hour lumen depreciation and endurance cycling. |

---

### Category E: Recognized Laboratory Network

| Lab ID | Facility Name | Location | Testing Scope Authorized |
| :--- | :--- | :--- | :--- |
| **LAB-BIS-CL** | *BIS Central Laboratory* | Sahibabad, Ghaziabad, UP | IS 16102 (Part 1 & 2), IS 15885 |
| **LAB-NABL-ERDA** | *Electrical Research and Development Association (ERDA)* | Vadodara, Gujarat | Full safety, performance, and photometric scope |
| **LAB-NABL-CPRI** | *Central Power Research Institute (CPRI)* | Bengaluru, Karnataka | Full safety, environmental, and endurance scope |
| **LAB-NABL-ETDC** | *Electronic Test and Development Centre (ETDC)* | Multiple Centers | Safety testing under CRS Scheme |

---

### Category F: Consumer Verification

* **Standard Mark**: Compulsory Registration Mark ("Standard Mark") displaying symbol $\text{IS } 16102\ (\text{Part } 1)$ and unique registration number **$\text{R-}XXXXXXXX$**.
* **Verification Flow**: Input R-Number into BIS Care App $\to$ returns verified manufacturer name, brand, model numbers, and validity status.
