# Phase 5: 507-Unit Discrepancy Diagnostic

## Root Cause
The duplicate audit previously reported 17,674 EvidenceUnits, while the quality audit reported 17,167 (a difference of exactly 507 units).
This was caused by the duplicate audit being run *before* the Phase 5 cleanup script (`scripts/phase5_cleanup.py`) was executed. 

The `phase5_cleanup.py` script removes stale folders from the `data/processed/evidence_units/` directory that belong to documents that are no longer classified as `EXTRACTION_SUCCESS`. The 507 units were located in these now-deleted stale document folders. Because the duplicate auditor simply iterates through the filesystem, it processed these stale units in its previous run. The 13 extra short units (17 vs 4) were also contained within these stale units.

## Current State
- The 507 stale units **do not exist** in the current EvidenceUnit filesystem (`data/processed/evidence_units/`).
- The current filesystem correctly contains exactly 17,167 units across 640 successful document directories.
- The 507 units were successfully purged generated artifacts and did not belong to the authoritative corpus.

## Remediation
Since the stale data was previously removed from the filesystem, re-running the duplicate auditor (`ai/processing/duplicate_auditor.py`) naturally aligns its count with the current canonical corpus. The duplicate auditor has been re-run and now accurately reflects 17,167 units and 4 short units. No authoritative data was deleted or modified during this diagnostic.
