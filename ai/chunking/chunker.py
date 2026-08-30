"""
Structure-Aware Semantic Chunker for BIS Documents.
Preserves clause hierarchy lineage, normative modal expressions (shall, shall not, under consideration),
atomic requirement-condition boundaries, discrete structured tables (Step 7),
standalone domain definitions (Step 8), and cross-standard references (Step 9).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.chunking.rules import extract_normative_context
from ai.chunking.schema import (
    ChunkClause,
    ChunkCrossReference,
    ChunkProvenance,
    ChunkType,
    KnowledgeChunk,
    NormativeContext,
    NormativeForce,
    make_chunk_id,
)
from ai.chunking.table_chunker import TableChunker
from ai.chunking.validators import ChunkValidator

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"


def map_cross_references(raw_refs: List[Dict[str, Any]]) -> List[ChunkCrossReference]:
    """Maps raw cross-reference objects into typed ChunkCrossReference instances (Step 9)."""
    mapped = []
    for r in raw_refs:
        std = r.get("target_standard", "")
        if not std:
            continue
        rel = "requirements_apply" if "shall" in r.get("context_snippet", "").lower() else "normative_reference"
        if r.get("reference_type") == "test_method":
            rel = "test_method_applies"
        elif r.get("reference_type") == "definition":
            rel = "definition_applies"

        mapped.append(ChunkCrossReference(
            standard=std,
            target_location=r.get("target_location"),
            relationship=rel,
            reference_type=r.get("reference_type", "normative"),
            context_snippet=r.get("context_snippet"),
        ))
    return mapped


class StructureAwareChunker:
    """Chunks normalized BIS documents into semantically coherent knowledge units."""

    def __init__(self):
        self.table_chunker = TableChunker()
        self.validator = ChunkValidator()
        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    def chunk_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Loads frozen data/normalized/{document_id}.json and produces structured chunks.
        Saves output to data/chunks/{document_id}.json and {document_id}.chunks.json.
        """
        norm_file = NORMALIZED_DIR / f"{document_id}.json"
        if not norm_file.exists():
            norm_file = NORMALIZED_DIR / f"{document_id}.normalized.json"
        if not norm_file.exists():
            raise FileNotFoundError(f"Normalized document missing: {norm_file}")

        with open(norm_file, "r", encoding="utf-8") as f:
            norm_doc = json.load(f)

        logger.info("Chunking normalized document %s", document_id)
        doc_meta = norm_doc.get("document_metadata", {})
        source_id = norm_doc.get("source_id", "SRC-UNKNOWN")
        std_num = str(doc_meta.get("standard_number") or doc_meta.get("title", document_id)).strip()

        chunks: List[KnowledgeChunk] = []

        # Lookup maps for quick entity, reference, and requirement binding
        entities_by_clause: Dict[str, List[Dict[str, Any]]] = {}
        for ent in norm_doc.get("entities", []):
            entities_by_clause.setdefault(str(ent.get("source_clause", "0")), []).append(ent)

        refs_by_clause: Dict[str, List[ChunkCrossReference]] = {}
        for ref in norm_doc.get("cross_references", []):
            mapped_ref = map_cross_references([ref])
            if mapped_ref:
                refs_by_clause.setdefault(str(ref.get("source_clause", "0")), []).extend(mapped_ref)

        reqs_by_clause: Dict[str, List[Dict[str, Any]]] = {}
        for req in norm_doc.get("requirements", []):
            reqs_by_clause.setdefault(str(req.get("clause", "0")), []).append(req)

        # 1. Definition Chunks (Clause 3 - Step 8)
        for idx, def_item in enumerate(norm_doc.get("definitions", [])):
            c_num = def_item.get("source_clause", "3")
            pages = def_item.get("source_pages", [6])
            term = def_item.get("term", "")
            definition_text = def_item.get("definition", "")

            def_title = f"Definition: {term}"
            def_qa_text = (
                f"Definition: {term}\n"
                f"Standard: {std_num} (Clause {c_num}, Page {pages[0] if pages else 1})\n\n"
                f"{term} is defined as: {definition_text}"
            )

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(document_id, f"DEF_{c_num}", idx + 1, prefix="DEF"),
                document_id=document_id,
                source_id=source_id,
                chunk_type=ChunkType.DEFINITION,
                title=def_title,
                term=term,
                definition=definition_text,
                clause=ChunkClause(
                    number=c_num,
                    title=def_title,
                    depth=2,
                    parent_clause="3",
                    hierarchy_path=["3", c_num],
                    section_number="3",
                    section_title="TERMINOLOGY",
                ),
                normative_context=NormativeContext(
                    normative_force=NormativeForce.INFORMATIVE,
                    modal_keywords=["definition"],
                    verbatim_normative_statements=[f"{term} — {definition_text}"],
                ),
                text=def_qa_text,
                entities=[{
                    "entity_type": "definition",
                    "term": term,
                    "term_id": def_item.get("term_id"),
                }],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(c_num, []),
                page_refs=pages,
                provenance=ChunkProvenance(
                    document_id=document_id,
                    source_id=source_id,
                    standard_number=std_num,
                    clause=c_num,
                    pages=pages,
                    section="3 TERMINOLOGY",
                    original_text_snippet=definition_text[:200],
                ),
                metadata={"term": term},
            )
            chunks.append(chunk)

        # 2. Table Chunks (Step 7 - Table 2, Table 3, etc.)
        table_chunks = self.table_chunker.create_table_chunks(
            doc_id=document_id,
            source_id=source_id,
            std_num=std_num,
            raw_tables=norm_doc.get("tables", []),
            refs_by_clause=refs_by_clause,
        )
        chunks.extend(table_chunks)

        # 3. Clause & Requirement Chunks with Hierarchy, Normative Context, and Cross-References (Step 9)
        def traverse_clauses(
            clause_list: List[Dict[str, Any]],
            parent_chain: List[str],
            sec_num: Optional[str] = None,
            sec_title: Optional[str] = None,
        ):
            for idx, c in enumerate(clause_list):
                c_num = str(c.get("clause_number", ""))
                c_title = c.get("title", f"Clause {c_num}")
                c_text = c.get("content", "")
                c_pages = c.get("page_refs", [c.get("page_start", 1)])
                c_reqs = c.get("requirements", reqs_by_clause.get(c_num, []))
                c_ents = entities_by_clause.get(c_num, [])
                c_refs = refs_by_clause.get(c_num, [])

                current_chain = parent_chain + [c_num]

                curr_sec_num = sec_num or (c_num if not parent_chain else parent_chain[0])
                curr_sec_title = sec_title or (c_title if not parent_chain else "")

                # Skip Clause 3 root if definitions already chunked individually
                if c_num == "3" and len(c.get("subclauses", [])) > 0:
                    if c.get("subclauses"):
                        traverse_clauses(c["subclauses"], current_chain, curr_sec_num, curr_sec_title)
                    continue

                # Determine Chunk Type
                sem_type = c.get("semantic_type", "")
                if sem_type == "scope" or c_num == "1":
                    ch_type = ChunkType.SCOPE
                elif sem_type == "reference" or c_num == "2":
                    ch_type = ChunkType.REFERENCE
                elif sem_type == "sampling_requirement" or "15" in c_num:
                    ch_type = ChunkType.SAMPLING
                elif sem_type == "test_method" or "test" in c_title.lower():
                    ch_type = ChunkType.TEST_METHOD
                elif len(c_reqs) > 0 or sem_type == "requirement" or sem_type == "marking_requirement":
                    ch_type = ChunkType.REQUIREMENT
                else:
                    ch_type = ChunkType.GENERAL_PROVISION

                hierarchy_str = " > ".join(current_chain)
                enriched_text = f"[{hierarchy_str}] Clause {c_num} - {c_title} (Page {c_pages}):\n{c_text.strip()}"

                if c_reqs:
                    for r in c_reqs:
                        if r.get("conditions"):
                            enriched_text += f"\n[Condition]: {json.dumps(r['conditions'])}"
                        if r.get("test"):
                            enriched_text += f"\n[Test Procedure]: {json.dumps(r['test'])}"
                        if r.get("acceptance_criterion"):
                            enriched_text += f"\n[Acceptance Criterion]: {json.dumps(r['acceptance_criterion'])}"

                norm_context = extract_normative_context(c_text, c_reqs)
                parent_clause_id = parent_chain[-1] if parent_chain else None

                chunk = KnowledgeChunk(
                    chunk_id=make_chunk_id(document_id, c_num, idx + 1),
                    document_id=document_id,
                    source_id=source_id,
                    chunk_type=ch_type,
                    title=c_title,
                    clause=ChunkClause(
                        number=c_num,
                        title=c_title,
                        depth=len(current_chain),
                        parent_clause=parent_clause_id,
                        hierarchy_path=current_chain,
                        section_number=curr_sec_num,
                        section_title=curr_sec_title,
                    ),
                    normative_context=norm_context,
                    text=enriched_text,
                    entities=c_ents,
                    requirements=c_reqs,
                    conditions=[r.get("conditions") for r in c_reqs if r.get("conditions")],
                    references=c_refs,
                    page_refs=c_pages,
                    provenance=ChunkProvenance(
                        document_id=document_id,
                        source_id=source_id,
                        standard_number=std_num,
                        clause=c_num,
                        pages=c_pages,
                        section=curr_sec_title or c_title,
                        original_text_snippet=c_text[:200],
                    ),
                    metadata={
                        "semantic_type": sem_type,
                        "hierarchy_path": current_chain,
                        "has_requirements": len(c_reqs) > 0,
                    },
                )
                chunks.append(chunk)

                if c.get("subclauses"):
                    traverse_clauses(c["subclauses"], current_chain, curr_sec_num, curr_sec_title)

        traverse_clauses(norm_doc.get("clauses", []), [])

        # 4. Annex Chunks
        for idx, annex in enumerate(norm_doc.get("annexes", [])):
            a_id = annex.get("annex_id", f"ANNEX {idx + 1}")
            a_title = annex.get("title", a_id)
            a_pages = annex.get("page_refs", [annex.get("page_start", 1)])
            a_text = annex.get("content", "")

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(document_id, f"ANNEX_{a_id.replace(' ', '_')}", idx + 1, prefix="ANNEX"),
                document_id=document_id,
                source_id=source_id,
                chunk_type=ChunkType.ANNEX,
                title=a_title,
                clause=ChunkClause(
                    number=a_id,
                    title=a_title,
                    depth=1,
                    parent_clause=None,
                    hierarchy_path=[a_id],
                    section_title=a_title,
                ),
                normative_context=extract_normative_context(a_text, []),
                text=f"{a_id} - {a_title} (Pages {a_pages}):\n{a_text.strip()}",
                entities=[],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(a_id, []),
                page_refs=a_pages,
                provenance=ChunkProvenance(
                    document_id=document_id,
                    source_id=source_id,
                    standard_number=std_num,
                    clause=a_id,
                    pages=a_pages,
                    section=a_title,
                    original_text_snippet=a_text[:200],
                ),
                metadata={"annex_id": a_id},
            )
            chunks.append(chunk)

        # Convert to serialized JSON dicts
        serialized_chunks = [c.model_dump() for c in chunks]

        # Audit & Validate chunks
        val_report = self.validator.validate_chunks(serialized_chunks)
        if not val_report["is_valid"]:
            logger.warning("Chunk validation warnings for %s: %s", document_id, val_report["errors"])

        # Write to both data/chunks/{document_id}.json and {document_id}.chunks.json
        out_file_main = CHUNKS_DIR / f"{document_id}.json"
        out_file_alias = CHUNKS_DIR / f"{document_id}.chunks.json"

        with open(out_file_main, "w", encoding="utf-8") as f:
            json.dump(serialized_chunks, f, indent=2, ensure_ascii=False)
        with open(out_file_alias, "w", encoding="utf-8") as f:
            json.dump(serialized_chunks, f, indent=2, ensure_ascii=False)

        logger.info(
            "✅ Successfully created %d structure-aware knowledge chunks for %s -> %s",
            len(serialized_chunks),
            document_id,
            out_file_main.name,
        )

        return serialized_chunks

    def chunk_all_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Chunks all normalized documents."""
        results = {}
        for p in sorted(NORMALIZED_DIR.glob("DOC-*.json")):
            if not p.name.endswith(".normalized.json"):
                doc_id = p.stem
                results[doc_id] = self.chunk_document(doc_id)
        return results


def chunk_document(document_id: str) -> List[Dict[str, Any]]:
    """Convenience helper function to chunk a single document."""
    chunker = StructureAwareChunker()
    return chunker.chunk_document(document_id)


def chunk_all_documents() -> Dict[str, List[Dict[str, Any]]]:
    """Convenience helper function to chunk all documents."""
    chunker = StructureAwareChunker()
    return chunker.chunk_all_documents()
