import json
from .schemas import EvidenceObject

def select_evidence(retrieval_results, retrieval_data, top_n=10) -> list[EvidenceObject]:
    """Select diverse and structured evidence mapped into EvidenceObjects."""
    selected = []
    seen_types = set()
    
    # Priority: exact matches first, then authority, then diversity
    sorted_results = sorted(
        retrieval_results["results"],
        key=lambda r: (
            -1 if r.get("exact_match") else 0,
            r.get("authority_rank", 4),
            -r.get("fusion_score", 0.0)
        )
    )
    
    for cand in sorted_results:
        if len(selected) >= top_n:
            break
            
        rid = cand["retrieval_unit_id"]
        unit = retrieval_data.unit_by_id.get(rid, {})
        sid = unit.get("source_record_id")
        etype = unit.get("entity_type")
        
        # Diversity check: allow multiple of same type if exact match, else penalize redundancy
        if not cand.get("exact_match") and etype in seen_types and len(selected) >= 5:
            continue
            
        seen_types.add(etype)
        
        # Hydrate from Phase 12.2 (Structured Knowledge)
        krec = retrieval_data.knowledge.get(sid, {})
        
        # Populate EvidenceObject
        ev = EvidenceObject(
            retrieval_unit_id=rid,
            entity_type=etype,
            source_record_id=sid,
            source_url=krec.get("source", {}).get("url"),
            source_title=krec.get("title"),
            authority=cand.get("authority_rank", 4),
            provenance_status=krec.get("provenance", {}).get("provenance_status"),
            text=unit.get("text")
        )
        
        # Explicit Entity Extraction from Phase 12.2 / Phase 12.3
        
        if etype == "STANDARD":
            ent_id = unit.get("entity_id", "")
            if ent_id.startswith("std_"):
                ev.standard_number = ent_id[4:]
            
            for r in retrieval_data.entities_by_type.get("STANDARD", []):
                if r["entity_id"] == ent_id:
                     ev.standard_title = r.get("title")
                     if "normalized_is" in r:
                          ev.standard_number = r["normalized_is"]
                     break
                     
            if not ev.standard_number and "is_numbers" in krec.get("entities", {}) and krec["entities"]["is_numbers"]:
                 ev.standard_number = krec["entities"]["is_numbers"][0]
                 
            if not ev.standard_title and "title" in krec and "IS " in krec["title"]:
                 ev.standard_title = krec["title"]
                 
            if "Revision" in (ev.standard_title or "") or "Supersedes" in unit.get("text", "") or cand.get("supersession_status") != "UNKNOWN":
                 ev.standard_revision = "Explicitly provided"

        elif etype in ("LAB_SCOPE", "TESTING_FEE", "LABORATORIES"):
            lims_details = {}
            relationships = []
            actual_entity = {}
            
            ent_id = unit.get("entity_id", "")
            for r in retrieval_data.entities_by_type.get(etype, []):
                 if r["entity_id"] == ent_id:
                      actual_entity = r
                      break
                      
            try:
                raw_data = actual_entity.get("raw_data", {})
                content = raw_data.get("content", "{}")
                if isinstance(content, str):
                    lims_details = json.loads(content)
                else:
                    lims_details = content
                
                for rel in raw_data.get("relationships", []):
                    relationships.append({
                        "subject": actual_entity.get("entity_id"),
                        "predicate": rel.get("relationship_type"),
                        "object": rel.get("target_knowledge_id")
                    })
            except Exception:
                pass
                
            title = actual_entity.get("title") or raw_data.get("title") or ""
                
            if etype == "LAB_SCOPE":
                ev.laboratory_id = lims_details.get("lab_code")
                ev.standard_number = lims_details.get("standard")
                if not ev.standard_number and "IS " in title:
                     ev.standard_number = "IS " + title.split("IS ")[1].split(" ")[0]
                if not ev.laboratory_id and "Lab " in title:
                     ev.laboratory_id = title.split("Lab ")[1].split(" ")[0]
                ev.test_parameter = lims_details.get("test_parameter")
                ev.test_method = lims_details.get("test_method")
                ev.validity_date = lims_details.get("validity")
                # Bind relationship manually if present in content
                if ev.laboratory_id and ev.standard_number:
                     ev.relationships.append({"subject": f"LABORATORY:{ev.laboratory_id}", "predicate": "HAS_SCOPE_FOR", "object": f"STANDARD:{ev.standard_number}"})

            elif etype == "TESTING_FEE":
                ev.laboratory_id = lims_details.get("lab_code")
                ev.laboratory_name = lims_details.get("lab_name")
                ev.standard_number = lims_details.get("standard")
                
                if not ev.standard_number and "IS " in title:
                     ev.standard_number = "IS " + title.split("IS ")[1].split(" ")[0]
                if not ev.laboratory_id and "(" in title:
                     ev.laboratory_id = title.split("(")[1].split(")")[0]
                     
                ev.test_parameter = lims_details.get("test_parameter")
                ev.clause = lims_details.get("clause")
                ev.fee_amount = lims_details.get("amount_inr") or lims_details.get("testing_charge")
                ev.fee_currency = lims_details.get("currency", "INR")
                ev.effective_date = lims_details.get("effective_date")
                ev.remarks = lims_details.get("remarks")
                
                if ev.standard_number and ev.fee_amount is not None:
                     ev.relationships.append({"subject": f"STANDARD:{ev.standard_number}", "predicate": "HAS_FEE", "object": str(ev.fee_amount)})
                     
            elif etype == "LABORATORIES":
                ev.laboratory_id = lims_details.get("lab_code")
                ev.laboratory_name = lims_details.get("lab_name") or krec.get("title")
                
        elif etype == "UNKNOWN":
            pass # Keep fields empty
            
        else:
            # General QCO, Registration, etc.
            ents = krec.get("entities", {})
            if ents.get("is_numbers"):
                 ev.standard_number = ents["is_numbers"][0]
            if ents.get("products"):
                 ev.product = ents["products"][0]
                 
            ev.document_title = krec.get("title")

        selected.append(ev)
        
    return selected
