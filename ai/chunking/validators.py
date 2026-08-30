"""
Chunking Validators Module for Phase 2E.
Audits chunk artifacts to ensure schema compliance, provenance completeness,
and safety constraints (e.g. under_consideration guard).
"""

import logging
from typing import Any, Dict, List
from ai.chunking.schema import ChunkType, KnowledgeChunk, NormativeForce

logger = logging.getLogger(__name__)


class ChunkValidator:
    """Audits generated knowledge chunks for correctness and integrity."""

    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        errors: List[str] = []
        doc_id = chunks[0].get("document_id", "UNKNOWN") if chunks else "UNKNOWN"

        if not chunks:
            return {"document_id": doc_id, "is_valid": False, "errors": ["No chunks provided"]}

        type_counts: Dict[str, int] = {}

        for idx, c_dict in enumerate(chunks):
            # 1. Pydantic validation
            try:
                chunk = KnowledgeChunk.model_validate(c_dict)
            except Exception as e:
                errors.append(f"Chunk {idx} failed schema validation: {e}")
                continue

            ch_type = chunk.chunk_type.value
            type_counts[ch_type] = type_counts.get(ch_type, 0) + 1

            # 2. Provenance Check
            if not chunk.provenance.pages or not chunk.page_refs:
                errors.append(f"Chunk {chunk.chunk_id} has missing page references.")

            # 3. Under Consideration Safety Guard
            if chunk.normative_context.normative_force == NormativeForce.UNDER_CONSIDERATION:
                if any(r.get("status") == "mandatory" for r in chunk.requirements):
                    errors.append(f"Safety violation: Under consideration chunk {chunk.chunk_id} has mandatory requirements.")

            # 4. Table Chunk Validation
            if chunk.chunk_type == ChunkType.TABLE:
                if not chunk.rows:
                    errors.append(f"Table chunk {chunk.chunk_id} has no structured rows.")
                if not chunk.table_number:
                    errors.append(f"Table chunk {chunk.chunk_id} missing table_number.")

            # 5. Definition Chunk Validation
            if chunk.chunk_type == ChunkType.DEFINITION:
                if not chunk.term or not chunk.definition:
                    errors.append(f"Definition chunk {chunk.chunk_id} missing term or definition body.")

        return {
            "document_id": doc_id,
            "is_valid": len(errors) == 0,
            "total_chunks": len(chunks),
            "type_counts": type_counts,
            "errors": errors,
        }


def validate_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience helper function to validate chunk list."""
    validator = ChunkValidator()
    return validator.validate_chunks(chunks)
