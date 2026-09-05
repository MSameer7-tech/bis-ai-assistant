# Source Access Matrix & Operational Protocols

**Document Version**: 1.0  
**Phase**: Phase 2 — BIS Authorized Knowledge-Source Architecture  
**Scope**: Operational Matrix of Endpoints, Access Methods, Rate Limits, and Formats  

---

## 1. Complete Source Endpoint Access Matrix

| Source ID | Source Name | Source Family | Canonical Host | Access Method | Format | Rate Limit (Req/Min) |
|---|---|---|---|---|---|---|
| **SRC-001** | BIS Know Your Standard Portal | `SRCF-001` | `www.bis.gov.in` | `HTML_SEARCH` | HTML, PDF | 20 |
| **SRC-002** | BIS Standards e-Sale Portal | `SRCF-001` | `standardsbis.bsbedge.com` | `HTML_CATALOG` | HTML | 20 |
| **SRC-003** | Standards Amendments Registry | `SRCF-002` | `www.bis.gov.in` | `PDF_LINK_DISCOVERY` | HTML, PDF | 15 |
| **SRC-004** | The Gazette of India Portal | `SRCF-003` | `www.egazette.gov.in` | `SEARCH_ENDPOINT` | HTML, PDF | 15 |
| **SRC-005** | Compulsory Certification Portal | `SRCF-003` | `www.bis.gov.in` | `HTML_CATALOG` | HTML, PDF | 20 |
| **SRC-006** | BIS Product Manuals Directory | `SRCF-004` | `www.bis.gov.in` | `PDF_LINK_DISCOVERY` | HTML, PDF | 15 |
| **SRC-007** | BIS Scheme of Inspection (SIT) | `SRCF-005` | `www.bis.gov.in` | `PDF_LINK_DISCOVERY` | HTML, PDF | 15 |
| **SRC-008** | Product Certification Overview | `SRCF-006` | `www.bis.gov.in` | `DIRECT_HTML` | HTML | 30 |
| **SRC-009** | Compulsory Registration (CRS) | `SRCF-006` | `www.crsbis.in` | `DIRECT_HTML` | HTML, PDF | 30 |
| **SRC-010** | Manakonline Licence Search | `SRCF-007` | `www.manakonline.in` | `REGISTRY_QUERY` | HTML | 10 |
| **SRC-011** | CRS Registered Manufacturers | `SRCF-007` | `www.crsbis.in` | `REGISTRY_QUERY` | HTML | 10 |
| **SRC-012** | BIS Central/Regional Labs | `SRCF-008` | `www.bis.gov.in` | `HTML_CATALOG` | HTML, PDF | 20 |
| **SRC-013** | BIS Recognized Labs Register | `SRCF-008` | `www.bis.gov.in` | `HTML_SEARCH` | HTML, PDF | 20 |
| **SRC-014** | BIS Hallmarking Regulations | `SRCF-009` | `www.bis.gov.in` | `DIRECT_HTML` | HTML, PDF | 30 |
| **SRC-015** | Manakonline Hallmarking Portal | `SRCF-009` | `www.manakonline.in` | `REGISTRY_QUERY` | HTML | 10 |
| **SRC-016** | Consumer Affairs & BIS Care | `SRCF-010` | `www.bis.gov.in` | `DIRECT_HTML` | HTML, PDF | 30 |
| **SRC-017** | Publications & FAQs | `SRCF-011` | `www.bis.gov.in` | `DIRECT_HTML` | HTML, PDF | 30 |
| **SRC-018** | Acts, Rules & Regulations | `SRCF-012` | `www.bis.gov.in` | `PDF_LINK_DISCOVERY` | HTML, PDF | 15 |

---

## 2. Polite Access & Crawling Policies

- **Standardized User-Agent**: Every request must carry `User-Agent: BIS-AI-Technical-Assistant-Acquisition/1.0 (Government-Regulatory-Research)`.
- **Adaptive Backoff**: HTTP 429 or 503 responses trigger exponential backoff with base 5.0 seconds.
- **Circuit Breaker**: 3 consecutive network failures on an endpoint temporarily halts acquisition for that specific source while allowing other endpoints to continue.
