"""
Processing Subpackage for BIS AI Assistant.
Handles Phase 2D semantic normalization, knowledge entity extraction,
machine-readable requirements, graph relationships, table normalization,
structured cross-reference resolution, dual value normalization, and definitions.
"""

from ai.processing.clause_classifier import ClauseClassifier, classify_clauses
from ai.processing.cross_reference_resolver import CrossReferenceResolver, resolve_cross_references
from ai.processing.definition_extractor import DefinitionExtractor, extract_definitions
from ai.processing.entity_extractor import EntityExtractor
from ai.processing.normalizer import DocumentNormalizer, normalize_all_documents, normalize_document
from ai.processing.relationship_extractor import RelationshipExtractor
from ai.processing.requirement_extractor import RequirementExtractor
from ai.processing.table_normalizer import TableNormalizer
from ai.processing.value_normalizer import ValueNormalizer, normalize_value

__all__ = [
    "ClauseClassifier",
    "classify_clauses",
    "CrossReferenceResolver",
    "resolve_cross_references",
    "DefinitionExtractor",
    "extract_definitions",
    "EntityExtractor",
    "RequirementExtractor",
    "RelationshipExtractor",
    "TableNormalizer",
    "ValueNormalizer",
    "normalize_value",
    "DocumentNormalizer",
    "normalize_document",
    "normalize_all_documents",
]
