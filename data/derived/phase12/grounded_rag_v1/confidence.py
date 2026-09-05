from .schemas import ConfidenceLabel, EvidenceStatus
import json

def calculate_confidence(selected_evidence, status, gaps, config):
    """
    Calculate deterministic confidence score and label.
    """
    if status == EvidenceStatus.NO_EVIDENCE:
        return {"label": ConfidenceLabel.NONE.value, "score": 0.0, "reasons": ["No evidence retrieved"], "calibration_status": "BASELINE_UNCALIBRATED"}
        
    if gaps and any(g.get("gap_type") == "UNKNOWN_INTENT" for g in gaps):
        return {"label": ConfidenceLabel.NONE.value, "score": 0.0, "reasons": ["Unknown entity or intent"], "calibration_status": "BASELINE_UNCALIBRATED"}
        
    score = 0.0
    reasons = []
    
    # Base score from top retrieved item fusion score
    if selected_evidence:
        top_score = selected_evidence[0].get("retrieval_score", 0.0)
        score += min(top_score, 0.5) # Cap base contribution
        
    # Boost for exact match in any evidence
    if any("EXACT_IDENTIFIER_MATCH" in e.get("retrieval_reasons", []) for e in selected_evidence):
        score += 0.3
        reasons.append("Exact identifier match found")
        
    # Boost for authoritative source
    if any(e.get("authority") in ("BIS_PUBLISHED", "BIS") for e in selected_evidence):
        score += 0.2
        reasons.append("Supported by authoritative BIS source")
        
    # Penalty for gaps
    if status == EvidenceStatus.PARTIAL:
        score *= 0.7
        reasons.append("Evidence is only partial")
    elif status == EvidenceStatus.INSUFFICIENT:
        score *= 0.3
        reasons.append("Evidence is insufficient to answer the query")
        
    # Cap score
    score = min(max(score, 0.0), 1.0)
    
    # Determine label
    c_config = config.get("confidence", {})
    high_t = c_config.get("high_threshold", 0.8)
    med_t = c_config.get("medium_threshold", 0.5)
    
    if score >= high_t and status == EvidenceStatus.SUFFICIENT:
        label = ConfidenceLabel.HIGH
    elif score >= med_t and status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.PARTIAL):
        label = ConfidenceLabel.MEDIUM
    else:
        label = ConfidenceLabel.LOW
        
    return {
        "label": label.value,
        "score": round(score, 4),
        "reasons": reasons,
        "calibration_status": "BASELINE_UNCALIBRATED"
    }
