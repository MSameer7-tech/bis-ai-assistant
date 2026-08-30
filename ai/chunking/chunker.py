"""
Structure-Aware Semantic Chunker for BIS Documents.
Preserves clause hierarchy lineage, normative modal expressions (shall, shall not, under consideration),
and atomic requirement-condition-test method boundaries.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.chunking.schema import (
    ChunkClause,
    ChunkProvenance,
    ChunkType,
    KnowledgeChunk,
    NormativeContext,
    NormativeForce,
    make_chunk_id,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"

MODAL_PATTERNS = [
    (r"\bshall\s+not\b", "shall not"),
    (r"\bshall\b", "shall"),
    (r"\bmust\s+not\b", "must not"),
    (r"\bmust\b", "must"),
    (r"\bshould\b", "should"),
    (r"\bmay\b", "may"),
    (r"\bunder\s+consideration\b", "under consideration"),
    (r"\bcompliance\s+is\s+checked\b", "compliance is checked by"),
    (r"\bnote\b", "note"),
]


def extract_normative_context(text: str, reqs: List[Dict[str, Any]]) -> NormativeContext:
    """Extracts modal auxiliary keywords, normative force, and verbatim statements."""
    text_lower = text.lower()
    modals = []
    for pat, label in MODAL_PATTERNS:
        if re.search(pat, text_lower):
            modals.append(label)

    # Determine Normative Force accurately
    if any(r.get("status") == "mandatory" for r in reqs):
        force = NormativeForce.MANDATORY
    elif reqs and all(r.get("status") == "under_consideration" for r in reqs):
        force = NormativeForce.UNDER_CONSIDERATION
    elif "shall not" in modals or "must not" in modals:
        force = NormativeForce.PROHIBITION
    elif "shall" in modals or "must" in modals:
        force = NormativeForce.MANDATORY
    elif "under consideration" in text_lower and not any(r.get("status") == "mandatory" for r in reqs):
        force = NormativeForce.UNDER_CONSIDERATION
    elif "should" in modals:
        force = NormativeForce.RECOMMENDATION
    else:
        force = NormativeForce.INFORMATIVE

    verbatim = []
    for line in text.splitlines():
        l_str = line.strip()
        if any(m in l_str.lower() for m in ("shall", "must", "not less than", "shall not exceed", "under consideration")):
            if len(l_str) > 10:
                verbatim.append(l_str)

    # Detect compliance verification method
    comp_method = None
    if "compliance is checked" in text_lower or "test" in text_lower:
        for line in text.splitlines():
            if "compliance is checked" in line.lower() or "is checked by" in line.lower():
                comp_method = line.strip()
                break

    return NormativeContext(
        normative_force=force,
        modal_keywords=modals,
        verbatim_normative_statements=verbatim,
        compliance_verification_method=comp_method,
    )


class StructureAwareChunker:
    """Chunks normalized BIS documents into semantically coherent knowledge units."""

    def __init__(self):
        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    def chunk_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Loads frozen data/normalized/{document_id}.json and produces structured chunks.
        Saves output to data/chunks/{document_id}.chunks.json.
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

        refs_by_clause: Dict[str, List[Dict[str, Any]]] = {}
        for ref in norm_doc.get("cross_references", []):
            refs_by_clause.setdefault(str(ref.get("source_clause", "0")), []).append(ref)

        reqs_by_clause: Dict[str, List[Dict[str, Any]]] = {}
        for req in norm_doc.get("requirements", []):
            reqs_by_clause.setdefault(str(req.get("clause", "0")), []).append(req)

        # 1. Definition Chunks (Clause 3)
        for idx, def_item in enumerate(norm_doc.get("definitions", [])):
            c_num = def_item.get("source_clause", "3")
            pages = def_item.get("source_pages", [6])
            term = def_item.get("term", "")
            definition_text = def_item.get("definition", "")

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(document_id, f"DEF_{c_num}", idx + 1, prefix="DEF"),
                document_id=document_id,
                source_id=source_id,
                chunk_type=ChunkType.DEFINITION,
                clause=ChunkClause(
                    number=c_num,
                    title=f"Definition: {term}",
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
                text=f"Definition of {term} (Clause {c_num}, Page {pages}):\n{definition_text}",
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

        # 2. Table Chunks (e.g. Table 2, Table 3)
        for idx, tab in enumerate(norm_doc.get("tables", [])):
            t_num = str(tab.get("table_id", f"T{idx + 1}"))
            c_num = str(tab.get("clause", "0"))
            p_num = tab.get("source_page", 1)
            t_title = tab.get("title", f"Table {idx + 1}")

            table_text = f"{t_title} (Clause {c_num}, Page {p_num}):\n"
            if tab.get("raw_markdown"):
                table_text += tab["raw_markdown"]
            else:
                table_text += json.dumps(tab.get("rows", []), indent=2)

            has_under_cons = any(
                isinstance(r, dict) and r.get("status") == "under_consideration" for r in tab.get("rows", [])
            )
            t_force = NormativeForce.UNDER_CONSIDERATION if has_under_cons else NormativeForce.MANDATORY

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(document_id, f"TAB_{t_num}", idx + 1, prefix="TAB"),
                document_id=document_id,
                source_id=source_id,
                chunk_type=ChunkType.TABLE,
                clause=ChunkClause(
                    number=c_num or t_num,
                    title=t_title,
                    depth=2,
                    parent_clause=c_num.split(".")[0] if "." in c_num else None,
                    hierarchy_path=[c_num.split(".")[0], c_num] if "." in c_num else [t_num],
                    section_number=c_num.split(".")[0] if "." in c_num else None,
                    section_title=t_title,
                ),
                normative_context=NormativeContext(
                    normative_force=t_force,
                    modal_keywords=["table values", "torque", "bending moment"],
                    verbatim_normative_statements=[f"{t_title} requirements"],
                ),
                text=table_text,
                entities=[],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(c_num, []),
                table_data=tab,
                page_refs=[p_num],
                provenance=ChunkProvenance(
                    document_id=document_id,
                    source_id=source_id,
                    standard_number=std_num,
                    clause=c_num or t_num,
                    pages=[p_num],
                    section=t_title,
                    original_text_snippet=table_text[:200],
                ),
                metadata={"table_id": t_num, "total_rows": len(tab.get("rows", []))},
            )
            chunks.append(chunk)

        # 3. Clause & Requirement Chunks with Hierarchy & Normative Binding
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

                # If this is top-level clause e.g. "8", update section context
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

                # Build contextual text with clause hierarchy header
                hierarchy_str = " > ".join(current_chain)
                enriched_text = f"[{hierarchy_str}] Clause {c_num} - {c_title} (Page {c_pages}):\n{c_text.strip()}"

                # Append conditions and acceptance criteria directly into text to keep meaning atomic
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

        out_file = CHUNKS_DIR / f"{document_id}.chunks.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(serialized_chunks, f, indent=2, ensure_ascii=False)

        logger.info(
            "✅ Successfully created %d structure-aware knowledge chunks for %s -> %s",
            len(serialized_chunks),
            document_id,
            out_file.name,
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
