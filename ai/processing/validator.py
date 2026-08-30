"""
Semantic Knowledge Validator for Phase 2D.
Verifies entities, machine-readable requirements, cross-references, provenance,
and safety/accuracy constraints across normalized knowledge documents.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SemanticValidator:
    """Audits and validates Phase 2D normalized JSON artifacts."""

    def validate_normalized_document(self, norm_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a 5-pillar validation audit on a normalized document artifact.
        Returns a validation report with pass/fail checks and error diagnostics.
        """
        doc_id = norm_doc.get("document_id", "UNKNOWN")
        checks: Dict[str, bool] = {}
        errors: List[str] = []

        # 1. Entity Checks
        entities = norm_doc.get("entities", [])
        definitions = norm_doc.get("definitions", [])
        requirements = norm_doc.get("requirements", [])
        tables = norm_doc.get("tables", [])

        checks["entities_extracted"] = len(entities) > 0
        checks["requirements_extracted"] = len(requirements) >= 0
        checks["definitions_extracted"] = len(definitions) >= 0

        # 2. Requirement Checks
        for req in requirements:
            req_id = req.get("requirement_id", "")
            if not req_id.startswith("REQ-"):
                errors.append(f"Invalid requirement_id format: {req_id}")
            if "operator" not in req or "parameter" not in req:
                errors.append(f"Missing operator/parameter in {req_id}")
            if "provenance" not in req:
                errors.append(f"Missing provenance block in requirement {req_id}")

        checks["requirements_structure_valid"] = len(errors) == 0

        # 3. Cross-Reference Checks
        cross_refs = norm_doc.get("cross_references", [])
        for ref in cross_refs:
            if not ref.get("target_standard"):
                errors.append(f"Missing target_standard in reference {ref.get('reference_id')}")
            if ref.get("reference_type") not in ("normative", "informative", "test_method", "definition", "related_standard"):
                errors.append(f"Invalid reference_type in {ref.get('reference_id')}: {ref.get('reference_type')}")

        checks["cross_references_valid"] = len(errors) == 0

        # 4. Provenance Checks
        for ent in entities:
            prov = ent.get("provenance", {})
            if not prov.get("document_id") or not prov.get("clause") or not prov.get("page"):
                errors.append(f"Incomplete provenance in entity {ent.get('entity_id')}")

        checks["provenance_binding_valid"] = len(errors) == 0

        # 5. Safety & Accuracy Checks ("under consideration" must not be mandatory)
        for req in requirements:
            if "under consideration" in str(req.get("original_value", "")).lower():
                if req.get("status") == "mandatory":
                    errors.append(f"Safety violation: 'under consideration' requirement {req.get('requirement_id')} marked as mandatory!")

        for tab in tables:
            t_title = str(tab.get("title", "")).lower()
            if "torque" in t_title or "torsion" in t_title:
                for r in tab.get("rows", []):
                    if isinstance(r, dict) and "GX53" in str(r.get("cap", "")):
                        if r.get("status") == "mandatory":
                            errors.append("Safety violation: GX53 torque table entry marked as mandatory instead of under_consideration!")

        checks["safety_under_consideration_guarded"] = len(errors) == 0
        checks["overall_semantic_valid"] = len(errors) == 0

        return {
            "document_id": doc_id,
            "is_valid": len(errors) == 0,
            "checks": checks,
            "errors": errors,
            "stats": {
                "total_entities": len(entities),
                "total_definitions": len(definitions),
                "total_requirements": len(requirements),
                "total_cross_references": len(cross_refs),
                "total_tables": len(tables),
            },
        }


def validate_document(norm_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience helper to validate a normalized document."""
    validator = SemanticValidator()
    return validator.validate_normalized_document(norm_doc)
