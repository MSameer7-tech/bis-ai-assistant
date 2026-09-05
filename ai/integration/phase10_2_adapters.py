import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

class IntegrationProvenance:
    def __init__(self, data: Dict[str, Any]):
        self.source_url = data.get("source_url")
        self.final_url = data.get("final_url")
        self.source_sha256 = data.get("source_sha256")
        self.source_family = data.get("source_family")
        self.document_id = data.get("document_id")
        self.canonical_identity = data.get("canonical_identity")
        self.retrieved_at = data.get("retrieved_at")
        self.extraction_method = data.get("extraction_method")
        self.page = data.get("page")
        self.clause_reference = data.get("clause_reference")
        self.table_index = data.get("table_index")
        self.row_index = data.get("row_index")
        self.raw_artifact_reference = data.get("raw_artifact_reference")

    def to_dict(self):
        return self.__dict__

class IntegrationEligibility:
    @staticmethod
    def evaluate(record: Dict[str, Any], required_keys: List[str], excluded_states: List[str]) -> str:
        for ex in excluded_states:
            if record.get("status") == ex or record.get("identity_status") == ex or record.get("lifecycle_status") == ex:
                return ex
                
        special_states = ["UNCHANGED", "DUPLICATE_REPRESENTATION_ALIAS", "DISTINCT_DOCUMENT"]
        if record.get("status") in special_states:
            return record.get("status")

        if not record.get("canonical_identity"):
            return "IDENTITY_UNRESOLVED"

        for req in required_keys:
            if not record.get(req):
                return "INVALID_SCHEMA"
                
        if not record.get("source_sha256"):
            return "IDENTITY_UNRESOLVED"
            
        return "ELIGIBLE"

class IntegrationRecordEnvelope:
    def __init__(self, domain: str, record_type: str, source_record_id: str,
                 canonical_identity: str, authority: str, authority_level: str,
                 evidence_role: str, lifecycle_status: str, identity_status: str,
                 eligibility_status: str, payload: Dict[str, Any], provenance: Dict[str, Any],
                 relationships: List[Dict[str, Any]], source_sha256: str):
        self.integration_record_id = hashlib.sha256(f"{domain}_{source_record_id}_{source_sha256}".encode()).hexdigest()
        self.domain = domain
        self.record_type = record_type
        self.source_record_id = source_record_id
        self.canonical_identity = canonical_identity
        self.authority = authority
        self.authority_level = authority_level
        self.evidence_role = evidence_role
        self.lifecycle_status = lifecycle_status
        self.identity_status = identity_status
        self.eligibility_status = eligibility_status
        self.payload = payload
        self.provenance = provenance
        self.relationships = relationships
        self.source_sha256 = source_sha256
        self.schema_version = "1.0.0"

    def to_dict(self):
        return self.__dict__

class Phase91ActsAdapter:
    def normalize(self, raw_record: Dict[str, Any]) -> IntegrationRecordEnvelope:
        eligibility = IntegrationEligibility.evaluate(
            raw_record, 
            ["document_id", "source_sha256", "canonical_identity"], 
            ["CONTENT_CHANGED_REQUIRES_VERSION_REVIEW", "FETCH_FAILED", "ACCESS_RESTRICTED", "EXTRACTION_FAILED", "IDENTITY_UNRESOLVED", "AMBIGUOUS"]
        )
        
        payload = {
            "document_id": raw_record.get("document_id"),
            "canonical_identity": raw_record.get("canonical_identity"),
            "document_type": raw_record.get("document_type"),
            "title": raw_record.get("title"),
            "act_rule_number": raw_record.get("act_rule_number"),
            "year": raw_record.get("year"),
            "issuing_authority": raw_record.get("issuing_authority"),
            "source_family": "ACTS_RULES",
            "authority_level": "STATUTORY",
            "lifecycle_status": raw_record.get("lifecycle_status", "UNKNOWN"),
            "version_status": raw_record.get("version_status", "UNKNOWN"),
            "effective_from": raw_record.get("effective_from"),
            "effective_to": raw_record.get("effective_to"),
            "source_url": raw_record.get("source_url"),
            "final_url": raw_record.get("final_url"),
            "source_sha256": raw_record.get("source_sha256"),
            "retrieved_at": raw_record.get("retrieved_at"),
            "extraction_method": raw_record.get("extraction_method"),
            "raw_artifact_reference": raw_record.get("raw_artifact_reference"),
            "eligibility_status": eligibility
        }
        
        prov = IntegrationProvenance(payload).to_dict()
        
        return IntegrationRecordEnvelope(
            domain="ActsRules", record_type="StatutoryDocument",
            source_record_id=payload["document_id"], canonical_identity=payload["canonical_identity"],
            authority="BIS", authority_level="STATUTORY", evidence_role="STATUTORY_EVIDENCE",
            lifecycle_status=payload["lifecycle_status"], identity_status=raw_record.get("identity_status", "RESOLVED"),
            eligibility_status=eligibility, payload=payload, provenance=prov,
            relationships=[], source_sha256=payload["source_sha256"]
        )

