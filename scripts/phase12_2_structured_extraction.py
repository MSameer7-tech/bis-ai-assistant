import json
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

V22_PATH = "data/bootstrap/bis_missing_domains_dataset_v22.jsonl"
V22_EXPECTED_SHA = "68229fbe37078b6571da7a0b71747fd4b5b383f232b796c71ae6e773c0c13dbe"

DERIVED_DIR = Path("data/derived/phase12")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = DERIVED_DIR / "structured_knowledge_v1.jsonl"
MANIFEST_PATH = DERIVED_DIR / "structured_knowledge_v1_manifest.json"

class Relationship:
    def __init__(self, target_id, rel_type):
        self.target_knowledge_id = target_id
        self.relationship_type = rel_type

    def to_dict(self):
        return {
            "target_knowledge_id": self.target_knowledge_id,
            "relationship_type": self.relationship_type
        }

class DerivedKnowledge:
    def __init__(self, kn_id, src_id, domain, kn_type, title, subject, content, authority, evidence_status):
        self.knowledge_id = kn_id
        self.source_record_id = src_id
        self.corpus_version = "v22"
        self.domain = domain
        self.knowledge_type = kn_type
        self.title = title
        self.subject = subject
        self.content = content
        self.authority = authority
        self.evidence_status = evidence_status
        self.entities = {"is_numbers": [], "products": [], "lab_codes": []}
        self.relationships = []
        self.provenance = {}
        self.effective_date = "UNKNOWN"
        self.validity = "UNKNOWN"
        self.supersession = {"is_superseded": False, "superseded_by": "UNKNOWN"}
        self.accessibility = "UNKNOWN"
        self.raw_entities = {}

    def to_dict(self):
        return {
            "knowledge_id": self.knowledge_id,
            "source_record_id": self.source_record_id,
            "corpus_version": self.corpus_version,
            "domain": self.domain,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "subject": self.subject,
            "content": self.content,
            "entities": self.entities,
            "raw_entities": self.raw_entities,
            "relationships": [r.to_dict() for r in self.relationships],
            "authority": self.authority,
            "source": self.provenance.get("source", {}),
            "provenance": self.provenance,
            "effective_date": self.effective_date,
            "validity": self.validity,
            "supersession": self.supersession,
            "accessibility": self.accessibility,
            "evidence_status": self.evidence_status
        }

def extract_is_number(text):
    if not text:
        return "UNKNOWN", "UNKNOWN"
    match = re.search(r'(IS\s*\d+)', text, re.IGNORECASE)
    if match:
        norm = match.group(1).replace(" ", "").upper().replace("IS", "IS ")
        return norm, text
    return "UNKNOWN", "UNKNOWN"

def get_provenance(rec):
    sha = rec.get("source_sha256")
    return {
        "source_record_id": rec.get("record_id"),
        "corpus_version": "v22",
        "source_url": rec.get("source_url"),
        "source_type": rec.get("source_type", "UNKNOWN"),
        "issuing_authority": rec.get("authority", "UNKNOWN"),
        "source_sha256": sha,
        "retrieved_at": rec.get("retrieved_at", "UNKNOWN"),
        "provenance_status": "PROVENANCE_COMPLETE" if sha else "PROVENANCE_INCOMPLETE",
        "original_title": rec.get("title", "UNKNOWN")
    }

