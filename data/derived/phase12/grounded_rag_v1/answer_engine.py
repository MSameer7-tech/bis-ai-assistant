import json
import re
import os
import sys

# To allow importing from Phase 12.B
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from scripts.phase12_b_hybrid_retrieval import RetrievalData, hybrid_retrieve
from .schemas import QueryIntent, EvidenceStatus, Claim, SupportStatus
from .evidence_selector import select_evidence
from .sufficiency import evaluate_sufficiency
from .confidence import calculate_confidence
from .citation_builder import build_citations
from .query_decomposer import decompose_query
from .claim_validator import validate_claim

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def generate_claims_and_text(subquestion, evidence, status, citations, gaps, requested_identifiers=None):
    """
    Deterministic generation of claims and prose from evidence for a specific subquestion.
    """
    claims = []
    unsupported_claims = []
    text_parts = []
    intent = subquestion.intent
    
    if status in (EvidenceStatus.NO_EVIDENCE, EvidenceStatus.INSUFFICIENT):
        text_parts.append("I could not verify this from the available BIS evidence.")
        if gaps:
            text_parts.append("\nMissing:")
            for g in gaps:
                text_parts.append(f"- {g.get('message')}")
        
        claims.append(Claim(
            claim_id=f"c_{intent.name}_0",
            claim_type="META",
            text="The available evidence is insufficient to answer the query.",
            supporting_evidence_ids=[],
            support_status=SupportStatus.SUPPORTED
        ))
        return "\n".join(text_parts), claims, unsupported_claims
        
    if status == EvidenceStatus.PARTIAL:
         text_parts.append("The available BIS evidence provides partial information.")
         if gaps:
            for g in gaps:
                text_parts.append(f"- Limitation: {g.get('message')}")
                
    # Build text based on intent and available evidence
    if intent == QueryIntent.TESTING_FEE:
        has_total = False
        text_parts.append("The available LIMS evidence lists the following testing charges:")
        
        for i, ev in enumerate(evidence):
            if ev.entity_type == "TESTING_FEE":
                is_num = ev.standard_number or "UNKNOWN_IS"
                lab = ev.laboratory_name or ev.laboratory_id or "UNKNOWN_LAB"
                param = ev.test_parameter or ev.clause or "testing"
                fee = ev.fee_amount
                curr = ev.fee_currency or "INR"
                date = ev.effective_date
                
                if fee is not None:
                    claim_text = f"At {lab}, the charge for {param} under {is_num} is {curr} {fee}."
                    if date:
                        claim_text = f"At {lab}, the charge for {param} under {is_num} is {curr} {fee}, effective {date}."
                        
                    claims.append(Claim(
                        claim_id=f"c_{intent.name}_{i}",
                        claim_type="BIS_FACT",
                        text=claim_text,
                        subject_entity=f"STANDARD:{is_num}",
                        predicate="HAS_FEE",
                        object_entity=str(fee),
                        supporting_evidence_ids=[ev.source_record_id],
                        support_status=SupportStatus.UNSUPPORTED # Pending validation
                    ))
                    
                    if "complete testing" in param.lower() or "total" in param.lower():
                        has_total = True
                        
        if not has_total:
             text_parts.append("\nThe source does not establish that these constitute the complete testing cost.")
             
    elif intent == QueryIntent.QCO_APPLICABILITY:
        text_parts.append("The retrieved evidence indicates the following regarding mandatory certification:")
        for i, ev in enumerate(evidence):
             if ev.text and ("QCO" in ev.text or "Compulsory" in ev.document_title or "Mandatory" in ev.document_title):
                  title = ev.document_title or "the relevant Quality Control Order"
                  claim_text = f"Mandatory certification (QCO) applies according to {title}."
                  claims.append(Claim(
                      claim_id=f"c_{intent.name}_{i}",
                      claim_type="BIS_FACT",
                      text=claim_text,
                      subject_entity=ev.product or "GENERAL_PRODUCT",
                      predicate="HAS_QCO",
                      object_entity=title,
                      supporting_evidence_ids=[ev.source_record_id],
                      support_status=SupportStatus.UNSUPPORTED
                  ))
                  
    elif intent == QueryIntent.LABORATORY_LOOKUP:
         for i, ev in enumerate(evidence):
             if ev.entity_type == "LAB_SCOPE":
                 lab = ev.laboratory_id or "UNKNOWN_LAB"
                 is_num = ev.standard_number or "UNKNOWN_IS"
                 claim_text = f"Laboratory {lab} is listed with testing scope for {is_num}."
                 claims.append(Claim(
                      claim_id=f"c_{intent.name}_{i}",
                      claim_type="BIS_FACT",
                      text=claim_text,
                      subject_entity=f"LABORATORY:{lab}",
                      predicate="HAS_SCOPE_FOR",
                      object_entity=f"STANDARD:{is_num}",
                      supporting_evidence_ids=[ev.source_record_id],
                      support_status=SupportStatus.UNSUPPORTED
                 ))
    
    elif intent == QueryIntent.HISTORICAL_VERSION:
         for i, ev in enumerate(evidence):
             if ev.entity_type == "STANDARD" or ev.standard_revision:
                 title = ev.standard_title or ev.document_title or "UNKNOWN_TITLE"
                 claim_text = f"The current version is {title}."
                 claims.append(Claim(
                      claim_id=f"c_{intent.name}_{i}",
                      claim_type="BIS_FACT",
                      text=claim_text,
                      subject_entity=f"STANDARD:{ev.standard_number or 'UNKNOWN_IS'}",
                      predicate="IS_LATEST_REVISION",
                      object_entity=title,
                      supporting_evidence_ids=[ev.source_record_id],
                      support_status=SupportStatus.UNSUPPORTED
                 ))
                 
    elif intent == QueryIntent.STANDARD_LOOKUP:
         for i, ev in enumerate(evidence):
             if ev.entity_type == "STANDARD" and ev.standard_title:
                 claim_text = f"The standard is {ev.standard_title}."
                 claims.append(Claim(
                      claim_id=f"c_{intent.name}_{i}",
                      claim_type="BIS_FACT",
                      text=claim_text,
                      subject_entity=f"STANDARD:{ev.standard_number}",
                      predicate="HAS_TITLE",
                      object_entity=ev.standard_title,
                      supporting_evidence_ids=[ev.source_record_id],
                      support_status=SupportStatus.UNSUPPORTED
                 ))
                 break
                 
    elif intent == QueryIntent.UNKNOWN:
         for i, ev in enumerate(evidence):
             if ev.entity_type == "UNKNOWN" and "UNKNOWN" in ev.source_record_id:
                 claim_text = f"Record {ev.source_record_id} is marked as UNKNOWN and is unusable for factual identification."
                 claims.append(Claim(
                     claim_id=f"c_{intent.name}_{i}",
                     claim_type="META",
                     text=claim_text,
                     subject_entity=ev.source_record_id,
                     predicate="IS_UNKNOWN",
                     object_entity="TRUE",
                     supporting_evidence_ids=[ev.source_record_id],
                     support_status=SupportStatus.UNSUPPORTED
                 ))
                 break
                 
    else:
        # Generic handler
        for i, ev in enumerate(evidence):
            if ev.text and not ev.document_title:
                 # It's a procedure or generic text
                 claim_text = ev.text[:200] + "..." if len(ev.text) > 200 else ev.text
                 claims.append(Claim(
                      claim_id=f"c_{intent.name}_{i}",
                      claim_type="BIS_FACT",
                      text=claim_text,
                      subject_entity="QUERY",
                      predicate="GENERAL_INFORMATION",
                      object_entity="EVIDENCE_TEXT",
                      supporting_evidence_ids=[ev.source_record_id],
                      support_status=SupportStatus.UNSUPPORTED
                 ))
            break
            
    # VALIDATION GATE
    final_claims = []
    for c in claims:
        validated_claim = validate_claim(c, evidence, intent, requested_identifiers=requested_identifiers)
        if validated_claim.support_status == SupportStatus.SUPPORTED:
            final_claims.append(validated_claim)
            # Reconstruct text explicitly from supported claims to avoid source-title-as-fact
            if intent == QueryIntent.TESTING_FEE:
                 text_parts.append(f"- {validated_claim.text}")
            elif intent == QueryIntent.QCO_APPLICABILITY:
                 text_parts.append(f"- {validated_claim.text}")
            elif intent == QueryIntent.LABORATORY_LOOKUP:
                 text_parts.append(f"- {validated_claim.text}")
            elif intent == QueryIntent.HISTORICAL_VERSION:
                 text_parts.append(f"- {validated_claim.text}")
            elif intent == QueryIntent.STANDARD_LOOKUP:
                 text_parts.append(validated_claim.text)
            elif intent == QueryIntent.UNKNOWN:
                 text_parts.append(validated_claim.text)
            else:
                 text_parts.append(validated_claim.text)
        else:
            unsupported_claims.append(validated_claim)
            
    if not final_claims:
         text_parts = ["I could not verify this from the available BIS evidence."]
         
    return "\n\n".join(text_parts), final_claims, unsupported_claims


