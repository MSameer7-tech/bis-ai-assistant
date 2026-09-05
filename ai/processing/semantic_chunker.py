"""
Phase 6: Deterministic Semantic Chunker.
Converts EvidenceUnits into derived SemanticChunks for retrieval,
preserving authoritative provenance and table structures.
"""
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SemanticChunk(BaseModel):
    """Derived chunk from an EvidenceUnit for RAG retrieval."""
    chunk_id: str = Field(..., description="Deterministic ID, e.g. CHUNK-<EU_ID>-001")
    evidence_unit_id: str
    document_id: str
    source_family_id: str
    document_type: str
    standard_number: Optional[str] = None
    standard_part: Optional[str] = None
    edition_year: Optional[str] = None
    document_kind: Optional[str] = None
    lifecycle: Optional[str] = None
    page: Optional[int] = None
    clause: Optional[str] = None
    heading: Optional[str] = None
    section: Optional[str] = None
    source_url: str
    parent_raw_sha256: str
    chunk_text: str
    chunk_sequence: int
    parent_document_sequence: int = 0
    duplicate_group_id: Optional[str] = None
    duplicate_type: Optional[str] = None

def compute_chunk_id(document_id: str, evidence_unit_id: str, sequence: int, chunker_version: str = "1.0") -> str:
    concat_str = f"{document_id}_{evidence_unit_id}_{sequence}_{chunker_version}"
    h = hashlib.sha256(concat_str.encode('utf-8')).hexdigest()[:16]
    return f"CH-{h}"

class SemanticChunker:
    def __init__(self, max_chunk_chars: int = 1500, duplicate_audit_path: Optional[Path] = None):
        self.max_chunk_chars = max_chunk_chars
        self.duplicate_audit = {}
        if duplicate_audit_path and duplicate_audit_path.exists():
            with open(duplicate_audit_path, "r") as f:
                audit_data = json.load(f)
                self.duplicate_audit = audit_data.get("evidence_unit_map", {})

    def _split_technical_sentences(self, text: str) -> List[str]:
        """
        Splits by sentences while protecting BIS technical identifiers.
        E.g., avoids splitting on "IS 1234.5", "clause 7.2", "Rs.", "Fig."
        """
        # Replace protected dots temporarily
        protected = text
        protected = re.sub(r'(?<=\d)\.(?=\d)', '<DOT>', protected)
        protected = re.sub(r'\b(IS|Rs|Fig|No|clause|Cl)\.\s', r'\1<DOT> ', protected, flags=re.IGNORECASE)
        protected = re.sub(r'(?<=[A-Z])\.(?=[A-Z])', '<DOT>', protected) # e.g. U.S.A.
        
        # Split on sentence boundaries
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', protected)
        
        # Restore protected dots
        sentences = [s.replace('<DOT>', '.').strip() for s in raw_sentences if s.strip()]
        return sentences

    def chunk_evidence_unit(self, unit: Dict[str, Any]) -> List[SemanticChunk]:
        """Chunks a single EvidenceUnit dictionary."""
        eu_id = unit["evidence_unit_id"]
        doc_id = unit["document_id"]
        content_text = unit["content_text"]
        content_type = unit.get("content_type", "CLAUSE")
        
        # Look up duplicate metadata
        dup_info = self.duplicate_audit.get(eu_id, {})
        dup_group = dup_info.get("duplicate_group_id")
        dup_type = dup_info.get("duplicate_type")

        # Base chunk data inherited from EvidenceUnit
        base_kwargs = {
            "evidence_unit_id": eu_id,
            "document_id": doc_id,
            "source_family_id": unit.get("document_family_id", doc_id),
            "document_type": unit.get("document_type", "UNKNOWN"),
            "page": unit.get("page_number"),
            "clause": unit.get("section_or_clause"),
            "heading": unit.get("heading"),
            "source_url": unit["source_url"],
            "parent_raw_sha256": unit["parent_raw_sha256"],
            "duplicate_group_id": dup_group,
            "duplicate_type": dup_type,
            "parent_document_sequence": 0 # Populated at generation time
        }

        # Handle Tables specifically
        if content_type == "TABLE":
            return [SemanticChunk(
                chunk_id=compute_chunk_id(doc_id, eu_id, 1),
                chunk_text=content_text,  # Tables are kept intact to preserve relations
                chunk_sequence=1,
                **base_kwargs
            )]

        # Handle coherent clauses (if small enough, keep intact)
        if len(content_text) <= self.max_chunk_chars:
            return [SemanticChunk(
                chunk_id=compute_chunk_id(doc_id, eu_id, 1),
                chunk_text=content_text,
                chunk_sequence=1,
                **base_kwargs
            )]

        # Fallback to structural splitting: Paragraphs -> Technical Sentences
        chunks = []
        seq = 1
        
        paragraphs = [p.strip() for p in content_text.split("\n\n") if p.strip()]
        
        current_chunk_text = ""
        
        for para in paragraphs:
            if len(current_chunk_text) + len(para) + 2 <= self.max_chunk_chars:
                current_chunk_text += ("\n\n" + para) if current_chunk_text else para
            else:
                if len(para) > self.max_chunk_chars:
                    if current_chunk_text:
                        chunks.append(current_chunk_text)
                        current_chunk_text = ""
                        
                    sentences = self._split_technical_sentences(para)
                    for sent in sentences:
                        if len(current_chunk_text) + len(sent) + 1 <= self.max_chunk_chars:
                            current_chunk_text += (" " + sent) if current_chunk_text else sent
                        else:
                            if current_chunk_text:
                                chunks.append(current_chunk_text)
                            current_chunk_text = sent
                else:
                    if current_chunk_text:
                        chunks.append(current_chunk_text)
                    current_chunk_text = para

        if current_chunk_text:
            chunks.append(current_chunk_text)

        result = []
        for c_text in chunks:
            result.append(SemanticChunk(
                chunk_id=compute_chunk_id(doc_id, eu_id, seq),
                chunk_text=c_text.strip(),
                chunk_sequence=seq,
                **base_kwargs
            ))
            seq += 1

        return result