class Extractor:
    def extract(self, rec):
        rec_id = rec.get("record_id")
        domain = rec.get("domain", "UNKNOWN")
        authority = rec.get("authority", "UNKNOWN")
        title = rec.get("title", "UNKNOWN")
        rec_type = rec.get("record_type", "UNKNOWN")
        content_str = str(rec.get("content", ""))
        
        # Rule 18: Invalid Record specific handling
        if rec_id == "LAB-UNKNOWN_79dcb12d":
            k = DerivedKnowledge(
                kn_id=f"dk_{rec_id}",
                src_id=rec_id,
                domain=domain,
                kn_type="UNKNOWN",
                title=title,
                subject="Invalid Record",
                content=content_str,
                authority=authority,
                evidence_status=rec.get("evidence_status", "NOT_ESTABLISHED")
            )
            k.provenance = get_provenance(rec)
            k.accessibility = rec.get("accessibility_status", "UNKNOWN")
            return [k]

        entities_yielded = []
        
        # Check if record has explicit entity data
        entity_data = rec.get("entity", {})
        
        if rec_type in ["RECOGNIZED_LAB", "BIS_OWNED_LAB", "RECOGNIZED_LABORATORY"]:
            lab_code = entity_data.get("lab_code") or rec.get("lab_code", "UNKNOWN")
            lab_name = entity_data.get("lab_name") or title
            validity = entity_data.get("validity_date") or rec.get("validity_date", "UNKNOWN")
            address = entity_data.get("address", "UNKNOWN")
            
            lab_k = DerivedKnowledge(
                kn_id=f"dk_{rec_id}_lab",
                src_id=rec_id,
                domain=domain,
                kn_type="LABORATORIES",
                title=lab_name,
                subject="Laboratory Entity",
                content=json.dumps({"lab_name": lab_name, "lab_code": lab_code, "address": address}),
                authority=authority,
                evidence_status="AVAILABLE_EVIDENCE"
            )
            lab_k.provenance = get_provenance(rec)
            lab_k.accessibility = "ACCESSIBLE"
            lab_k.validity = validity
            if lab_code != "UNKNOWN":
                lab_k.entities["lab_codes"].append(lab_code)
                
            entities_yielded.append(lab_k)
            
            # Note: For our new tests, we need to handle the mock test data format too.
            # If the mock test payload has "scopes" inside content:
            try:
                c_json = json.loads(content_str)
                if isinstance(c_json, dict) and "scopes" in c_json:
                    scopes = c_json.get("scopes", [])
                    for i, scope in enumerate(scopes):
                        norm_is, raw_is = extract_is_number(scope.get("is_number", ""))
                        scope_k = DerivedKnowledge(
                            kn_id=f"dk_{rec_id}_scope_{i}",
                            src_id=rec_id,
                            domain=domain,
                            kn_type="LAB_SCOPE",
                            title=f"Scope for {norm_is}",
                            subject="Laboratory Scope",
                            content=json.dumps(scope),
                            authority=authority,
                            evidence_status="AVAILABLE_EVIDENCE"
                        )
                        scope_k.provenance = get_provenance(rec)
                        scope_k.accessibility = "ACCESSIBLE"
                        scope_k.entities["is_numbers"].append(norm_is)
                        scope_k.raw_entities["is_number_raw"] = raw_is
                        
                        lab_k.relationships.append(Relationship(scope_k.knowledge_id, "HAS_SCOPE"))
                        scope_k.relationships.append(Relationship(lab_k.knowledge_id, "BELONGS_TO_LAB"))
                        if norm_is != "UNKNOWN":
                            scope_k.relationships.append(Relationship(f"std_{norm_is}", "TESTS_STANDARD"))
                        entities_yielded.append(scope_k)
                        
                        if "fee" in scope:
                            fee_k = DerivedKnowledge(
                                kn_id=f"dk_{rec_id}_fee_{i}",
                                src_id=rec_id,
                                domain=domain,
                                kn_type="TESTING_FEE",
                                title=f"Testing Fee for {norm_is}",
                                subject="Testing Fee",
                                content=json.dumps({"fee": scope.get("fee")}),
                                authority=authority,
                                evidence_status="AVAILABLE_EVIDENCE"
                            )
                            fee_k.provenance = get_provenance(rec)
                            fee_k.accessibility = "ACCESSIBLE"
                            fee_k.relationships.append(Relationship(scope_k.knowledge_id, "FEE_FOR_SCOPE"))
                            scope_k.relationships.append(Relationship(fee_k.knowledge_id, "HAS_FEE"))
                            entities_yielded.append(fee_k)
            except:
                pass
                
        elif rec_type == "LAB_SCOPE_TEST_CHARGE":
            lab_code = entity_data.get("lab_code", "UNKNOWN")
            raw_is = entity_data.get("standard_reference", "")
            norm_is, _ = extract_is_number(raw_is)
            test_param = entity_data.get("test", "UNKNOWN")
            fee_amount = entity_data.get("testing_charge_excluding_taxes_inr")
            
            # Scope Knowledge
            scope_k = DerivedKnowledge(
                kn_id=f"dk_{rec_id}_scope",
                src_id=rec_id,
                domain=domain,
                kn_type="LAB_SCOPE",
                title=f"Scope: {norm_is} ({lab_code})",
                subject="Laboratory Scope",
                content=json.dumps({
                    "lab_code": lab_code, 
                    "standard": raw_is, 
                    "test": test_param
                }),
                authority=authority,
                evidence_status="AVAILABLE_EVIDENCE"
            )
            scope_k.provenance = get_provenance(rec)
            scope_k.accessibility = "ACCESSIBLE"
            if norm_is != "UNKNOWN":
                scope_k.entities["is_numbers"].append(norm_is)
                scope_k.raw_entities["is_number_raw"] = raw_is
                scope_k.relationships.append(Relationship(f"std_{norm_is}", "TESTS_STANDARD"))
            if lab_code != "UNKNOWN":
                scope_k.entities["lab_codes"].append(lab_code)
                scope_k.relationships.append(Relationship(f"lab_{lab_code}", "BELONGS_TO_LAB"))
                
            entities_yielded.append(scope_k)
            
            # Fee Knowledge
            if fee_amount is not None:
                fee_k = DerivedKnowledge(
                    kn_id=f"dk_{rec_id}_fee",
                    src_id=rec_id,
                    domain=domain,
                    kn_type="TESTING_FEE",
                    title=f"Testing Fee: {norm_is} ({lab_code})",
                    subject="Testing Fee",
                    content=json.dumps({
                        "test_parameter": test_param,
                        "amount_inr": fee_amount,
                        "exclusion_taxes": True
                    }),
                    authority=authority,
                    evidence_status="AVAILABLE_EVIDENCE"
                )
                fee_k.provenance = get_provenance(rec)
                fee_k.accessibility = "ACCESSIBLE"
                fee_k.relationships.append(Relationship(scope_k.knowledge_id, "FEE_FOR_SCOPE"))
                scope_k.relationships.append(Relationship(fee_k.knowledge_id, "HAS_FEE"))
                entities_yielded.append(fee_k)

        else:
            # Fallback document extraction
            k = DerivedKnowledge(
                kn_id=f"dk_{rec_id}",
                src_id=rec_id,
                domain=domain,
                kn_type="DOCUMENT",
                title=title,
                subject="General Document",
                content=content_str[:1000] + "..." if len(content_str) > 1000 else content_str,
                authority=authority,
                evidence_status="AVAILABLE_EVIDENCE" if content_str else "MISSING_EVIDENCE"
            )
            k.provenance = get_provenance(rec)
            k.accessibility = "ACCESSIBLE" if content_str else "INACCESSIBLE_SOURCE"
            entities_yielded.append(k)

        return entities_yielded

