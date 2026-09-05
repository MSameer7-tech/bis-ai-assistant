"""
Evidence Unit Formulation & Cryptographic Provenance Builder (Phase 4D).
Transforms real extracted clauses, tables, and records into atomic, cryptographically anchored Evidence Units.
Strictly rejects documents with missing raw SHA-256 parent digests.
"""
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from ai.processing.document_extractor import ExtractedDocument, ExtractedClause, ExtractedTable

logger = logging.getLogger(__name__)


class EvidenceUnit(BaseModel):
    """Atomic, cryptographically anchored evidence container for RAG retrieval and compliance verification."""
    evidence_unit_id: str = Field(..., description="Deterministic unique ID, e.g. EV-IS-1786-2008-P3-CL-4.2")
    document_id: str
    document_family_id: str
    document_type: str
    authority_class: str
    source_url: str = Field(..., description="Original URL the document was acquired from")
    section_or_clause: str
    heading: str
    content_text: str
    content_type: str  # CLAUSE, TABLE, DEFINITION, TEST_METHOD, SAMPLING_PLAN, MARKING_RULE, STATUTORY_ORDER
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    parent_raw_sha256: str
    unit_content_sha256: str
    citation_anchor: str = Field(..., description="Verifiable human-readable citation anchor")
    page_number: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def compute_text_sha256(text: str) -> str:
    """Computes SHA-256 hash over clean text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_clause_identifier(raw_id: str) -> str:
    """Normalizes clause numbers into canonical dot-separated format, e.g. '4 . 1' -> '4.1', '4_1' -> '4.1'."""
    clean = raw_id.strip()
    clean = re.sub(r"[\s_-]+", ".", clean)
    clean = re.sub(r"\.+", ".", clean)
    clean = clean.strip(".")
    return clean if clean else "1"


class EvidenceUnitBuilder:
    """Builds atomic Evidence Units from ExtractedDocument structures with zero synthetic fallbacks."""

    def build_evidence_units(self, doc: ExtractedDocument) -> Tuple[List[EvidenceUnit], Optional[str]]:
        """
        Decomposes an ExtractedDocument into individual atomic Evidence Units.
        Returns (units, error_reason). If parent raw SHA-256 is missing, returns ([], error).
        """
        if not doc.is_success:
            return [], f"Cannot build evidence units for failed extraction: {doc.error_reason}"

        doc_id = doc.document_id
        fam_id = doc.document_family_id
        doc_type = doc.document_type
        authority_class = doc.metadata.get("document", {}).get("authority_class", "PRIMARY_NORMATIVE")
        parent_sha = doc.metadata.get("acquisition", {}).get("sha256")

        source_url = (
            doc.metadata.get("source", {}).get("canonical_source_url") or
            doc.metadata.get("acquisition", {}).get("final_url") or
            "UNKNOWN_URL"
        )

        # Strict Provenance Gate: Reject documents without verifiable parent raw SHA-256
        if not parent_sha or len(parent_sha) != 64 or parent_sha == "UNKNOWN_PARENT_HASH":
            return [], f"QUARANTINE: Document {doc_id} is missing valid 64-char parent raw SHA-256 digest"

        units: List[EvidenceUnit] = []

        # 1. Build Units from Clauses
        for clause in doc.clauses:
            cl_no = normalize_clause_identifier(clause.clause_number)
            p_num = clause.page_number or 1
            unit_id = f"EV-{doc_id}-P{p_num}-CL-{cl_no}"
            unit_sha = compute_text_sha256(clause.content_text)

            # Map clause_type to content_type
            ctype = "CLAUSE"
            if clause.clause_type == "STATUTORY":
                ctype = "STATUTORY_ORDER"
            elif clause.clause_type == "TERMINOLOGY":
                ctype = "DEFINITION"
            elif clause.clause_type == "MARKING":
                ctype = "MARKING_RULE"
            elif clause.clause_type == "SAMPLING":
                ctype = "SAMPLING_PLAN"
            elif clause.clause_type == "TEST_METHOD":
                ctype = "TEST_METHOD"

            citation_anchor = f"{doc_id}, Page {p_num}, Clause {clause.clause_number}"
            if clause.heading:
                citation_anchor += f" ({clause.heading})"

            units.append(
                EvidenceUnit(
                    evidence_unit_id=unit_id,
                    document_id=doc_id,
                    document_family_id=fam_id,
                    document_type=doc_type,
                    authority_class=authority_class,
                    source_url=source_url,
                    section_or_clause=clause.clause_number,
                    heading=clause.heading,
                    content_text=clause.content_text,
                    content_type=ctype,
                    structured_data={"clause_type": clause.clause_type},
                    parent_raw_sha256=parent_sha,
                    unit_content_sha256=unit_sha,
                    citation_anchor=citation_anchor,
                    page_number=clause.page_number
                )
            )

        # 2. Build Units from Tables
        for table in doc.tables:
            p_num = table.page_number or 1
            raw_tnum = table.table_number or table.table_id
            clean_tnum = normalize_clause_identifier(raw_tnum)
            unit_id = f"EV-{doc_id}-P{p_num}-TAB-{clean_tnum}"

            # Format table content as clean markdown
            md_lines = []
            if table.title:
                md_lines.append(f"### {table.table_number or ''}: {table.title}\n")
            if table.headers:
                md_lines.append("| " + " | ".join(table.headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
            for row in table.rows:
                md_lines.append("| " + " | ".join(row) + " |")

            tab_text = "\n".join(md_lines) if md_lines else f"Table {table.table_number}"
            tab_sha = compute_text_sha256(tab_text)

            citation_anchor = f"{doc_id}, Page {p_num}, {table.table_number or 'Table'}"
            if table.title:
                citation_anchor += f" ({table.title})"

            units.append(
                EvidenceUnit(
                    evidence_unit_id=unit_id,
                    document_id=doc_id,
                    document_family_id=fam_id,
                    document_type=doc_type,
                    authority_class=authority_class,
                    source_url=source_url,
                    section_or_clause=table.table_number or "TABLE",
                    heading=table.title or f"Table {table.table_number}",
                    content_text=tab_text,
                    content_type="TABLE",
                    structured_data={
                        "headers": table.headers,
                        "rows": table.rows,
                        "table_id": table.table_id
                    },
                    parent_raw_sha256=parent_sha,
                    unit_content_sha256=tab_sha,
                    citation_anchor=citation_anchor,
                    page_number=p_num
                )
            )

        return units, None