class Phase92QCOAdapter:
    def normalize(self, raw_record: Dict[str, Any]) -> IntegrationRecordEnvelope:
        eligibility = IntegrationEligibility.evaluate(
            raw_record, 
            ["qco_id", "source_sha256", "canonical_identity"], 
            ["IDENTITY_UNRESOLVED", "CONFLICTING_EVIDENCE", "EXTRACTION_FAILED", "FETCH_FAILED", "AMBIGUOUS_RELATIONSHIP"]
        )
        
        payload = {
            "qco_id": raw_record.get("qco_id"),
            "canonical_identity": raw_record.get("canonical_identity"),
            "notification_number": raw_record.get("notification_number"),
            "ministry": raw_record.get("ministry"),
            "department": raw_record.get("department"),
            "publication_date": raw_record.get("publication_date"),
            "effective_date": raw_record.get("effective_date"),
            "title": raw_record.get("title"),
            "referenced_standard_numbers": raw_record.get("referenced_standard_numbers", []),
            "amendment_references": raw_record.get("amendment_references", []),
            "lifecycle_status": raw_record.get("lifecycle_status", "UNKNOWN"),
            "source_url": raw_record.get("source_url"),
            "final_url": raw_record.get("final_url"),
            "source_sha256": raw_record.get("source_sha256"),
            "retrieved_at": raw_record.get("retrieved_at"),
            "extraction_method": raw_record.get("extraction_method"),
            "raw_artifact_reference": raw_record.get("raw_artifact_reference"),
            "eligibility_status": eligibility
        }
        
        prov = IntegrationProvenance(payload).to_dict()
        
        relationships = []
        for std in payload.get("referenced_standard_numbers", []):
            rel = {
                "relationship_id": hashlib.sha256(f"qco_{payload['qco_id']}_std_{std}".encode()).hexdigest(),
                "qco_id": payload["qco_id"],
                "standard_number": std,
                "standard_identity": std if eligibility == "ELIGIBLE" else None,
                "relationship_type": "QCO_ENFORCES_STANDARD",
                "relationship_source": "GAZETTE_QCO",
                "relationship_status": "RESOLVED" if eligibility == "ELIGIBLE" else "UNRESOLVED",
                "provenance": prov
            }
            relationships.append(rel)
        
        return IntegrationRecordEnvelope(
            domain="QCOGazette", record_type="QCODocument",
            source_record_id=payload["qco_id"], canonical_identity=payload["canonical_identity"],
            authority="BIS", authority_level="REGULATORY", evidence_role="QCO_EVIDENCE",
            lifecycle_status=payload["lifecycle_status"], identity_status=raw_record.get("identity_status", "RESOLVED"),
            eligibility_status=eligibility, payload=payload, provenance=prov,
            relationships=relationships, source_sha256=payload["source_sha256"]
        )

class Phase93SITAdapter:
    def normalize(self, raw_record: Dict[str, Any]) -> IntegrationRecordEnvelope:
        eligibility = IntegrationEligibility.evaluate(
            raw_record, 
            ["sit_document_id", "source_sha256", "canonical_identity"], 
            ["IDENTITY_REVIEW_REQUIRED", "AMBIGUOUS_MATCH"]
        )
        
        payload = {
            "sit_document_id": raw_record.get("sit_document_id"),
            "canonical_identity": raw_record.get("canonical_identity"),
            "standard_number": raw_record.get("standard_number"),
            "standard_identity": raw_record.get("standard_identity"),
            "part": raw_record.get("part"),
            "section": raw_record.get("section"),
            "edition_year": raw_record.get("edition_year"),
            "sit_revision": raw_record.get("sit_revision"),
            "document_title": raw_record.get("document_title"),
            "document_type": raw_record.get("document_type", "SIT"),
            "lifecycle_status": raw_record.get("lifecycle_status", "UNKNOWN"),
            "source_url": raw_record.get("source_url"),
            "final_url": raw_record.get("final_url"),
            "source_sha256": raw_record.get("source_sha256"),
            "retrieved_at": raw_record.get("retrieved_at"),
            "extraction_method": raw_record.get("extraction_method"),
            "raw_artifact_reference": raw_record.get("raw_artifact_reference"),
            "eligibility_status": eligibility
        }
        
        prov = IntegrationProvenance(payload).to_dict()
        
        relationships = []
        if eligibility == "ELIGIBLE" and payload.get("standard_identity"):
            relationships.append({
                "relationship_id": hashlib.sha256(f"sit_{payload['sit_document_id']}_std_{payload['standard_identity']}".encode()).hexdigest(),
                "sit_document_id": payload["sit_document_id"],
                "standard_identity": payload["standard_identity"],
                "relationship_type": "STANDARD_HAS_SIT",
                "relationship_status": "RESOLVED",
                "provenance": prov
            })
            
        # Parse requirements if they exist
        requirements = []
        for req in raw_record.get("requirements", []):
            requirements.append({
                "requirement_id": hashlib.sha256(f"{payload['sit_document_id']}_{req.get('test_parameter')}".encode()).hexdigest(),
                "sit_document_id": payload["sit_document_id"],
                "standard_identity": payload["standard_identity"],
                "standard_number": payload["standard_number"],
                "test_parameter": req.get("test_parameter"),
                "test_method": req.get("test_method"),
                "sampling_requirement": req.get("sampling_requirement"),
                "frequency": req.get("frequency"),
                "acceptance_criteria": req.get("acceptance_criteria"),
                "clause_reference": req.get("clause_reference"),
                "page_number": req.get("page_number"),
                "table_index": req.get("table_index"),
                "row_index": req.get("row_index"),
                "eligibility_status": eligibility
            })
            
        payload["requirements"] = requirements
        
        return IntegrationRecordEnvelope(
            domain="SITTesting", record_type="SITDocument",
            source_record_id=payload["sit_document_id"], canonical_identity=payload["canonical_identity"],
            authority="BIS", authority_level="TECHNICAL_REQUIREMENT", evidence_role="SIT_EVIDENCE",
            lifecycle_status=payload["lifecycle_status"], identity_status=raw_record.get("identity_status", "RESOLVED"),
            eligibility_status=eligibility, payload=payload, provenance=prov,
            relationships=relationships, source_sha256=payload["source_sha256"]
        )
