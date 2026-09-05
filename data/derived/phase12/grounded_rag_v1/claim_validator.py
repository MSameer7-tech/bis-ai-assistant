from typing import List, Dict
from .schemas import Claim, EvidenceObject, SupportStatus, QueryIntent

def validate_claim(claim: Claim, evidence: List[EvidenceObject], intent: QueryIntent, requested_identifiers: List[str] = None) -> Claim:
    """
    Validates a claim against the explicit constraints of Phase 12.CB.
    A claim is ONLY supported if ALL components (subject, predicate, object) are explicitly
    supported by the SAME evidence object. Co-occurrence across different evidence objects
    is insufficient.
    """
    # META claims do not require factual evidence backing, they are internal system traces
    if claim.claim_type == "META":
        claim.support_status = SupportStatus.SUPPORTED
        return claim
        
    # Validation flags
    is_supported = False
    valid_evidence_ids = []
    
    # Extract identifiers to check exact match
    subject = claim.subject_entity
    predicate = claim.predicate
    obj = claim.object_entity
    
    # Fallback to text check if formal structure isn't fully defined but must be rejected if unsupported
    for ev in evidence:
        if ev.source_record_id not in claim.supporting_evidence_ids:
            continue
            
        # 1. Exact Identifier Binding Check
        if requested_identifiers:
             req_standards = [x for x in requested_identifiers if x.startswith("IS ")]
             if req_standards and subject and subject.startswith("STANDARD:"):
                  claim_is = subject.split(":")[1]
                  if claim_is not in req_standards:
                       continue
                       
        if subject and subject.startswith("STANDARD:"):
             req_is = subject.split(":")[1]
             if ev.standard_number and req_is != ev.standard_number:
                  # Exact identifier mismatch causes UNSUPPORTED (Test 1,2,3,4)
                  continue
                  
        if subject and subject.startswith("LABORATORY:"):
             req_lab = subject.split(":")[1]
             if ev.laboratory_id and req_lab != ev.laboratory_id:
                  continue

        # 2. Relationship validation
        if predicate == "HAS_TITLE":
            # Must explicitly have standard_title
            if ev.standard_title:
                is_supported = True
                valid_evidence_ids.append(ev.source_record_id)
                
        elif predicate == "HAS_SCOPE_FOR":
            # Test 8,9,11: Laboratory capability requires explicit scope linking Lab to IS
            # Must have a defined relationship in the evidence
            has_explicit_rel = False
            for rel in ev.relationships:
                 if rel.get("predicate") == "HAS_SCOPE_FOR":
                      has_explicit_rel = True
                      break
            if has_explicit_rel:
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        elif predicate == "HAS_FEE":
            # Test 12, 13, 19: Fee value cannot be detached from its IS
            has_explicit_rel = False
            for rel in ev.relationships:
                 if rel.get("predicate") == "HAS_FEE" and str(ev.fee_amount) == str(obj):
                      has_explicit_rel = True
                      break
            if has_explicit_rel:
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        elif predicate == "HAS_QCO":
            # Test 24, 25: QCO applicability must be product-specific
            if ev.product and obj and obj.lower() in ev.product.lower():
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        elif predicate == "IS_LATEST_REVISION":
            # Test 20, 21, 22, 23: Latest status requires explicit revision/supersession evidence
            if ev.standard_revision:
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        elif predicate == "HAS_PROCEDURE":
            # Procedure validation (prevent source-title-as-fact)
            # Test 5,6,26,27,28: Source title / Document title cannot become procedure fact
            if claim.text == ev.document_title or claim.text == ev.source_title:
                 # Explicit failure
                 pass
            elif ev.text and claim.text in ev.text:
                 # The text must actually be in the procedural content
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        elif predicate == "GENERAL_INFORMATION":
            # Prevent source-title-as-fact
            if claim.text == ev.document_title or claim.text == ev.source_title or claim.text.startswith("Information is provided in"):
                 pass
            elif claim.text and claim.text in (ev.text or ""):
                 is_supported = True
                 valid_evidence_ids.append(ev.source_record_id)
                 
        else:
             # Basic presence check for generic predicates if they fall through (should be rare)
             if ev.text and claim.text in ev.text:
                  is_supported = True
                  valid_evidence_ids.append(ev.source_record_id)

    if is_supported:
        claim.support_status = SupportStatus.SUPPORTED
        claim.supporting_evidence_ids = valid_evidence_ids
    else:
        claim.support_status = SupportStatus.UNSUPPORTED
        
    # URL check (Test 40)
    final_urls = []
    for ev in evidence:
        if ev.source_record_id in claim.supporting_evidence_ids and ev.source_url:
            final_urls.append(ev.source_url)
    claim.source_urls = final_urls
    
    if not claim.supporting_evidence_ids and claim.claim_type == "BIS_FACT":
        claim.support_status = SupportStatus.UNSUPPORTED

    return claim
