# Phase 8.5 HTTP Source Discovery Report

## A. SRC-001 HTTP Response
- **Status**: 200 OK
- **Final URL**: `https://www.bis.gov.in/know-your-standard/?lang=en`
- **Content Type**: `text/html; charset=UTF-8`
- **Content Length**: ~405 KB
- **HTML Title**: Know Your Standard - Bureau of Indian Standards

## B. SRC-001 Form/Search Mechanism
- **Form ID**: `views-exposed-form-solr-search-page-1`
- **Method**: `GET`
- **Action**: `https://www.bis.gov.in`
- **Inputs**: `<input type="text" name="s" id="edit-keywords">`
- The static HTML form appears to use the standard WordPress `s` query parameter, but the `id="edit-keywords"` and form ID suggest a Solr-backed search view.

## C. SRC-001 Discovered Endpoints
- **AJAX**: `https://www.bis.gov.in/wp-admin/admin-ajax.php`
- **WP API**: `https://www.bis.gov.in/wp-json/...`
- No explicit search-specific API endpoint was found exposed in the static HTML configuration.

## D. SRC-001 Refrigerator Result
- **Result**: FAILED
- Submitting a GET request with `?s=refrigerator&lang=en` did not yield the Solr search results. Instead, it triggered the global WordPress search which redirected to the Hindi homepage (`https://www.bis.gov.in/?lang=hi`), stripping the English parameter and yielding 0 standard results. The true Solr search mechanism likely relies on JavaScript/AJAX payloads that are not easily reconstructed from the static HTML alone.

## E. SRC-005 HTTP Response
- **Status**: 200 OK
- **Final URL**: `https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en`
- **Content Length**: ~411 KB
- **HTML Title**: Products under Compulsory Certification - Bureau of Indian Standards

## F. SRC-005 JavaScript/Configuration Evidence
- The page contains references to `admin-ajax.php`.
- **CRITICAL**: The page contains **0** tables, **0** DataTables configurations, and **0** API endpoint references for product directories. 

## G. SRC-005 Discovered Data Source
- **Discovery**: The `SRC-005` URL is merely a **landing page**. It does not contain the product tables. 
- Instead, it contains static anchor links to the actual sub-schemes, most notably:
  - `https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en`

## H. Endpoint Request/Response Evidence
- An HTTP `GET` request was executed against the **Scheme-I** sub-page.
- **URL**: `.../scheme-i-mark-scheme/?lang=en`
- **Response Size**: 1.24 MB
- **Content**: The response is a massive, static, server-rendered HTML document containing 2 large `<table>` elements.
- **Refrigerator Test**: The static HTML contains multiple occurrences of `"refrigerator"`, `"cement"`, and standard numbers.
- **DataTables**: False. The data is entirely server-rendered HTML.

## I. Pagination/Completeness Evidence
- **Complete**: YES
- The Scheme-I HTML table contains **909 rows**.
- There are no pagination controls. All products under Scheme I (which includes IS 15750 refrigerators) are served simultaneously in this single 1.2 MB static HTML payload.

## J. Authority/Provenance Validation
- Data is served directly from `https://www.bis.gov.in`.
- Valid HTTPS, HTTP 200 status.
- Official domain, definitively authoritative.

## K. Browser vs HTTP Findings
- **Browser (Playwright)**: Is actively blocked by anti-bot/WAF mechanisms, resulting in an empty 0-byte `<body>` being rendered.
- **HTTP (Requests)**: Successfully bypasses the WAF, receiving the complete 400KB to 1.2MB HTML payloads.

## L. Recommended Acquisition Strategy
- **Abandon browser automation (Playwright)** for BIS discovery.
- **Update `source_registry.json`**: Change `SRC-005` to point directly to the specific sub-scheme URLs (e.g., `scheme-i-mark-scheme`, `scheme-ii-registration-scheme`).
- **Data Extraction**: Use standard Python HTTP clients (e.g., `requests`) to fetch the HTML, and use `BeautifulSoup` to parse the statically rendered `<table>` rows into standard/product relationships. This is vastly more stable, requires no JavaScript execution, and avoids the WAF blocking Playwright.

## M. Hardcoding Audit
- No `"refrigerator"` logic hardcoded in discovery strategies.
- No `"IS 15750"` mappings hardcoded.
- The investigation script dynamically probed the environment without assuming the existence of specific product data.

## N. Phase 6 Integrity
- **Phase 6 State**: FROZEN and UNTOUCHED.
- No modifications were made to `candidate_documents.json`, Chroma collections, or BM25 indexes. No documents were acquired.

## O. Final Decision
**HTTP_SOURCE_DISCOVERY_PARTIAL**

(Success on SRC-005 product tables via static HTTP sub-pages, but partial failure on reconstructing the dynamic SRC-001 Solr search).
