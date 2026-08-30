"""
Table Chunker Module for Phase 2E.
Creates discrete, typed table chunks preserving structured row records and markdown representations.
"""

import json
import logging
import re
from typing import Any, Dict, List

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

logger = logging.getLogger(__name__)


class TableChunker:
    """Specialized chunker for standard specification tables."""

    def create_table_chunks(
        self,
        doc_id: str,
        source_id: str,
        std_num: str,
        raw_tables: List[Dict[str, Any]],
        refs_by_clause: Dict[str, List[ChunkCrossReference]],
    ) -> List[KnowledgeChunk]:
        table_chunks: List[KnowledgeChunk] = []

        for idx, tab in enumerate(raw_tables):
            t_num_raw = str(tab.get("table_id", f"T{idx + 1}"))
            t_digits = re.sub(r"[^0-9]", "", t_num_raw)
            t_num = str(int(t_digits)) if t_digits else str(idx + 1)
            c_num = str(tab.get("clause", "0"))
            p_num = tab.get("source_page", 1)
            t_title = tab.get("title", f"Table {t_num}")

            raw_rows = tab.get("rows", [])
            structured_rows = []
            for r in raw_rows:
                if isinstance(r, dict):
                    row_entry = dict(r)
                    if "torsion_moment" in r and isinstance(r["torsion_moment"], dict):
                        row_entry["torsion_moment"] = r["torsion_moment"].get("value")
                        row_entry["unit"] = r["torsion_moment"].get("unit", "Nm")
                    if "bending_moment" in r and isinstance(r["bending_moment"], dict):
                        row_entry["bending_moment"] = r["bending_moment"].get("value")
                        row_entry["unit"] = r["bending_moment"].get("unit", "Nm")
                    if "mass" in r and isinstance(r["mass"], dict):
                        row_entry["mass"] = r["mass"].get("value")
                        row_entry["mass_unit"] = r["mass"].get("unit", "kg")
                    structured_rows.append(row_entry)

            # Build readable Markdown table text
            table_md_lines = [
                f"{t_title} (Standard: {std_num}, Clause {c_num}, Page {p_num}):\n",
            ]
            if "torque" in t_title.lower() or "torsion" in t_title.lower() or t_num == "3":
                table_md_lines.append("| Cap Style | Torsion Moment (Torque) | Unit | Status |")
                table_md_lines.append("|---|---|---|---|")
                for r in structured_rows:
                    cap = r.get("cap", "-")
                    tm = r.get("torsion_moment", "-")
                    unit = r.get("unit", "Nm")
                    status = r.get("status", "mandatory")
                    table_md_lines.append(f"| {cap} | {tm} | {unit} | {status} |")
            elif "bending" in t_title.lower() or "mass" in t_title.lower() or t_num == "2":
                table_md_lines.append("| Cap Style | Bending Moment (Nm) | Mass (kg) | Status |")
                table_md_lines.append("|---|---|---|---|")
                for r in structured_rows:
                    cap = r.get("cap", "-")
                    bm = r.get("bending_moment", "-")
                    m = r.get("mass", "-")
                    status = r.get("status", "mandatory")
                    table_md_lines.append(f"| {cap} | {bm} | {m} | {status} |")
            else:
                table_md_lines.append(json.dumps(structured_rows, indent=2))

            table_text = "\n".join(table_md_lines)

            has_under_cons = any(
                isinstance(r, dict) and r.get("status") == "under_consideration" for r in structured_rows
            )
            t_force = NormativeForce.UNDER_CONSIDERATION if has_under_cons else NormativeForce.MANDATORY

            chunk = KnowledgeChunk(
                chunk_id=make_chunk_id(doc_id, f"TAB_{t_num}", idx + 1, prefix="TAB"),
                document_id=doc_id,
                source_id=source_id,
                chunk_type=ChunkType.TABLE,
                title=t_title,
                table_number=t_num,
                rows=structured_rows,
                table_data=tab,
                clause=ChunkClause(
                    number=c_num or t_num_raw,
                    title=t_title,
                    depth=2,
                    parent_clause=c_num.split(".")[0] if "." in c_num else None,
                    hierarchy_path=[c_num.split(".")[0], c_num] if "." in c_num else [t_num_raw],
                    section_number=c_num.split(".")[0] if "." in c_num else None,
                    section_title=t_title,
                ),
                normative_context=NormativeContext(
                    normative_force=t_force,
                    modal_keywords=["table values", "torque", "bending moment"],
                    verbatim_normative_statements=[f"{t_title} values in Clause {c_num}"],
                ),
                text=table_text,
                entities=[],
                requirements=[],
                conditions=[],
                references=refs_by_clause.get(c_num, []),
                page_refs=[p_num],
                provenance=ChunkProvenance(
                    document_id=doc_id,
                    source_id=source_id,
                    standard_number=std_num,
                    clause=c_num or t_num_raw,
                    pages=[p_num],
                    section=t_title,
                    original_text_snippet=table_text[:200],
                ),
                metadata={"table_number": t_num, "table_id": t_num_raw, "total_rows": len(structured_rows)},
            )
            table_chunks.append(chunk)

        return table_chunks
