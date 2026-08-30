# BIS Source Registry

This document serves as the master registry tracking all authoritative documents and data assets acquired, verified, and ingested into the **BIS AI Intelligent Assistant**.

---

## 1. Registry Lifecycle & Status Definition

Every source transitions through the following verification lifecycle:

```text
[Pending] ──> [Acquired] ──> [Verified Authentic] ──> [Processed & Ingested] ──> [Active]
                                      │
                                      └──> [Rejected / Superseded]
```

* **`Pending`**: Identified as a required official document; awaiting official PDF / source download.
* **`Acquired`**: Raw file obtained from an official government or BIS portal; awaiting metadata validation.
* **`Verified`**: Authenticity, Gazette reference, edition, and amendment status verified against the official BIS/Ministry gazette.
* **`Processed`**: Text extracted, clauses detected, structured JSON generated, and chunks validated.
* **`Active`**: Available in the production hybrid retrieval knowledge base.
* **`Superseded`**: Document was replaced by a newer revision or withdrawn by BIS/Ministry.

---

## 2. Master Source Registry

| ID | Source / Document Title | Type | Authority Tier | Knowledge Domain | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-001** | Official BIS Standard (Safety) | Indian Standard | Primary (Tier 1B) | Standards & Technical | `Pending` | Target: LED Lamps Safety Standard |
| **SRC-002** | Official BIS Standard (Performance) | Indian Standard | Primary (Tier 1B) | Standards & Performance | `Pending` | Target: LED Lamps Performance Standard |
| **SRC-003** | Official BIS Standard (Controlgear/Driver) | Indian Standard | Primary (Tier 1B) | Related Standards | `Pending` | Target: AC/DC LED Controlgear Safety |
| **SRC-004** | Line Ministry Quality Control Order | QCO / Gazette Order | Primary (Tier 1A) | Regulatory & Enforcement | `Pending` | Target: Electronics / Lighting QCO Notification |
| **SRC-005** | BIS Conformity Assessment Regulations | Statutory Regulation | Primary (Tier 1A) | Certification Schemes | `Pending` | Scheme I (ISI) & Scheme II (CRS) rules |
| **SRC-006** | BIS Product Manual / Guidelines | Product Manual | Supporting (Tier 2) | Licensing & Procedures | `Pending` | Guidelines for grant of license / registration |
| **SRC-007** | CRS Registration Guidelines | Procedural Guideline | Supporting (Tier 2) | Licensing & Series Guidelines | `Pending` | Grouping & series rules for lighting products |
| **SRC-008** | BIS Laboratory Scope Directory (LIMS) | Lab Registry Snapshot | Supporting (Tier 3) | Laboratories & Testing | `Pending` | Recognized test labs for lighting products |
| **SRC-009** | BIS Hallmarking Regulations & HUID Guide | Regulatory Order | Primary (Tier 1A) | Hallmarking | `Pending` | Gold/Silver hallmarking & HUID rules |
| **SRC-010** | BIS Consumer Grievance & Verification Guide | Portal / CAD Guide | Supporting (Tier 2) | Consumer Affairs | `Pending` | Mark verification & BIS Care app guide |

---

## 3. Machine-Readable Schema (`data/metadata/source_registry.json`)

When sources transition to `Acquired` and `Verified`, their structured metadata will be synchronized to `data/metadata/source_registry.json` using the schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BISSourceRegistry",
  "type": "array",
  "items": {
    "type": "object",
    "required": [
      "source_id",
      "title",
      "document_type",
      "issuing_organization",
      "authority_tier",
      "domain",
      "status"
    ],
    "properties": {
      "source_id": { "type": "string" },
      "title": { "type": "string" },
      "document_type": { "type": "string", "enum": ["indian_standard", "qco", "regulation", "product_manual", "guideline", "lab_scope", "faq"] },
      "issuing_organization": { "type": "string" },
      "standard_number": { "type": ["string", "null"] },
      "edition": { "type": ["string", "null"] },
      "amendments": { "type": "array", "items": { "type": "string" } },
      "authority_tier": { "type": "string", "enum": ["Tier 1A (Statutory)", "Tier 1B (Normative)", "Tier 2 (Guidance)", "Tier 3 (Directory)"] },
      "domain": { "type": "string" },
      "official_source_url": { "type": ["string", "null"] },
      "file_path": { "type": ["string", "null"] },
      "status": { "type": "string", "enum": ["pending", "acquired", "verified", "processed", "active", "superseded"] },
      "retrieval_date": { "type": ["string", "null"] }
    }
  }
}
```
