import hashlib
import json
from typing import Dict, Any, List

class StatutoryEvidenceUnit:
    def __init__(self, record_envelope: Dict[str, Any], text_chunk: str, chunk_index: int, provenance_overrides: Dict[str, Any] = None):
        self.chunk_id = hashlib.sha256(f"{record_envelope['integration_record_id']}_{chunk_index}".encode()).hexdigest()
        self.integration_record_id = record_envelope["integration_record_id"]
        self.canonical_identity = record_envelope["canonical_identity"]
        self.text_chunk = text_chunk
        self.evidence_role = "STATUTORY_EVIDENCE"
        self.authority_level = record_envelope.get("authority_level", "STATUTORY")
        self.lifecycle_status = record_envelope.get("lifecycle_status", "ACTIVE")
        
        # Provenance propagation
        self.provenance = record_envelope.get("provenance", {}).copy()
        if provenance_overrides:
            self.provenance.update(provenance_overrides)

class StatutoryRelevanceGate:
    @staticmethod
    def validate(query: str, evidence: StatutoryEvidenceUnit) -> bool:
        # A mock semantic relevance gate. Real implementation would use cross-encoder/LLM.
        # Ensure it rejects technical questions.
        technical_keywords = ["test parameter", "sampling frequency", "is 15750", "laboratory capability", "testing method"]
        query_lower = query.lower()
        if any(kw in query_lower for kw in technical_keywords):
            return False
        
        statutory_keywords = ["act", "power", "penalty", "regulation", "rule", "legal"]
        if any(kw in query_lower for kw in statutory_keywords):
            return True
            
        return False

class Phase10StatutoryIndex:
    def __init__(self):
        self.structured_metadata_index = {}
        self.bm25_text_index = {}
        self.chroma_text_index = {}
        
    def integrate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "status": "EXCLUDED",
            "chunks_created": 0,
            "reason": None
        }
        
        if record.get("eligibility_status") != "ELIGIBLE":
            result["reason"] = f"Ineligible status: {record.get('eligibility_status')}"
            return result
            
        if record.get("evidence_role") != "STATUTORY_EVIDENCE":
            result["reason"] = "Role mismatch"
            return result
            
        # 1. Add to structured index for metadata lookup
        self.structured_metadata_index[record["canonical_identity"]] = record["payload"]
        
        # 2. Chunking & Text indexing (simulated)
        text = record["payload"].get("title", "")
        # Create a single chunk for the title as simulation
        chunk = StatutoryEvidenceUnit(record, text, 0)
        
        self.bm25_text_index[chunk.chunk_id] = chunk
        self.chroma_text_index[chunk.chunk_id] = chunk
        
        result["status"] = "INTEGRATED"
        result["chunks_created"] = 1
        return result

    def retrieve(self, query: str, active_only: bool = True) -> List[StatutoryEvidenceUnit]:
        results = []
        for chunk in self.chroma_text_index.values():
            if StatutoryRelevanceGate.validate(query, chunk):
                if active_only and chunk.lifecycle_status in ["SUPERSEDED", "WITHDRAWN", "HISTORICAL"]:
                    continue
                results.append(chunk)
        return results

    def conflict_resolution(self, chunks: List[StatutoryEvidenceUnit]) -> List[StatutoryEvidenceUnit]:
        # If multiple active chunks from different distinct documents are retrieved, we have a conflict
        active_chunks = [c for c in chunks if c.lifecycle_status == "ACTIVE"]
        identities = set([c.canonical_identity for c in active_chunks])
        if len(identities) > 1:
            # Conflicting evidence -> controlled abstention
            return []
        return active_chunks
