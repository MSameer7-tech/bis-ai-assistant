"""
Processing Subpackage for BIS AI Assistant.
Handles Phase 2D semantic normalization, knowledge entity extraction,
machine-readable requirements, graph relationships, table normalization,
and structured cross-reference resolution.
"""

from ai.processing.clause_classifier import ClauseClassifier, classify_clauses
from ai.processing.cross_reference_resolver import CrossReferenceResolver, resolve_cross_references
from ai.processing.entity_extractor import EntityExtractor
from ai.processing.normalizer import DocumentNormalizer, normalize_all_documents, normalize_document
from ai.processing.relationship_extractor import RelationshipExtractor
from ai.processing.requirement_extractor import RequirementExtractor
from ai.processing.table_normalizer import TableNormalizer

__all__ = [
    "ClauseClassifier",
    "classify_clauses",
    "CrossReferenceResolver",
    "resolve_cross_references",
    "EntityExtractor",
    "RequirementExtractor",
    "RelationshipExtractor",
    "TableNormalizer",
    "DocumentNormalizer",
    "normalize_document",
    "normalize_all_documents",
]