class GroundedRAGEngine:
    def __init__(self, retrieval_data, model):
        self.retrieval_data = retrieval_data
        self.model = model
        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)
            
    def answer(self, query):
        """Execute full Grounded RAG pipeline with Subquestions and Entity-Bound Grounding."""
        
        # 1. Decompose Query
        subquestions = decompose_query(query)
        
        # 2. Hybrid Retrieval (Shared for the query context)
        retrieval_result = hybrid_retrieve(self.retrieval_data, query, self.model)
        
        # 3. Evidence Selection (Shared pool, returns EvidenceObject list)
        evidence_pool = select_evidence(retrieval_result, self.retrieval_data, top_n=20)
        
        # Evaluate each subquestion independently
        for subq in subquestions:
            # Note: evaluate_sufficiency needs a raw evidence list for compatibility or we adapt it
            # We will convert EvidenceObjects back to raw dicts for evaluate_sufficiency for now
            # Actually, let's adapt evaluate_sufficiency to accept EvidenceObject
            
            # Since evaluate_sufficiency was written for dicts, we temporarily mock dicts
            raw_pool = []
            for ev in evidence_pool:
                raw_pool.append({
                    "entity_type": ev.entity_type,
                    "title": ev.source_title or ev.document_title,
                    "text": ev.text,
                    "supersession": "Explicit" if ev.standard_revision else "UNKNOWN",
                    "lims_details": {
                         "test_parameter": ev.test_parameter,
                         "amount_inr": ev.fee_amount
                    }
                })
                
            status, gaps = evaluate_sufficiency(subq.query, subq.intent, retrieval_result["identifiers"], raw_pool)
            subq.evidence_status = status
            subq.gaps = gaps
            
            # Confidence Calculation
            subq.confidence = calculate_confidence(raw_pool, status, gaps, self.config)
            
            # Citations
            citations = build_citations(evidence_pool)
            
            # Generate Text and Claims (Validation Gate happens inside here)
            req_idents = retrieval_result.get("identifiers", {}).get("is_numbers", [])
            answer_text, claims, unsupported_claims = generate_claims_and_text(subq, evidence_pool, status, citations, gaps, requested_identifiers=req_idents)
            
            # If all factual claims are unsupported, demote status to INSUFFICIENT
            if not any(c.claim_type == "BIS_FACT" for c in claims) and status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.PARTIAL):
                 subq.evidence_status = EvidenceStatus.INSUFFICIENT
                 subq.gaps.append({"gap_type": "UNSUPPORTED_CLAIMS", "message": "Factual claims could not be verified by exact identifier/relationship matching."})
                 subq.confidence = {"label": "NONE", "score": 0.0, "reasons": ["Claims failed validation gate"], "calibration_status": "BASELINE_UNCALIBRATED"}
                 subq.answer_text = "I could not verify this from the available BIS evidence."
            else:
                 subq.claims = claims
                 subq.answer_text = answer_text
                 
            subq.unsupported_claims = unsupported_claims
            
        # Build answer trace
        
        # Construct final composed answer text
        final_answer_parts = []
        if len(subquestions) > 1:
            for subq in subquestions:
                final_answer_parts.append(f"### {subq.intent.name.replace('_', ' ').title()}\n{subq.answer_text}")
        elif len(subquestions) == 1:
            final_answer_parts.append(subquestions[0].answer_text)
            
        all_claims = []
        all_unsupported = []
        for subq in subquestions:
            for c in subq.claims:
                cdict = c.__dict__.copy()
                cdict["support_status"] = c.support_status.value
                all_claims.append(cdict)
            for c in subq.unsupported_claims:
                cdict = c.__dict__.copy()
                cdict["support_status"] = c.support_status.value
                all_unsupported.append(cdict)
            
        # Determine global status with strict aggregation logic
        statuses = [sq.evidence_status for sq in subquestions]
        
        if all(s == EvidenceStatus.SUFFICIENT for s in statuses):
             global_status = "SUFFICIENT"
        elif all(s == EvidenceStatus.NO_EVIDENCE for s in statuses):
             global_status = "NO_EVIDENCE"
        elif all(s in (EvidenceStatus.INSUFFICIENT, EvidenceStatus.NO_EVIDENCE) for s in statuses):
             global_status = "INSUFFICIENT"
        else:
             global_status = "PARTIAL"
             
        trace = {
            "subquestions": []
        }
        
        # GLOBAL AGGREGATION GATE
        overall_status = EvidenceStatus.SUFFICIENT
        for sq in subquestions:
            if sq.evidence_status == EvidenceStatus.INSUFFICIENT:
                overall_status = EvidenceStatus.INSUFFICIENT
                break
            elif sq.evidence_status == EvidenceStatus.PARTIAL:
                overall_status = EvidenceStatus.PARTIAL
                
        # If demoted to INSUFFICIENT globally due to the gate, enforce it
        for sq in subquestions:
            sq.evidence_status = overall_status
            
            trace["subquestions"].append({
                "intent": sq.intent.name,
                "evidence_status": sq.evidence_status.value,
                "confidence": sq.confidence,
                "answer_text": sq.answer_text,
                "gaps": sq.gaps
            })
            
        trace.update({
            "query": query,
            "retrieval_count": retrieval_result["union_candidates"],
            "selected_evidence_count": len(evidence_pool),
            "evidence_status": global_status,
            "answer": "\n\n".join(final_answer_parts),
            "claims": all_claims,
            "unsupported_claims": all_unsupported,
            "evidence": [ev.__dict__ for ev in evidence_pool],
            "citations": [], # Mapped directly on claims now
            "generation_mode": "GROUNDED" if global_status in ("SUFFICIENT", "PARTIAL") else "FALLBACK"
        })
        
        return trace
