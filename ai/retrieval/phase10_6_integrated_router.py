import json
import os
from typing import List, Dict, Any

class EvidenceClaimBinding:
    def __init__(self, claim_id: str, claim_type: str, text: str, evidence_role: str, evidence_ids: List[str], provenance: Dict[str, Any]):
        self.claim_id = claim_id
        self.claim_type = claim_type
        self.text = text
        self.evidence_role = evidence_role
        self.evidence_ids = evidence_ids
        self.provenance = provenance
        self.verification_status = "PENDING"

class IntegratedRetrievalRouter:
    def __init__(self, policy_path: str = "data/integration/phase10_6/routing_policy.json"):
        with open(policy_path, "r") as f:
            self.policy = json.load(f)

    def determine_allowed_roles(self, intents: List[str]) -> set:
        allowed = set()
        for intent in intents:
            if intent in self.policy:
                allowed.update(self.policy[intent]["allowed"])
        return allowed

    def determine_prohibited_roles(self, intents: List[str]) -> set:
        prohibited = set()
        for intent in intents:
            if intent in self.policy:
                prohibited.update(self.policy[intent]["prohibited"])
        return prohibited

    def route_evidence(self, query_intents: List[str], retrieved_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        allowed = self.determine_allowed_roles(query_intents)
        prohibited = self.determine_prohibited_roles(query_intents)
        
        filtered_evidence = []
        rejected_evidence = []
        
        for ev in retrieved_evidence:
            role = ev.get("evidence_role")
            
            if role in prohibited:
                rejected_evidence.append({"evidence": ev, "reason": "PROHIBITED_ROLE"})
                continue
                
            if role not in allowed:
                rejected_evidence.append({"evidence": ev, "reason": "ROLE_NOT_ALLOWED_FOR_INTENT"})
                continue
                
            if ev.get("lifecycle_status") in ["WITHDRAWN", "SUPERSEDED"] and not self._is_historical_intent(query_intents):
                rejected_evidence.append({"evidence": ev, "reason": "LIFECYCLE_EXPIRED"})
                continue
                
            if ev.get("identity_status") in ["IDENTITY_UNRESOLVED", "IDENTITY_REVIEW_REQUIRED"]:
                rejected_evidence.append({"evidence": ev, "reason": "IDENTITY_UNRESOLVED"})
                continue
                
            if ev.get("relationship_status") == "INFERRED":
                rejected_evidence.append({"evidence": ev, "reason": "INFERRED_RELATIONSHIP"})
                continue
                
            filtered_evidence.append(ev)
            
        sufficiency = self._evaluate_sufficiency(query_intents, filtered_evidence)
            
        return {
            "query_intents": query_intents,
            "allowed_roles": list(allowed),
            "prohibited_roles": list(prohibited),
            "filtered_evidence": filtered_evidence,
            "rejected_evidence": rejected_evidence,
            "sufficiency_status": sufficiency
        }

    def _is_historical_intent(self, intents: List[str]) -> bool:
        return "HISTORICAL" in intents

    def _evaluate_sufficiency(self, intents: List[str], evidence: List[Dict[str, Any]]) -> str:
        roles_present = set([e.get("evidence_role") for e in evidence])
        
        for intent in intents:
            if intent in self.policy:
                reqs = self.policy[intent]["minimum_requirements"]
                for req in reqs:
                    if req not in roles_present:
                        if roles_present:
                            return "PARTIAL_EVIDENCE"
                        else:
                            return "INSUFFICIENT_EVIDENCE"
                            
        if not roles_present:
            return "INSUFFICIENT_EVIDENCE"
            
        return "SUFFICIENT_EVIDENCE"

    def group_for_llm_context(self, evidence: List[Dict[str, Any]]) -> str:
        groups = {}
        for ev in evidence:
            role = ev.get("evidence_role", "UNKNOWN")
            if role not in groups:
                groups[role] = []
            groups[role].append(ev)
            
        context_parts = []
        for role, items in sorted(groups.items()):
            context_parts.append(f"[{role}]")
            for idx, item in enumerate(items):
                text = item.get("text_chunk") or item.get("text") or str(item.get("payload", ""))
                context_parts.append(f"Evidence {idx+1}: {text}")
            context_parts.append("")
            
        return "\n".join(context_parts)
