"""
Phase 2D Semantic Normalization Orchestrator.
Transforms verified Phase 2C structured JSON into rich semantic knowledge representations
in data/normalized/{document_id}.normalized.json with complete traceability.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.processing.entity_extractor import EntityExtractor
from ai.processing.relationship_extractor import RelationshipExtractor
from ai.processing.requirement_extractor import RequirementExtractor
from ai.processing.table_normalizer import TableNormalizer

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
METADATA_DIR = ROOT_DIR / "data" / "metadata"
DOCUMENTS_PATH = METADATA_DIR / "documents.json"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"


class DocumentNormalizer:
    """Orchestrates semantic normalization, entity extraction, and relationship mapping."""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.requirement_extractor = RequirementExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.table_normalizer = TableNormalizer()
        NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    def normalize_document(self, document_id: str) -> Dict[str, Any]:
        """
        Normalizes a processed document JSON artifact into its Phase 2D semantic representation.
        Outputs to data/normalized/{document_id}.normalized.json.
        """
        proc_file = PROCESSED_DIR / f"{document_id}.json"
        if not proc_file.exists():
            raise FileNotFoundError(f"Processed document not found: {proc_file}")

        with open(proc_file, "r", encoding="utf-8") as f:
            proc_doc = json.load(f)

        logger.info("Normalizing document %s", document_id)
        doc_meta = proc_doc.get("document_metadata", {})

        # 1. Document Identity Normalization
        normalized_identity = {
            "document_id": document_id,
            "source_id": proc_doc.get("source_id"),
            "standard_number": doc_meta.get("standard_number"),
            "title": doc_meta.get("title"),
            "version": doc_meta.get("version"),
            "issuing_authority": "Bureau of Indian Standards / Ministry of Electronics & IT",
            "source_file": doc_meta.get("source_file"),
            "sha256": doc_meta.get("sha256"),
        }

        # 2. Extract Entities
        entities = self.entity_extractor.extract_entities_from_document(proc_doc)

        # 3. Extract Machine-Readable Requirements
        requirements = self.requirement_extractor.extract_requirements(proc_doc)

        # 4. Extract Relationships (Triples)
        relationships = self.relationship_extractor.extract_relationships(proc_doc, entities)

        # 5. Normalize Tables
        normalized_tables = self.table_normalizer.normalize_tables(proc_doc)

        # 6. Normalize Explicit Standard References
        referenced_standards = [
            e["name"] for e in entities if e["entity_type"] == "referenced_standard"
        ]
        referenced_standards = sorted(list(set(referenced_standards)))

        # 7. Enrich Clauses with semantic components
        req_by_clause: Dict[str, List[Dict[str, Any]]] = {}
        for req in requirements:
            req_by_clause.setdefault(req["clause"], []).append(req)

        def enrich_clause_nodes(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            enriched = []
            for c in clauses:
                node = dict(c)
                c_num = c.get("clause_number", "")
                node["requirements"] = req_by_clause.get(c_num, [])
                if c.get("subclauses"):
                    node["subclauses"] = enrich_clause_nodes(c["subclauses"])
                enriched.append(node)
            return enriched

        enriched_clauses = enrich_clause_nodes(proc_doc.get("clauses", []))

        # 8. Assemble Canonical Normalized Document
        normalized_document = {
            "document_id": document_id,
            "source_id": proc_doc.get("source_id"),
            "document_metadata": normalized_identity,
            "semantic_sections": proc_doc.get("sections", []),
            "clauses": enriched_clauses,
            "entities": entities,
            "relationships": relationships,
            "requirements": requirements,
            "tables": normalized_tables,
            "references": referenced_standards,
            "annexes": proc_doc.get("annexes", []),
            "normalization_metadata": {
                "normalized_at": datetime.now(timezone.utc).isoformat(),
                "total_entities": len(entities),
                "total_requirements": len(requirements),
                "total_relationships": len(relationships),
                "total_tables": len(normalized_tables),
                "total_references": len(referenced_standards),
                "status": "normalized",
            },
            "provenance": {
                "source_id": proc_doc.get("source_id"),
                "document_id": document_id,
                "raw_file": doc_meta.get("source_file"),
                "sha256": doc_meta.get("sha256"),
            },
        }

        # 9. Write to data/normalized/{document_id}.normalized.json
        out_file = NORMALIZED_DIR / f"{document_id}.normalized.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(normalized_document, f, indent=2, ensure_ascii=False)

        # 10. Update documents.json & source_registry.json status to metadata_verified
        if DOCUMENTS_PATH.exists():
            with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
                documents = json.load(f)
            for d in documents:
                if d["document_id"] == document_id:
                    d["status"] = "metadata_verified"
                    break
            with open(DOCUMENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)

        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
            for item in registry:
                if item.get("document_id") == document_id:
                    item["status"] = "metadata_verified"
                    break
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)

        logger.info(
            "✅ Successfully normalized %s -> %s (%d entities, %d requirements, %d relationships)",
            document_id,
            out_file.name,
            len(entities),
            len(requirements),
            len(relationships),
        )

        return normalized_document

    def normalize_all_documents(self) -> Dict[str, Any]:
        """Normalizes all documents currently in data/metadata/documents.json."""
        if not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(f"Documents manifest missing: {DOCUMENTS_PATH}")

        with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
            documents = json.load(f)

        results = {}
        for doc in documents:
            doc_id = doc["document_id"]
            results[doc_id] = self.normalize_document(doc_id)

        return results


def normalize_document(document_id: str) -> Dict[str, Any]:
    """Convenience helper function to normalize a single document."""
    normalizer = DocumentNormalizer()
    return normalizer.normalize_document(document_id)


def normalize_all_documents() -> Dict[str, Any]:
    """Convenience helper function to normalize all documents."""
    normalizer = DocumentNormalizer()
    return normalizer.normalize_all_documents()
