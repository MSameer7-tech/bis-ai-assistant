from typing import Dict, Any, List

class ChangeDetector:
    @staticmethod
    def classify_change(candidate: Dict[str, Any], baseline_records: Dict[str, Any]) -> str:
        # Check HTTP cache validators first if provided
        if candidate.get("http_status") == 304:
            return "UNCHANGED"
            
        candidate_id = candidate.get("candidate_identity")
        candidate_sha = candidate.get("source_sha256")
        
        # Exact match ID in baseline
        if candidate_id in baseline_records:
            baseline_sha = baseline_records[candidate_id].get("source_sha256")
            if candidate_sha == baseline_sha:
                return "UNCHANGED"
            else:
                return "CONTENT_CHANGED_REQUIRES_VERSION_REVIEW"
                
        # Check if the SHA exists under a different ID (alias)
        for b_id, b_rec in baseline_records.items():
            if b_rec.get("source_sha256") == candidate_sha:
                return "DUPLICATE_REPRESENTATION_ALIAS"
                
        # New distinct document
        return "DISTINCT_DOCUMENT"

class VersionManager:
    @staticmethod
    def determine_lifecycle_transition(current_status: str, new_status: str) -> str:
        # Mock logic representing state transitions
        if new_status == "WITHDRAWN":
            return "WITHDRAWN"
        if current_status == "ACTIVE" and new_status == "SUPERSEDED":
            return "SUPERSEDED"
        return new_status or current_status

    @staticmethod
    def construct_version_path(document_id: str, version_number: int) -> str:
        # Never overwrite: data/raw/immutable/
        return f"data/raw/immutable/{document_id}/v{version_number:03d}/"
