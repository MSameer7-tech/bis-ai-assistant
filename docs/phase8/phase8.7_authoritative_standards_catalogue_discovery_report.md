# Phase 8.7: Authoritative Indian Standards Catalogue Discovery Report

## Objective
Investigate authoritative BIS sources (`SRC-001`, `SRC-002`, `SRC-003`) to discover the actual Indian Standards catalogue. Identify the discovery mechanisms (API, HTML, JS) and record schemas, particularly focusing on how product relationships are maintained.

## Findings Summary
The overarching Indian Standards metadata is hosted on the ASP.NET e-Sale portal (`SRC-002`). `SRC-001` and `SRC-003` (WordPress-based) are heavily restricted against HTTP clients or rely on generic CMS search functions rather than structured catalogues. 

Most importantly, the authoritative standard record does **not** contain explicit product keyword mappings for compulsory schemes. Product-to-standard relationships are maintained at the Scheme level (`SRC-005`), not in the overarching standards metadata.

---

## Detailed Source Investigations

### 1. SRC-002: Standards Publishing & e-Sale Portal (`standardsbis.bsbedge.com`)
**Status:** DISCOVERY SUCCESSFUL

This is the authoritative portal for standard metadata. It is built using ASP.NET WebForms and is accessible via standard HTTP clients without WAF blocks.

*   **Discovery Mechanism:**
    *   The portal uses the ASP.NET AJAX Control Toolkit for its search autocomplete functionality.
    *   **JSON API Endpoint:** `POST https://standardsbis.bsbedge.com/popupextender.aspx/GetStdNo_Bis`
    *   **Payload:** `{"prefixText": "<STANDARD_NUMBER>", "count": 20, "contextKey": ""}`
    *   **Response:** JSON array containing the full Standard Number and internal Database ID required to view the record (e.g., `Standard_Number=IS+15750&id=8074`).
*   **Metadata Record:**
    *   **Endpoint:** `GET /BIS_SearchStandard.aspx?Standard_Number=IS+15750&id=8074`
    *   **Format:** Server-rendered HTML.
    *   **Schema Discovered:**
        *   Standard Number (`IS 15750 : 2006`)
        *   Reaffirmed Year (`2022`)
        *   Title (`Household frost-free refrigerating appliances...`)
        *   Technical Committee (`MED 3`)
        *   Status (`withdrawn`, `active`)
        *   Superseded By (`IS 17550 (Part 1) : 2021...`)
        *   No. of Amendments (`2`)
*   **Product Relationships:**
    *   The detailed metadata schema does **not** contain a structured field for "Products" or "Keywords" linking generic product names (like "refrigerator") to the standard. 
    *   **Conclusion:** The compulsory product mapping discovered in Phase 8.6 (`SRC-005`) is a separate dataset. It is factually incorrect to expect `SRC-002` to provide a "refrigerator -> IS 15750" structured keyword mapping.

### 2. SRC-001: Know Your Standard (`www.bis.gov.in/know-your-standard`)
**Status:** BLOCKED / NOT A STRUCTURED CATALOGUE

*   Hosted on a WordPress backend.
*   The primary search form submits to the generic WordPress search (`/?s=keyword`), which returns unstructured web pages and blog posts rather than a database catalogue.
*   The actual "Know Your Standard" widget likely relies on internal iFrames or protected APIs that time out when queried via standard HTTP clients in this environment.

### 3. SRC-003: Amendments & Errata (`www.bis.gov.in/know-your-standard/amendments/`)
**Status:** BLOCKED

*   Standard Python HTTP clients (and `curl`) experience hard timeouts (`Read timed out (15s)`) or receive empty responses. 
*   Like Phase 8.4's browser automation, this path is heavily WAF-protected against automated headless/scripted access.

---

## Proposed Phase 8.7 Acquisition Strategy

1.  **Target Source:** Use `SRC-002` (`standardsbis.bsbedge.com`) exclusively for authoritative standards metadata.
2.  **Lookup Mechanism:** 
    *   Use the discovered `GetStdNo_Bis` JSON API to resolve standard numbers to internal IDs.
    *   Fetch the detail HTML using `BIS_SearchStandard.aspx`.
3.  **Data Extraction:** Extract Title, Status, Committee, Reaffirmed Year, and Superseded By fields using BeautifulSoup.
4.  **Integration Rule:** Treat `SRC-002` metadata as enriching the standard entity itself. Do **not** attempt to extract compulsory product mappings from this source, as they do not exist here. Phase 8.6 (`SRC-005`) remains the correct source for Scheme/Product relationships.
