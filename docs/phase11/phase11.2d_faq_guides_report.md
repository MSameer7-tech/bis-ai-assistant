# Phase 11.2D FAQ / Guides / Booklets Acquisition Report

## 1. Objective
Expand the Phase 11 baseline with authoritative guidance material (FAQs, Booklets, Guides, Procedures, Circulars) from official BIS sources. The goal is to provide the RAG system with rich, natural-language explanations of BIS procedures and requirements.

## 2. Acquisition Strategy
Given the absence of a single centralized FAQ portal, the crawler utilized **dynamic navigation** starting from broad BIS entry points (home, product certification, hallmarking, labs, consumer affairs). 
It employed a keyword-based link filter (`faq`, `guide`, `booklet`, `circular`, `procedure`, `handbook`, etc.) to discover and target relevant content. **PDFs were strictly prioritized** in the crawl queue because BIS typically publishes its official guides and procedures in PDF format.

## 3. Acquisition Pipeline Execution
The pipeline successfully crawled 51 prioritized URLs from a discovered pool of 242 candidates.

**Key authoritative content acquired (40 PDFs):**
- Internship Scheme Handbooks & Guidelines
- Revised Guidelines for Jewellers (Hallmarking)
- Guidelines for Assaying and Hallmarking Centres (AHC)
- Mandatory Hallmarking Orders & District Coverage Lists
- Assaying and Hallmarking Manual
- Standards National Portal (SNP) Bilingual Booklet
- Training Strategies
- Various Amendment Information Forms (AIF) for IS Standards
- Circulars on Simplified Procedures

## 4. Corpus Evolution Metrics (v21 → v22)

| Metric | Value |
|---|---|
| v21 Baseline Record Count | 1,092 |
| v22 Total Record Count | 1,135 |
| Newly Added Records | 43 |
| Rejected as Duplicates | 0 |
| Rejected for Insufficient Authority | 0 |
| Inaccessible Sources (Timeout/Large PDF) | 7 |
| Conflicting Records | 0 |

## 5. Domain Coverage (v22)

| Domain | Records | Change |
|---|---|---|
| LABORATORIES | 728 | - |
| HALLMARKING | 180 | - |
| LICENCES_REGISTRATIONS | 75 | - |
| CONSUMER_BIS_CARE | 59 | - |
| FAQ_GUIDES_BOOKLETS | **93** | **+43 (+86%)** |
| **Total** | **1,135** | |

## 6. Deduplication & Extraction Results
- **Extraction:** 40 of the 43 successfully acquired records were PDF documents. PyPDF2 successfully extracted the textual content. 
- **Timeouts:** 7 PDFs failed to download within the 8-second timeout window. These are likely very large files. They are recorded as inaccessible.
- **Deduplication:** 0 records were rejected as duplicates, meaning all 43 acquired documents are entirely new to the corpus.

## 7. Quality Notes
- The strategy to dynamically navigate and prioritize PDFs yielded exactly the type of authoritative, procedural guidance needed for the RAG system.
- The `FAQ_GUIDES_BOOKLETS` domain is now significantly more robust, containing official manuals and step-by-step guides for crucial processes like Jeweller Registration and AHC operations.

## 8. Recommendation
Phase 11.2D is **PASS**. The FAQ/Guides domain has been successfully expanded with high-value procedural PDFs.

As instructed, we should now pause acquisition phases and proceed to **Phase 11.3: Full Corpus Audit** to evaluate if the current 1,135 records represent sufficient knowledge coverage for the final RAG rebuild.
