# Phase 11.2C Consumer / BIS Care Acquisition Report

## 1. Objective
Acquire authoritative consumer service, complaint mechanism, verification, and awareness material from official BIS endpoints. Using the public-first strategy validated in Phase 11.2B: exhaust publicly accessible BIS content before attempting gated operational portals.

## 2. Acquisition Strategy
The crawler targeted consumer-specific BIS pages with a scoped link-following filter that only pursued URLs containing "consumer", "complaint", or "care" keywords. This prevents domain inflation by excluding general BIS standards/certification content.

**Start URLs:**
- `bis.gov.in/index.php/consumer-affairs/`
- `bis.gov.in/index.php/consumer-affairs/complaints/`
- `bis.gov.in/index.php/consumer-affairs/bis-care-app/`
- `bis.gov.in/index.php/consumer-affairs/consumer-awareness/`
- `manakonline.in/MANAK/Complaints` (operational portal, last priority)

## 3. Acquisition Pipeline Execution
The full run navigated 40 URLs and successfully acquired diverse consumer-oriented content:

**Key sources discovered and acquired:**
- Consumer affairs overview pages
- Complaint registration and status portals (`services.bis.gov.in` consumer dashboard)
- Consumer contact information pages
- Consumer FAQ pages
- Manak Munch consumer awareness gallery (18+ awareness content pages)
- BIS Circular/guidelines for consumers
- Public complaint dashboard
- BIS Students chapters programme
- BIS Standard clubs programme
- Complaint procedure PDF (`Procedure-for-dealing-with-complaints.pdf`)

**Operational portal behavior:**
- `manakonline.in/MANAK/Complaints` — timed out (WAF/session-gated), recorded as FAILED
- `services.bis.gov.in` consumer endpoints — many were publicly accessible and successfully acquired

## 4. Corpus Evolution Metrics (v20 → v21)

| Metric | Value |
|---|---|
| v20 Baseline Record Count | 1,058 |
| v21 Total Record Count | 1,092 |
| Newly Added Records | 34 |
| Rejected as Duplicates | 2 |
| Rejected for Insufficient Authority | 0 |
| Inaccessible Sources | 4 |
| Conflicting Records | 0 |

## 5. Domain Coverage (v21)

| Domain | Records |
|---|---|
| LABORATORIES | 728 |
| HALLMARKING | 180 |
| LICENCES_REGISTRATIONS | 75 |
| CONSUMER_BIS_CARE | 59 |
| FAQ_GUIDES_BOOKLETS | 50 |
| **Total** | **1,092** |

The CONSUMER_BIS_CARE domain grew from 25 → 59 records (+136% increase).

## 6. Deduplication Results
- 2 records rejected as content-hash duplicates of existing v20 records
- 4 sources recorded as inaccessible (WAF/session-gated)
- 0 records rejected for insufficient authority

## 7. Quality Notes
- The link filter successfully prevented domain inflation: only consumer/complaint/care URLs were followed
- The Manak Munch gallery pages contain consumer awareness content but are individually thin; the Phase 11.3 corpus audit should evaluate whether gallery pages carry sufficient standalone informational value
- The complaints procedure PDF was successfully extracted
- Hash-anchored URLs (e.g., `#skip-to-main-content`) were correctly treated as distinct crawl targets but produce duplicate content; 2 were properly caught by deduplication

## 8. Recommendation
Phase 11.2C is **PASS**. The consumer domain has been substantially enriched with authoritative material covering complaint mechanisms, verification portals, consumer awareness, and official procedures.

Ready to proceed to **Phase 11.2D: FAQ / Guides / Booklets** expansion.
