from typing import Dict, Any, List
from ai.update.change_detector_and_version import ChangeDetector, VersionManager
from ai.update.index_and_rollback import IndexUpdater, RollbackManager
import uuid

class TransactionManager:
    def __init__(self):
        self.batch_id = str(uuid.uuid4())
        self.candidates = []
        self.status = "PENDING"
        self.events = []

    def log_event(self, doc_id: str, old_status: str, new_status: str, reason: str):
        self.events.append({
            "batch_id": self.batch_id,
            "document_id": doc_id,
            "previous_status": old_status,
            "new_status": new_status,
            "reason": reason
        })

    def commit(self) -> bool:
        # Represents atomic promotion
        if any(c.get("validation_failed") for c in self.candidates):
            self.status = "FAILED"
            return False
        self.status = "RELEASED"
        return True

class IncrementalUpdateEngine:
    def __init__(self, baseline_records: Dict[str, Any]):
        self.baseline = baseline_records
        self.transaction = None
        self.index_updater = IndexUpdater()

    def run_update_batch(self, candidates: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        self.transaction = TransactionManager()
        self.transaction.candidates = candidates
        
        results = {
            "unchanged": 0,
            "changed": 0,
            "new": 0,
            "duplicate": 0,
            "failures": 0,
            "dry_run": dry_run
        }
        
        for cand in candidates:
            # 1. Detect change
            change_type = ChangeDetector.classify_change(cand, self.baseline)
            doc_id = cand.get("candidate_identity", "unknown")
            
            self.transaction.log_event(doc_id, "UNKNOWN", change_type, "change detection")
            
            if change_type == "UNCHANGED":
                results["unchanged"] += 1
                if not dry_run:
                    # Preserve existing record, skip extraction and embedding
                    pass
            elif change_type == "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW":
                results["changed"] += 1
                if not dry_run:
                    # Trigger extraction/embedding
                    if cand.get("simulate_extraction_failure"):
                        cand["validation_failed"] = True
                        results["failures"] += 1
                        self.transaction.log_event(doc_id, change_type, "EXTRACTION_FAILED", "mock failure")
                    else:
                        self.index_updater.update_document_incremental(doc_id, [{"text": "new chunk"}], {"lifecycle": "ACTIVE"})
            elif change_type == "DISTINCT_DOCUMENT":
                results["new"] += 1
                if not dry_run:
                    if cand.get("identity_status") == "IDENTITY_UNRESOLVED":
                        cand["validation_failed"] = True
                        results["failures"] += 1
                        self.transaction.log_event(doc_id, change_type, "IDENTITY_UNRESOLVED", "unresolved identity")
                    else:
                        self.index_updater.update_document_incremental(doc_id, [{"text": "new doc"}], {"lifecycle": "ACTIVE"})
            elif change_type == "DUPLICATE_REPRESENTATION_ALIAS":
                results["duplicate"] += 1
        
        # Transaction commit
        if not dry_run:
            success = self.transaction.commit()
            results["transaction_status"] = "RELEASED" if success else "HELD_FOR_REVIEW"
        else:
            results["transaction_status"] = "DRY_RUN_COMPLETED"
            
        return results
