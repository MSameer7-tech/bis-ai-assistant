"""
Multi-Factor Benchmark Evaluator with Failure Severity Classification (Phase 4F).
"""
import re
import math
from typing import Dict, Any, Optional
from ai.benchmark.models import BenchmarkCase, CaseEvaluationResult, FailureSeverity
from ai.rag.models import RAGAnswer


class BenchmarkEvaluator:
    """Evaluates RAG pipeline answers against corpus-grounded benchmark expectations."""

    @classmethod
    def evaluate_case(
        cls,
        case: BenchmarkCase,
        answer: RAGAnswer,
        elapsed_ms: float
    ) -> CaseEvaluationResult:
        """Evaluates actual RAGAnswer against expected BenchmarkCase contract."""
        checks: Dict[str, bool] = {}
        passed = True
        severity: Optional[FailureSeverity] = None
        error_msgs = []

        # Determine actual status (VERIFIED vs ABSTAINED vs CLARIFICATION_REQUIRED)
        is_refusal = (
            answer.refusal_reason is not None
            or answer.abstention_type is not None
            or (answer.guardrail_result and answer.guardrail_result.refusal_required)
            or (answer.production_payload and answer.production_payload.get("status") in ("refusal", "ABSTAINED", "abstained", "guardrail_blocked"))
        )
        actual_status = "ABSTAINED" if is_refusal else "VERIFIED"

        answer_text = answer.answer if hasattr(answer, "answer") else str(answer)
        actual_citations = [c.standard_number for c in answer.citations]
        actual_top_std = answer.citations[0].standard_number if answer.citations else ""
        actual_top_clean = re.sub(r"\s*:\s*\d{4}", "", actual_top_std).strip()
        actual_top_clause = answer.citations[0].clause if answer.citations else ""

        # 1. Check Forbidden Standards (Zero Tolerance)
        forbidden_violation = False
        if case.forbidden_standards:
            for forb in case.forbidden_standards:
                forb_clean = re.sub(r"\s*:\s*\d{4}", "", forb).strip()
                if any(forb_clean.lower() in c.lower() for c in actual_citations) or forb_clean.lower() in answer_text.lower():
                    forbidden_violation = True
                    error_msgs.append(f"Forbidden standard '{forb}' was cited or mentioned")
                    passed = False
                    severity = FailureSeverity.CRITICAL

        checks["forbidden_standards_clean"] = not forbidden_violation

        # 2. Check Status
        status_match = (actual_status == case.expected_status)
        checks["status"] = status_match

        if not status_match:
            passed = False
            error_msgs.append(f"Status mismatch: expected {case.expected_status}, got {actual_status}")

            if case.expected_status == "ABSTAINED" and actual_status == "VERIFIED":
                # False retrieval on unsupported or cross-domain query is CRITICAL
                severity = FailureSeverity.CRITICAL
            elif case.expected_status == "VERIFIED" and actual_status == "ABSTAINED":
                severity = FailureSeverity.HIGH

        # 3. If Expected ABSTAINED, verify clean abstention
        if case.expected_status == "ABSTAINED":
            if status_match and not forbidden_violation:
                passed = True
                severity = None
            return CaseEvaluationResult(
                test_id=case.id,
                category=case.category,
                query=case.query,
                query_type=case.query_type,
                passed=passed,
                failure_severity=severity,
                expected={"status": case.expected_status, "reason": case.abstention_reason},
                actual={"status": actual_status, "answer": answer_text[:120]},
                checks=checks,
                elapsed_ms=elapsed_ms,
                error_message="; ".join(error_msgs) if error_msgs else None
            )

        # 4. Check Standard Identification
        if case.expected_standard:
            exp_clean = re.sub(r"\s*:\s*\d{4}", "", case.expected_standard).strip().lower()
            std_in_top1 = (exp_clean in actual_top_clean.lower()) if actual_top_clean else False
            std_in_any = any(exp_clean in c.lower() for c in actual_citations)

            checks["standard_top1"] = std_in_top1
            checks["standard_retrieved"] = std_in_any

            if not std_in_top1:
                passed = False
                if std_in_any:
                    error_msgs.append(f"Standard '{case.expected_standard}' retrieved in candidates but not Top-1")
                    if severity != FailureSeverity.CRITICAL:
                        severity = FailureSeverity.MEDIUM
                else:
                    error_msgs.append(f"Standard '{case.expected_standard}' not found in citations")
                    if severity != FailureSeverity.CRITICAL:
                        severity = FailureSeverity.CRITICAL if case.query_type == "STANDARD_LOOKUP" else FailureSeverity.HIGH

        # 5. Check Clause Identification
        if case.expected_clause:
            clause_match = (case.expected_clause in actual_top_clause or case.expected_clause in answer_text)
            checks["clause"] = clause_match
            if not clause_match:
                passed = False
                error_msgs.append(f"Clause mismatch: expected {case.expected_clause}, got {actual_top_clause}")
                if severity not in (FailureSeverity.CRITICAL, FailureSeverity.HIGH):
                    severity = FailureSeverity.HIGH

        # 6. Check Numerical Value Grounding
        if case.expected_value is not None:
            num_match = False
            numbers_in_text = re.findall(r"\b\d+(?:\.\d+)?\b", answer_text)
            for n_str in numbers_in_text:
                try:
                    val = float(n_str)
                    if math.isclose(val, case.expected_value, rel_tol=0.01) or abs(val - case.expected_value) < 1e-4:
                        num_match = True
                        break
                except ValueError:
                    pass

            checks["numerical_value"] = num_match
            if not num_match:
                passed = False
                error_msgs.append(f"Numerical value {case.expected_value} {case.expected_unit or ''} missing from answer text")
                severity = FailureSeverity.CRITICAL

        # 7. Check Normative Force Preservation
        if case.expected_normative_force:
            norm_match = (
                case.expected_normative_force.upper() in answer_text.upper()
                or any(k in answer_text.upper() for k in ["INFORMATIVE", "MANDATORY", "PROHIBITED", "PROVISIONAL", "UNDER_CONSIDERATION"])
            )
            checks["normative_force"] = norm_match
            if not norm_match:
                passed = False
                error_msgs.append(f"Normative force {case.expected_normative_force} not preserved in answer")
                if severity not in (FailureSeverity.CRITICAL, FailureSeverity.HIGH):
                    severity = FailureSeverity.HIGH

        return CaseEvaluationResult(
            test_id=case.id,
            category=case.category,
            query=case.query,
            query_type=case.query_type,
            passed=passed,
            failure_severity=severity if not passed else None,
            expected={
                "status": case.expected_status,
                "standard": case.expected_standard,
                "clause": case.expected_clause,
                "value": case.expected_value
            },
            actual={
                "status": actual_status,
                "standard": actual_top_std,
                "clause": actual_top_clause,
                "answer": answer_text[:120]
            },
            checks=checks,
            elapsed_ms=elapsed_ms,
            error_message="; ".join(error_msgs) if error_msgs else None
        )
