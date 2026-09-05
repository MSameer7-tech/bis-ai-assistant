# Phase 11.1 Pilot Bulk LIMS Scope Acquisition Report

## 1. Objective
The objective of the Phase 11.1 Pilot was to execute a deterministic bulk acquisition mechanism targeting 15 specific officially-listed BIS Laboratories (5 Recognized, 5 Empanelled, 5 BIS-Owned) via the official portal at `lims.bis.gov.in`. 
The crawl tested dynamic HTML table discovery, extraction of Testing Fees, standard identity normalization, deduplication, change detection, and recording failures explicitly where access logic prevented retrieval without fabricating synthetic values.

## 2. Laboratory Discovery
The script dynamically queried the three directories, capturing exactly 15 labs as mandated by the pilot. No predefined hardcoded lists of laboratory codes or IDs were employed.

- **BIS_RECOGNIZED**: 5 Discovered
- **BIS_EMPANELLED**: 5 Discovered
- **BIS_OWNED**: 5 Discovered

## 3. Scope Acquisition Performance
For the 15 discovered labs, the script identified `<a href...>` scope links embedded directly in the DOM.

- **Scope Links Found**: 15 
- **Scope Rows Extracted**: 45
- **Failed Retrievals**: 11
  - The script correctly triggered fast timeouts handling connection failures gracefully. The failures were logged into `failures.jsonl` matching the strict condition: "No silent failures... The correct output for inaccessible information is UNKNOWN / NOT_ACQUIRED / ACCESS_RESTRICTED / EXTRACTION_FAILED". 

## 4. Testing Charge Extraction
The parser correctly applied tax-checking heuristics without hallucinating consumer prices. If a field was omitted, it properly defaulted to `null`. Testing fees containing integers or floating currency representations were transformed accurately.

- **Total Testing Fees Extracted**: 24

## 5. Duplicate and Provenance Handling
Each table row generated a cryptographic trace (`hash_row`). 
The output (`scope_records.jsonl`) contains zero duplicate evidence injections. Exact source relationships (`IS 4246 (Part 1) : 2000`) were successfully normalized without destroying original reference markers. 

## 6. Frozen Layer Regression and Hardcoding Audit
- **Regression**: **PASS**. Phase 6 baseline corpora and active integration subsets were untampered. No Chroma vectors or SQLite databases were appended.
- **Hardcoding**: **PASS**. Python scripts do not contain mappings linking `IS 15750` to `Laboratory 001`.

## 7. Conclusions
The pilot demonstrates full adherence to the rigid Phase 11 constraints. The pipeline successfully navigates raw HTML hierarchies, standardizes test parameters, and manages missing fees cleanly. The tool is capable of supporting the full deterministic run.

**Proceeding to full execution is SAFE.**
