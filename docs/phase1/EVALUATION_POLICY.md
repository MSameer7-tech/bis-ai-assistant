# Multi-Dimensional Evaluation Policy & Verification Framework

**Document Version**: 1.1  
**Phase**: Phase 1 — SIH PS Requirements & System Scope  
**Purpose**: Define the 7 core evaluation dimensions to verify system truthfulness, evidence grounding, and robustness, distinguishing PS requirements from project engineering targets.

---

## 1. PS Requirements vs Project Engineering Targets

```
╔══════════════════════════════════════════════════════════════════════════════╗
║               REQUIREMENTS VS ENGINEERING BENCHMARK TARGETS                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 1. SIH PS Requirements (Capabilities):                                       ║
║    - Natural language standard recommendation & Q&A.                         ║
║    - Certification scheme & process guidance.                                ║
║    - Consumer verification & hallmarking guidance.                           ║
║    - Multilingual interaction (English, Hindi, regional Indian languages).   ║
║    - 100% grounding in authorized BIS knowledge sources with citations.      ║
║                                                                              ║
║ 2. Project Engineering Target Benchmarks (Internal Quality Gates):           ║
║    - Intent Classification Accuracy : ≥ 98% on benchmark query suites        ║
║    - Product Resolution Precision   : ≥ 95% on natural language inputs       ║
║    - Retrieval Clause Recall        : ≥ 95% on top-5 ranked chunks           ║
║    - End-to-End Query Latency       : < 2.5s average response time           ║
║    - Citation Completeness          : 100% of factual answers                ║
║    - Zero-Hallucination Safe Refusal: 100% on out-of-scope adversarial tests ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. The 7 Evaluation Dimensions

Rather than relying on simple end-to-end string matching, every test query must be audited through a 7-stage evaluation pipeline:

```
Query
  ↓
[1. Product / Query Understanding] ──> Correct canonical entity & intent?
  ↓
[2. Retrieval Correctness]          ──> Relevant normative chunks & subgraph nodes?
  ↓
[3. Evidence Verification]          ──> Claim-appropriate authoritative evidence attached?
  ↓
[4. Mandatory / Scheme Logic]       ──> Accurate QCO & conformity scheme decision?
  ↓
[5. Answer Factual Precision]       ──> Verbatim parameters & zero hallucinated facts?
  ↓
[6. Citation & Provenance]          ──> Specific clause, table, and page references?
  ↓
[7. Scope & Safety Gate]            ──> Deterministic refusal on adversarial queries?
```

---

## 3. Dimensional Evaluation Criteria

### Dimension 1: Product & Query Understanding
- **Engineering Target**: Intent classification accuracy $\ge 98\%$, entity resolution accuracy $\ge 95\%$.
- **Validation**: Ensures natural language descriptions resolve to canonical commodities without mistaking descriptive words for standard codes.

### Dimension 2: Retrieval Correctness
- **Engineering Target**: Top-5 retrieval precision $\ge 90\%$, recall on governing clauses $\ge 95\%$.
- **Validation**: Ensures hybrid dense + lexical retrieval surfaces the exact governing clauses, manuals, and QCOs.

### Dimension 3: Evidence Grounding (Anti-Metadata Trap)
- **Quality Gate**: $100\%$ of factual assertions backed by claim-appropriate evidence records.
- **Validation**: System is audited to reject answers that merely match metadata without retrieving underlying document text (`METADATA_ONLY` rejection).

### Dimension 4: Regulatory Scheme & Mandate Logic
- **Safety Gate**: $100\%$ accuracy in differentiating Scheme-I, Scheme-II, Scheme-IV, and voluntary vs mandatory QCO enforcement.
- **Validation**: Prohibits false legal claims.

### Dimension 5: Technical Value & Tolerance Precision
- **Quality Gate**: $100\%$ numerical and unit consistency against standard tables.
- **Validation**: Unit conversions (e.g. MPa $\to \text{N/mm}^2$, bar $\to \text{kPa}$, kg $\to \text{g}$) must be mathematically verified.

### Dimension 6: Citation Completeness
- **Quality Gate**: $100\%$ of responses include valid document titles, standard numbers, and clause/page locators.
- **Validation**: Users must be able to verify every statement in the source document.

### Dimension 7: Adversarial Safety & Scope Handling
- **Safety Gate**: $100\%$ safe refusal rate on out-of-scope, fictional, or incompatible queries.
- **Validation**: 0 hallucinations on non-BIS goods.
