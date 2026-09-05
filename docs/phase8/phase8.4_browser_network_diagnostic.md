# Phase 8.4 Browser & Network Diagnostic

## A. Browser Environment
- **Playwright version**: 1.62.0
- **Configured Browser**: Chromium using `channel="chrome"`
- **Execution constraint**: Ran in an isolated sandbox environment using the host machine's Google Chrome executable.

## B. SRC-001 Timeline
- **T+0s**: Navigation initiated with `wait_until="commit"`. The request received a `302 Found` redirect immediately from `/know-your-standard/` to `/?lang=hi` (Hindi localized version).
- **T+2s - T+6s**: DOM count stayed around `23` nodes, `document.readyState` remained `"loading"`.
- **T+8s**: DOM count jumped to `1708` nodes.
- **T+10s - T+20s**: DOM count stabilized at `1753` nodes, `document.readyState` progressed through `"interactive"` to `"complete"`. The page title loaded as `अपने मानक को जानें - Bureau of Indian Standards`.

## C. SRC-001 DOM Hydration Evidence
The DOM partially hydrated, as evidenced by the node count growing from 23 to 1753 nodes over ~10 seconds. However, several JavaScript errors were logged on the page (e.g., `e.indexOf is not a function`, `WOW is not defined`), indicating that the page's scripts did not fully execute or initialize correctly.

## D. SRC-001 Network Evidence
- **Initial Request**: HTTP 302 Redirect to `?lang=hi`
- **Subsequent Requests**: Successfully downloaded 67+ assets including CSS, fonts, and images.
- **Status**: 200 OK for most resources, but 403 Forbidden on `Isi.gif`.

## E. SRC-001 Search-Control Evidence
**Result: NOT FOUND.** 
Despite the DOM node count reaching 1753, the semantic search control (`input[placeholder*="search" i]`) never appeared in the DOM. This is primarily caused by the `302` redirect to the Hindi language version (`?lang=hi`), where the placeholder text is localized (e.g., "खोजें" instead of "Search") and multiple JavaScript errors interrupted the initialization of interactive form components. 
- **Controlled query "refrigerator"**: Could not be executed.

## F. SRC-005 Timeline
- **T+0s**: Navigation initiated with `wait_until="commit"`. Received a 302 redirect to `?lang=hi`.
- **T+2s - T+20s**: DOM count immediately read as `1826` nodes, and `document.readyState` read `"complete"` throughout the polling window. The page title loaded as `अनिवार्य प्रमाणन के तहत उत्पाद - Bureau of Indian Standards`.

## G. SRC-005 Network/API Evidence
- **XHR/Fetch Requests**: Only one background request was observed: `https://www.bis.gov.in/directory/regional-offices/?lang=hi`.
- **Product Records API**: **ZERO** requests matching product discovery endpoints were observed.

## H. SRC-005 DataTables Evidence
**Result: NOT TRIGGERED.**
The DataTables or asynchronous fetch logic failed to initialize. No product-record API response was produced. The localized `?lang=hi` page combined with the observed JavaScript errors (`url.indexOf is not a function`) prevented the expected DataTables XHR requests from firing.

## I. Root Cause Classification
**LIVE_PORTAL_BLOCKED**
The portals are accessible via HTTP, but they are functionally blocked/unhydrated from an automation perspective due to:
1. **Language/Geo Redirect**: The server issues a mandatory 302 redirect to `?lang=hi`, breaking English-language semantic DOM selectors.
2. **JavaScript Failures**: The localized pages contain unhandled JavaScript errors that prevent critical asynchronous libraries (like DataTables) from initializing.
3. **Severe Latency**: Waiting for `domcontentloaded` times out at 30 seconds due to hanging background scripts.

## J. Recommended Fix
1. **Bypass Localization**: Append `?lang=en` to the canonical URL or intercept the initial request headers to enforce an English session cookie (`qtrans_front_language=en`).
2. **Broaden Selectors**: Update the semantic fallbacks in `query_driven.py` to identify search inputs by type or position rather than English placeholders.
3. **Handle Hanging DOMs**: Continue using `wait_until="commit"` combined with dynamic element polling, since `domcontentloaded` is unreliable on this portal.

## K. Whether another live validation can now be run
Another live validation should **NOT** be run until the localization redirect (302 to `?lang=hi`) and subsequent JS failures are resolved either via header injection or URL query parameters in the source registry.

## L. Statement of System State
Explicitly confirming:
- **No acquisition** was performed.
- **No extraction** was performed.
- **No indexing** was performed.
- Phase 6 indexes (Chroma, BM25, chunks) and `candidate_documents.json` remain untouched.
- No hardcoded product mappings were added.
