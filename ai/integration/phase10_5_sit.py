import hashlib
from typing import Dict, Any, List, Optional

class SITEVidenceUnit:
    def __init__(self, record_envelope: Dict[str, Any], text_chunk: str, chunk_index: int, provenance_overrides: Dict[str, Any] = None):
        self.chunk_id = hashlib.sha256(f"{record_envelope['integration_record_id']}_{chunk_index}".encode()).hexdigest()
        self.integration_record_id = record_envelope["integration_record_id"]
        self.canonical_identity = record_envelope["canonical_identity"]
        self.text_chunk = text_chunk
        self.evidence_role = "SIT_EVIDENCE"
        self.authority_level = record_envelope.get("authority_level", "TECHNICAL_REQUIREMENT")
        self.lifecycle_status = record_envelope.get("lifecycle_status", "ACTIVE")
        self.standard_identity = record_envelope["payload"].get("standard_identity")
        
        self.provenance = record_envelope.get("provenance", {}).copy()
        if provenance_overrides:
            self.provenance.update(provenance_overrides)

class SITRelevanceGate:
    @staticmethod
    def validate(query: str, evidence: SITEVidenceUnit) -> bool:
        query_lower = query.lower()
        # SIT evidence cannot answer legal, qco, laboratory capabilities, or certification applicability
        out_of_bounds = ["mandatory", "legal", "act", "qco", "gazette", "laboratory capability", "licence status", "hallmarking"]
        if any(kw in query_lower for kw in out_of_bounds):
            return False
            
        # Needs to match some SIT/testing keyword to be relevant for SIT_EVIDENCE
        sit_keywords = ["test", "sampling", "frequency", "method", "acceptance criteria", "parameter", "sit", "product manual"]
        if any(kw in query_lower for kw in sit_keywords):
            return True
            
        return False

class Phase10SITIndex:
    def __init__(self):
        self.structured_metadata_index = {}
        self.structured_requirements = {}
        self.structured_relationships = []
        self.bm25_text_index = {}
        self.chroma_text_index = {}
        
    def integrate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "status": "EXCLUDED",
            "chunks_created": 0,
            "relationships_integrated": 0,
            "requirements_integrated": 0,
            "reason": None
        }
        
        if record.get("eligibility_status") != "ELIGIBLE":
            result["reason"] = f"Ineligible status: {record.get('eligibility_status')}"
            return result
            
        if record.get("evidence_role") != "SIT_EVIDENCE":
            result["reason"] = "Role mismatch"
            return result
            
        if record.get("identity_status") == "IDENTITY_UNRESOLVED" or record.get("identity_status") == "IDENTITY_REVIEW_REQUIRED":
            result["reason"] = "Unresolved identity"
            result["status"] = "EXCLUDED"
            return result
            
        sit_id = record["payload"]["sit_document_id"]
        self.structured_metadata_index[sit_id] = record["payload"]
        
        # Integrate explicit Standard -> SIT relationships only
        for rel in record.get("relationships", []):
            if rel.get("relationship_status") == "RESOLVED":
                self.structured_relationships.append(rel)
                result["relationships_integrated"] += 1
                
        # Integrate requirements
        for req in record["payload"].get("requirements", []):
            self.structured_requirements[req["requirement_id"]] = req
            result["requirements_integrated"] += 1
            
            # Create text chunks for requirements to be searchable via BM25/Chroma
            text = f"Parameter: {req.get('test_parameter', '')} | Method: {req.get('test_method', '')} | Sampling: {req.get('sampling_requirement', '')}"
            prov = {
                "clause_reference": req.get("clause_reference"),
                "table_index": req.get("table_index"),
                "row_index": req.get("row_index")
            }
            chunk = SITEVidenceUnit(record, text, result["chunks_created"], prov)
            self.bm25_text_index[chunk.chunk_id] = chunk
            self.chroma_text_index[chunk.chunk_id] = chunk
            result["chunks_created"] += 1
        
        result["status"] = "INTEGRATED"
        return result

    def retrieve(self, query: str, active_only: bool = True, standard_identity: Optional[str] = None) -> List[SITEVidenceUnit]:
        results = []
        for chunk in self.chroma_text_index.values():
            if SITRelevanceGate.validate(query, chunk):
                if active_only and chunk.lifecycle_status in ["SUPERSEDED", "WITHDRAWN", "HISTORICAL"]:
                    continue
                if standard_identity and chunk.standard_identity != standard_identity:
                    continue
                results.append(chunk)
        return results

    def conflict_resolution(self, chunks: List[SITEVidenceUnit]) -> List[SITEVidenceUnit]:
        active_chunks = [c for c in chunks if c.lifecycle_status == "ACTIVE"]
        identities = set([c.canonical_identity for c in active_chunks])
        if len(identities) > 1:
            return [] # Conflict abstraction
        return active_chunks

    def resolve_multi_hop_product_sit(self, product_id: str, product_standard_graph: Dict[str, List[str]]) -> List[str]:
        # Product -> Standard graph (mock passed in) maps product to standard_identities
        # self.structured_relationships maps sit_id to standard_identities
        standards_for_product = product_standard_graph.get(product_id, [])
        sits = []
        for rel in self.structured_relationships:
            if rel.get("standard_identity") in standards_for_product:
                sits.append(rel["sit_document_id"])
        # We explicitly return hops, we do NOT infer a direct relationship
        return list(set(sits))
