from .schemas import QueryIntent, EvidenceStatus

def evaluate_sufficiency(query, intent, identifiers, selected_evidence):
    """
    Evaluate if evidence is sufficient based on dynamic requirements for a single intent.
    Returns (status, gaps).
    """
    gaps = []
    
    # Extract entities present in evidence
    evidence_types = {e["entity_type"] for e in selected_evidence}
    has_lab = "LABORATORIES" in evidence_types
    has_fee = "TESTING_FEE" in evidence_types
    has_scope = "LAB_SCOPE" in evidence_types
    has_standard = "STANDARD" in evidence_types or any("IS " in e.get("title", "") for e in selected_evidence)
    
    # 1. Unknown entity
    if intent == QueryIntent.UNKNOWN:
        if identifiers.get("source_ids") and any("UNKNOWN" in sid for sid in identifiers["source_ids"]):
            return EvidenceStatus.INSUFFICIENT, [{"gap_type": "UNKNOWN_INTENT", "message": "Query references an explicitly UNKNOWN entity."}]
        elif "unknown" in query.lower():
            return EvidenceStatus.INSUFFICIENT, [{"gap_type": "UNKNOWN_INTENT", "message": "Query intentionally references an UNKNOWN state."}]
        return EvidenceStatus.INSUFFICIENT, [{"gap_type": "UNKNOWN_INTENT", "message": "Query intent could not be mapped to required evidence."}]

    # 2. Dynamic fee query requirements
    if intent == QueryIntent.TESTING_FEE:
        if not has_fee:
            gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "testing_fee", "severity": "HIGH", "message": "No explicit testing fee was found in the authoritative evidence."})
            return EvidenceStatus.INSUFFICIENT, gaps
        
        # Check if we have total vs clause
        has_total = any(
             "TESTING_FEE" == e["entity_type"] and ("complete testing" in str(e.get("lims_details", {}).get("test_parameter", "")).lower() or "total" in str(e.get("lims_details", {}).get("test_parameter", "")).lower()) 
             for e in selected_evidence
        )
        if not has_total:
             gaps.append({"gap_type": "PARTIAL_EVIDENCE", "field": "testing_fee_total", "severity": "MEDIUM", "message": "Detailed clause charges exist but no total fee is specified."})
             return EvidenceStatus.PARTIAL, gaps
             
        # If IS is specified in query but not in evidence
        if identifiers.get("is_numbers") and not any(idn in str(e) for e in selected_evidence for idn in identifiers["is_numbers"]):
            gaps.append({"gap_type": "PARTIAL_EVIDENCE", "field": "is_number", "severity": "MEDIUM", "message": "Fee found but may not apply to the requested IS."})
            return EvidenceStatus.PARTIAL, gaps
            
        return EvidenceStatus.SUFFICIENT, gaps
        
    # 3. Dynamic lab query requirements
    if intent == QueryIntent.LABORATORY_LOOKUP:
        if not has_lab and not has_scope:
            gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "laboratory", "severity": "HIGH", "message": "No explicit laboratory evidence found."})
            return EvidenceStatus.INSUFFICIENT, gaps
        
        if (identifiers.get("is_numbers") or "cement" in query.lower()) and not has_scope:
             gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "laboratory_scope", "severity": "HIGH", "message": "Laboratory found but specific testing scope for the IS/product is missing."})
             return EvidenceStatus.INSUFFICIENT, gaps
             
        if not has_scope:
            return EvidenceStatus.PARTIAL, [{"gap_type": "PARTIAL_EVIDENCE", "message": "Laboratory existence confirmed but scope details absent."}]
            
        return EvidenceStatus.SUFFICIENT, gaps

    # 4. Certification / QCO
    if intent in (QueryIntent.CERTIFICATION_REQUIREMENT, QueryIntent.QCO_APPLICABILITY):
        qco_evidence = any("QCO" in str(e.get("text", "")) or "Compulsory" in str(e.get("title", "")) or "Mandatory" in str(e.get("title", "")) for e in selected_evidence)
        if not qco_evidence:
            gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "qco_applicability", "severity": "HIGH", "message": "No explicit evidence of mandatory certification (QCO) found."})
            return EvidenceStatus.INSUFFICIENT, gaps
            
        # Very specific product query vs general QCO
        if identifiers.get("entities") and not any(any(ent in str(e) for ent in identifiers["entities"]) for e in selected_evidence):
             gaps.append({"gap_type": "PARTIAL_EVIDENCE", "field": "qco_applicability", "severity": "MEDIUM", "message": "QCO found but may not explicitly apply to the requested product."})
             return EvidenceStatus.PARTIAL, gaps
             
        return EvidenceStatus.SUFFICIENT, gaps
        
    # 5. Historical version / latest
    if intent == QueryIntent.HISTORICAL_VERSION:
        if not has_standard:
             gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "standard", "severity": "HIGH", "message": "No standard found."})
             return EvidenceStatus.INSUFFICIENT, gaps
             
        revision_evidence = any(
            e.get("supersession") != "UNKNOWN" or "Revision" in e.get("title", "") or "Supersedes" in e.get("text", "") 
            for e in selected_evidence if e["entity_type"] == "STANDARD"
        )
        if not revision_evidence:
            gaps.append({"gap_type": "MISSING_EVIDENCE", "field": "revision_status", "severity": "HIGH", "message": "No explicit evidence of revision or latest status found."})
            return EvidenceStatus.INSUFFICIENT, gaps
            
        return EvidenceStatus.SUFFICIENT, gaps
        
    # Fallback
    if not selected_evidence:
        return EvidenceStatus.NO_EVIDENCE, [{"gap_type": "NO_EVIDENCE", "message": "No evidence retrieved."}]
        
    return EvidenceStatus.SUFFICIENT, gaps
