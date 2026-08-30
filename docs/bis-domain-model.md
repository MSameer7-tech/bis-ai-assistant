# BIS Domain Model & Entity Architecture

This document defines the formal relational structure, domain models, and graph relationships for the **BIS AI Intelligent Assistant**.

---

## 1. Relational Graph & Domain Architecture

```text
                                  ┌────────────────────────┐
                                  │        PRODUCT         │
                                  │ (Attributes & Specs)   │
                                  └───────────┬────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       ┌─────────────────────────┐                         ┌─────────────────────────┐
       │   STANDARD APPLICABILITY│                         │ REGULATORY APPLICABILITY│
       │ (Indian Standard Specs) │                         │  (Quality Control Orders│
       └────────────┬────────────┘                         └────────────┬────────────┘
                    │                                                   │
                    ▼                                                   ▼
       ┌─────────────────────────┐                         ┌─────────────────────────┐
       │     CLAUSES & TESTS     │                         │  CONFORMITY REQUIREMENT │
       │  (Normative Parameters) │                         │ (Mandatory / Voluntary) │
       └────────────┬────────────┘                         └────────────┬────────────┘
                    │                                                   │
                    ▼                                                   ▼
       ┌─────────────────────────┐                         ┌─────────────────────────┐
       │    LABORATORY SCOPE     │                         │  CERTIFICATION SCHEME   │
       │ (Authorized Test Scope) │                         │  (Scheme I / Scheme II) │
       └────────────┬────────────┘                         └────────────┬────────────┘
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │     SOURCE REGISTRY     │
                                 │ (Authoritative Tier 1/2)│
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │     CLAIM & EVIDENCE    │
                                 │  (Granular Citations)   │
                                 └─────────────────────────┘
```

---

## 2. Granular Evidence & Citation Lineage

To guarantee source traceability and zero hallucination, the system validates claims through this data lineage:

```text
User Question
      ↓
Answer Text
      ↓
[Claim] ──────────────────────────┐
  • claim_id: "CLM-001"           │
  • claim_text: "..."             │
  • status: "direct_evidence"     │
      ↓                           │
[Evidence Chunk]                  ▼
  • chunk_id: "CHK-102" ───> [Source Registry]
  • content: "..."             • source_id: "SRC-001"
  • document_id: "DOC-001"     • authority_level: "Tier 1B"
  • clause_number: "6.1"       • url: "https://..."
  • page_number: 14            • status: "verified_authentic"
```

---

## 3. First-Class Entity Data Models

### 3.1 `Product`
```json
{
  "product_id": "string",
  "product_name": "string",
  "category": "string",
  "manufacturer_description": "string",
  "technical_attributes": {
    "wattage": "number",
    "voltage_range": "string",
    "cap_type": "string",
    "driver_topology": "string"
  },
  "intended_use": "string",
  "variants": ["string"],
  "classification": "string"
}
```

### 3.2 `Source`
```json
{
  "source_id": "string",
  "domain": "string",
  "source_type": "string",
  "issuing_authority": "string",
  "authority_level": "string",
  "title": "string",
  "standard_or_document_number": "string",
  "version_edition": "string",
  "publication_date": "string",
  "effective_date": "string",
  "url": "string",
  "retrieval_date": "string",
  "status": "string",
  "notes": "string"
}
```

### 3.3 `Claim`
```json
{
  "claim_id": "string",
  "claim_text": "string",
  "claim_type": "string",
  "evidence_ids": ["string"],
  "confidence_status": "string",
  "citation_mapping": {
    "source_id": "string",
    "document_number": "string",
    "clause_number": "string",
    "page_number": "number"
  }
}
```

### 3.4 `IndianStandard` & `Clause`
```json
{
  "standard_number": "string",
  "title": "string",
  "division_council": "string",
  "publication_year": "number",
  "status": "string",
  "clauses": [
    {
      "clause_id": "string",
      "clause_number": "string",
      "clause_title": "string",
      "page_start": "number",
      "page_end": "number",
      "content_text": "string",
      "is_normative_requirement": "boolean"
    }
  ]
}
```

### 3.5 `QualityControlOrder`
```json
{
  "qco_id": "string",
  "issuing_ministry": "string",
  "gazette_notification_number": "string",
  "notification_date": "string",
  "effective_date": "string",
  "enforcement_status": "string",
  "notified_standards": ["string"],
  "applicability_criteria": "string",
  "exemptions": ["string"]
}
```

### 3.6 `CertificationScheme`
```json
{
  "scheme_code": "string",
  "scheme_name": "string",
  "regulatory_basis": "string",
  "factory_audit_required": "boolean",
  "lab_testing_required": "boolean",
  "portal_url": "string",
  "process_steps": ["string"]
}
```

### 3.7 `TestRequirement` & `Laboratory`
```json
{
  "test_id": "string",
  "test_name": "string",
  "standard_number": "string",
  "clause_ref": "string",
  "acceptance_criteria": "string",
  "laboratory": {
    "lab_id": "string",
    "lab_name": "string",
    "city": "string",
    "state": "string",
    "authorized_standards": ["string"]
  }
}
```

---

> [!NOTE]
> All concrete standards, clauses, dates, and order numbers serve as structural blueprints and illustrative examples. Actual values are strictly resolved from verified sources in the BIS Source Registry.