def check_sha(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def run():
    print("Checking initial v22 SHA-256...")
    initial_sha = check_sha(V22_PATH)
    if initial_sha != V22_EXPECTED_SHA:
        raise ValueError(f"v22 SHA changed! Expected {V22_EXPECTED_SHA}, got {initial_sha}")
    
    records = []
    with open(V22_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    if len(records) != 1135:
        raise ValueError(f"v22 record count changed! Expected 1135, got {len(records)}")

    print(f"Loaded {len(records)} records. Extracting...")
    
    extractor = Extractor()
    derived_entities = []
    
    stats = {
        "input_records": len(records),
        "derived_records": 0,
        "entity_counts": {},
        "relationship_counts": {},
        "unknown_counts": 0,
        "inaccessible_counts": 0,
        "extraction_failures": 0
    }
    
    for rec in records:
        try:
            entities = extractor.extract(rec)
            derived_entities.extend(entities)
        except Exception as e:
            stats["extraction_failures"] += 1

    stats["derived_records"] = len(derived_entities)
    
    for e in derived_entities:
        stats["entity_counts"][e.knowledge_type] = stats["entity_counts"].get(e.knowledge_type, 0) + 1
        for rel in e.relationships:
            stats["relationship_counts"][rel.relationship_type] = stats["relationship_counts"].get(rel.relationship_type, 0) + 1
        if e.accessibility == "INACCESSIBLE_SOURCE":
            stats["inaccessible_counts"] += 1
        if e.evidence_status in ["UNKNOWN", "NOT_ESTABLISHED"]:
            stats["unknown_counts"] += 1
            
    print(f"Writing {len(derived_entities)} derived entities...")
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        for e in derived_entities:
            f.write(json.dumps(e.to_dict(), sort_keys=True) + "\n")
            
    derived_sha = check_sha(OUT_PATH)
    final_sha = check_sha(V22_PATH)
    
    if final_sha != V22_EXPECTED_SHA:
        raise ValueError(f"v22 SHA changed AFTER extraction! Expected {V22_EXPECTED_SHA}, got {final_sha}")
        
    manifest = {
        "input_corpus": V22_PATH,
        "input_sha256": V22_EXPECTED_SHA,
        "input_record_count": 1135,
        "derived_dataset_path": str(OUT_PATH),
        "derived_dataset_sha256": derived_sha,
        "stats": stats,
        # Using a deterministic timestamp for reproducibility
        "timestamp": "2026-09-04T12:00:00Z"
    }
    
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    print("Done.")

if __name__ == "__main__":
    run()
