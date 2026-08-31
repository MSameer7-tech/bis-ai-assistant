"""
Structure-Aware Semantic Chunker Implementation for BIS Documents (Phase 2E & Phase 3).
Executes boundary rules, preserves hierarchical clause trees, isolates definitions and tables,
preserves normative modal keywords, assigns stable IDs, and computes content hashes.
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
    compute_chunk_content_hash,
    make_chunk_id,
)
from ai.chunking.table_chunker import TableChunker
from ai.chunking.validators import ChunkValidator

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"
CHUNKS_DIR = DATA_DIR / "chunks"


def map_cross_references(raw_refs: List[Dict[str, Any]]) -> List[ChunkCrossReference]:
    """Maps normalized cross reference dictionaries to Pydantic ChunkCrossReference objects."""
    res = []
    for r in raw_refs:
        std = r.get("target_standard") or r.get("standard") or r.get("target_standard_or_clause") or "UNKNOWN"
        ref_type = r.get("reference_type", "normative")
        rel = r.get("relationship")
        if not rel:
            if ref_type == "test_method":
                rel = "test_method_applies"
            elif ref_type == "requirement":
                rel = "requirements_apply"
            elif ref_type == "definition":
                rel = "definition_applies"
            else:
                rel = "references"

        res.append(
            ChunkCrossReference(
                standard=std,
                target_location=r.get("target_clause") or r.get("target_location"),
                relationship=rel,
                reference_type=ref_type,
                context_snippet=r.get("context_snippet"),
            )
        )
    return res


class StructureAwareChunker:
    """Creates discrete, self-contained knowledge chunks from Phase 2D normalized standards."""

    def __init__(self):
        self.table_chunker = TableChunker()
        self.validator = ChunkValidator()
        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    def chunk_document(
        self, document_id: str, version_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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
        # Lookup authentic publication date from registry or metadata
        registry_path = ROOT_DIR / "data" / "metadata" / "source_registry.json"
        reg_pub_date = None
        if registry_path.exists():
            try:
                with open(registry_path, "r", encoding="utf-8") as rf:
                    reg_data = json.load(rf)
                    for r in reg_data:
                        if r.get("document_id") == document_id or r.get("source_id") == source_id:
                            reg_pub_date = r.get("publication_date")
                            break
            except Exception:
                pass

        default_pub = "2026-08-01" if ("2026" in document_id or "2026" in std_num) else ("2017-01-01" if "2017" in std_num else "2012-08-01")
        pub_date = reg_pub_date or doc_meta.get("publication_date") or default_pub

        target_ver_id = version_id or norm_doc.get("version_id") or f"{document_id}-v001"

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

            c_hash = compute_chunk_content_hash(def_qa_text)

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(target_ver_id, c_num, idx + 1, prefix="DEF"),
                document_id=document_id,
                version_id=target_ver_id,
                source_id=source_id,
                standard_number=std_num,
                clause_number=c_num,
                parent_clause="3",
                section_number="3",
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
                normative_force="informative",
                text=def_qa_text,
                content_hash=c_hash,
                entities=[{
                    "entity_type": "definition",
                    "term": term,
                    "term_id": def_item.get("term_id"),
                }],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(c_num, []),
                pages=pages,
                page_refs=pages,
                temporal_status="current",
                valid_from=pub_date,
                valid_until=None,
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
            version_id=target_ver_id,
        )
        chunks.extend(table_chunks)

        seq_tracker: Dict[str, int] = {}

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

                # Determine Chunk Type and Prefix
                sem_type = c.get("semantic_type", "")
                if sem_type == "scope" or c_num == "1":
                    ch_type = ChunkType.SCOPE
                    pfx = "SCOPE"
                elif sem_type == "reference" or c_num == "2":
                    ch_type = ChunkType.REFERENCE
                    pfx = "REF"
                elif sem_type == "sampling_requirement" or "15" in c_num:
                    ch_type = ChunkType.SAMPLING
                    pfx = "SMPL"
                elif sem_type == "test_method" or "test" in c_title.lower():
                    ch_type = ChunkType.TEST_METHOD
                    pfx = "TEST"
                elif len(c_reqs) > 0 or sem_type == "requirement" or sem_type == "marking_requirement":
                    ch_type = ChunkType.REQUIREMENT
                    pfx = "REQ"
                else:
                    ch_type = ChunkType.GENERAL_PROVISION
                    pfx = "GEN"

                # Extract Normative Modals & Force
                norm_context = extract_normative_context(c_text, c_reqs)

                # Format self-contained chunk text with rich semantic context
                std_title = str(doc_meta.get("title", "")).strip()
                title_suffix = f" - {std_title}" if std_title else ""
                
                text_lines = [
                    f"Clause {c_num}: {c_title}",
                    f"Standard: {std_num}{title_suffix} (Section {curr_sec_num} {curr_sec_title}, Pages {c_pages})",
                ]
                if doc_meta.get("product_domain"):
                    text_lines.append(f"Domain: {doc_meta.get('product_domain')} | Category: {doc_meta.get('product_category')} | Product: {doc_meta.get('product_type')}")
                text_lines.extend([
                    f"Normative Force: {norm_context.normative_force.value.upper()}",
                    "",
                    c_text.strip() if c_text else f"{c_title} provision as specified in {std_num}.",
                ])

                # Append machine-readable requirements
                if c_reqs:
                    text_lines.append("\nStructured Requirements:")
                    for r in c_reqs:
                        param = r.get("parameter", "requirement")
                        op = r.get("operator", "")
                        val = r.get("value", "")
                        unit = r.get("unit", "")
                        st = r.get("status", "mandatory")
                        text_lines.append(f"  • {param}: {op} {val} {unit} [Status: {st}]".strip())

                # Append cross-references
                if c_refs:
                    text_lines.append("\nReferenced Standards:")
                    for ref in c_refs:
                        text_lines.append(f"  • {ref.standard} ({ref.relationship})")

                enriched_text = "\n".join(text_lines)
                c_hash = compute_chunk_content_hash(enriched_text)

                parent_clause_id = ".".join(c_num.split(".")[:-1]) if "." in c_num else None
                key = f"{c_num}_{pfx}"
                seq_tracker[key] = seq_tracker.get(key, 0) + 1
                seq = seq_tracker[key]

                chunk = KnowledgeChunk(
                    chunk_id=make_chunk_id(target_ver_id, c_num, seq, prefix=pfx),
                    document_id=document_id,
                    version_id=target_ver_id,
                    source_id=source_id,
                    standard_number=std_num,
                    clause_number=c_num,
                    parent_clause=parent_clause_id,
                    section_number=curr_sec_num,
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
                    normative_force=norm_context.normative_force.value,
                    text=enriched_text,
                    content_hash=c_hash,
                    entities=c_ents,
                    requirements=c_reqs,
                    conditions=[r.get("conditions") for r in c_reqs if r.get("conditions")],
                    references=c_refs,
                    pages=c_pages,
                    page_refs=c_pages,
                    temporal_status="current",
                    valid_from=pub_date,
                    valid_until=None,
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

            annex_text = f"{a_id} - {a_title} (Pages {a_pages}):\n{a_text.strip()}"
            c_hash = compute_chunk_content_hash(annex_text)

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(target_ver_id, a_id, idx + 1, prefix="ANNEX"),
                document_id=document_id,
                version_id=target_ver_id,
                source_id=source_id,
                standard_number=std_num,
                clause_number=a_id,
                parent_clause=None,
                section_number=a_id,
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
                normative_force="informative",
                text=annex_text,
                content_hash=c_hash,
                entities=[],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(a_id, []),
                pages=a_pages,
                page_refs=a_pages,
                temporal_status="current",
                valid_from=pub_date,
                valid_until=None,
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


def chunk_document(document_id: str, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convenience helper function to chunk a single normalized document."""
    chunker = StructureAwareChunker()
    return chunker.chunk_document(document_id, version_id=version_id)


def chunk_all_documents() -> Dict[str, List[Dict[str, Any]]]:
    """Batch chunks all normalized documents in data/normalized/."""
    chunker = StructureAwareChunker()
    results = {}
    for norm_file in sorted(NORMALIZED_DIR.glob("DOC-*.json")):
        if norm_file.name.endswith(".normalized.json"):
            continue
        doc_id = norm_file.stem
        try:
            chunks = chunker.chunk_document(doc_id)
            results[doc_id] = chunks
        except Exception as e:
            logger.error("Failed to chunk %s: %s", doc_id, e)
    return results
