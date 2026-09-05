import hashlib
from typing import Dict, Any, List, Optional

class QCOEvidenceUnit:
    def __init__(self, record_envelope: Dict[str, Any], text_chunk: str, chunk_index: int, provenance_overrides: Dict[str, Any] = None):
        self.chunk_id = hashlib.sha256(f"{record_envelope['integration_record_id']}_{chunk_index}".encode()).hexdigest()
        self.integration_record_id = record_envelope["integration_record_id"]
        self.canonical_identity = record_envelope["canonical_identity"]
        self.text_chunk = text_chunk
        self.evidence_role = "QCO_EVIDENCE"
        self.authority_level = record_envelope.get("authority_level", "REGULATORY")
        self.lifecycle_status = record_envelope.get("lifecycle_status", "ACTIVE")
        self.effective_date = record_envelope["payload"].get("effective_date")
        self.publication_date = record_envelope["payload"].get("publication_date")
        
        self.provenance = record_envelope.get("provenance", {}).copy()
        if provenance_overrides:
            self.provenance.update(provenance_overrides)

class QCORelevanceGate:
    @staticmethod
    def validate(query: str, evidence: QCOEvidenceUnit) -> bool:
        # Reject deeply technical queries that don't ask about QCOs
        technical_keywords = ["test method", "sampling frequency", "laboratory capability", "acceptance criteria"]
        query_lower = query.lower()
        if any(kw in query_lower for kw in technical_keywords):
            # Only allow if the query specifically mentions QCO/mandatory
            if "qco" not in query_lower and "mandatory" not in query_lower:
                return False
                
        # Accept if it's asking about QCOs, mandatory status, effective dates, ministries, etc
        qco_keywords = ["qco", "mandatory", "effective date", "ministry", "notification", "gazette", "standard"]
        if any(kw in query_lower for kw in qco_keywords):
            return True
            
        return False

class Phase10QCOIndex:
    def __init__(self):
        self.structured_metadata_index = {}
        self.structured_relationships = []
        self.bm25_text_index = {}
        self.chroma_text_index = {}
        
    def integrate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "status": "EXCLUDED",
            "chunks_created": 0,
            "relationships_integrated": 0,
            "reason": None
        }
        
        if record.get("eligibility_status") != "ELIGIBLE":
            result["reason"] = f"Ineligible status: {record.get('eligibility_status')}"
            return result
            
        if record.get("evidence_role") != "QCO_EVIDENCE":
            result["reason"] = "Role mismatch"
            return result
            
        qco_id = record["payload"]["qco_id"]
        self.structured_metadata_index[qco_id] = record["payload"]
        
        for rel in record.get("relationships", []):
            if rel.get("relationship_status") == "RESOLVED":
                self.structured_relationships.append(rel)
                result["relationships_integrated"] += 1
                
        text = record["payload"].get("title", "") + " " + record["payload"].get("notification_number", "")
        chunk = QCOEvidenceUnit(record, text, 0)
        
        self.bm25_text_index[chunk.chunk_id] = chunk
        self.chroma_text_index[chunk.chunk_id] = chunk
        
        result["status"] = "INTEGRATED"
        result["chunks_created"] = 1
        return result

    def retrieve(self, query: str, request_date: Optional[str] = None, active_only: bool = True) -> List[QCOEvidenceUnit]:
        results = []
        for chunk in self.chroma_text_index.values():
            if QCORelevanceGate.validate(query, chunk):
                if active_only and chunk.lifecycle_status in ["SUPERSEDED", "WITHDRAWN", "HISTORICAL"]:
                    continue
                
                # Effective date filtering logic
                if request_date and chunk.effective_date:
                    # Very simple string comparison for simulation (e.g. "2023-01-01" <= "2024-01-01")
                    if chunk.effective_date > request_date:
                        # QCO not yet effective on requested date
                        continue
                        
                results.append(chunk)
        return results

    def conflict_resolution(self, chunks: List[QCOEvidenceUnit]) -> List[QCOEvidenceUnit]:
        active_chunks = [c for c in chunks if c.lifecycle_status == "ACTIVE"]
        identities = set([c.canonical_identity for c in active_chunks])
        if len(identities) > 1:
            return []
        return active_chunks

    def resolve_multi_hop_product_qco(self, product_id: str, product_standard_graph: Dict[str, List[str]]) -> List[str]:
        # Product -> Standard graph (mock passed in) maps product to standard_identities
        # self.structured_relationships maps qco to standard_identities
        standards_for_product = product_standard_graph.get(product_id, [])
        qcos = []
        for rel in self.structured_relationships:
            if rel["standard_identity"] in standards_for_product:
                qcos.append(rel["qco_id"])
        # We only RETURN the multi-hop path elements, we do NOT mint a direct edge.
        return list(set(qcos))
