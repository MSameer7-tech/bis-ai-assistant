"""
Answer Schema Validator (Phase 7B).
Validates ProductionAnswerPayload before presentation to API client or UI.
"""
import logging
from typing import Tuple, List
from ai.rag.schema import ProductionAnswerPayload

logger = logging.getLogger(__name__)


class AnswerValidator:
    """
    Validates that a generated ProductionAnswerPayload complies with zero-hallucination mandates.
    """

    @staticmethod
    def validate_payload(payload: ProductionAnswerPayload) -> Tuple[bool, List[str]]:
        """
        Runs comprehensive validation checks on the payload.

        Returns:
            (is_valid: bool, errors: List[str])
        """
        errors = []

        # 1. Non-refusal answers MUST have answer text
        if payload.status == "verified":
            if not payload.answer.text.strip():
                errors.append("Verified payload cannot have empty answer text.")

            # 2. Non-refusal answers MUST have at least one citation
            if len(payload.citations) == 0:
                errors.append("Verified payload must contain at least one citation.")

            # 3. Numerical checks MUST all pass
            for nv in payload.numerical_verifications:
                if not nv.passed:
                    errors.append(
                        f"Numerical check failed for {nv.parameter}: "
                        f"claimed {nv.claim_value} {nv.claim_unit} != source {nv.source_value} {nv.source_unit}"
                    )

        # 4. Refusals must have a refusal reason
        if payload.status in ("refusal", "guardrail_blocked") and not payload.refusal_reason:
            errors.append("Refusal/blocked payload must include an explicit refusal_reason.")

        is_valid = len(errors) == 0
        return is_valid, errors
