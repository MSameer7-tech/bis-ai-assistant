"""
Phase 5C: Universal Ingestion Pipeline Runner for Multi-Domain BIS Documents.
Executes Phase 2C Extraction, Phase 2D Normalization, and Phase 2E Chunking
using the exact same canonical schema validated on DOC-001.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ai.processing.normalizer import DocumentNormalizer
from ai.processing.schema import (
    make_clause_id,
    make_parameter_id,
    make_requirement_id,
    make_section_id,
    make_standard_id,
    make_table_id,
    make_term_id,
    make_test_id,
)
from ai.chunking.chunker import StructureAwareChunker
from scripts.acquire_multi_domain_corpus import CORPUS_SPECS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def parse_content_into_processed_doc(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 2C Extraction: Formats raw spec text into canonical processed document JSON."""
    doc_id = spec["doc_id"]
    src_id = spec["src_id"]
    std_num = spec["std_num"]
    title = spec["title"]
    lines = [l.strip() for l in spec["content_summary"].strip().split("\n") if l.strip()]

    clauses: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    referenced_stds: List[str] = []

    # 1. Add Clause 1: Scope for standard identification and domain coverage
    domain = spec["domain"]
    cat = spec["category"]
    p_type = spec["product_type"]
    scope_clause = {
        "clause_id": make_clause_id(doc_id, "1"),
        "clause_number": "1",
        "title": "Scope",
        "content": f"Scope: This Indian Standard ({std_num}) covers and specifies requirements for {title}. It applies to {p_type} under {cat} category in the {domain} domain.",
        "page_start": 1,
        "page_end": 1,
        "page_refs": [1],
        "subclauses": []
    }
    clauses.append(scope_clause)

    page_num = 2
    for idx, line in enumerate(lines):
        if line.startswith("Clause "):
            # Example: Clause 8.1 Air Delivery: The minimum air delivery...
            parts = line.split(":", 1)
            header_parts = parts[0].replace("Clause ", "").strip().split(" ", 1)
            c_num = header_parts[0]
            c_title = header_parts[1] if len(header_parts) > 1 else "Requirement"
            c_body = parts[1].strip() if len(parts) > 1 else ""

            clause_entry = {
                "clause_id": make_clause_id(doc_id, c_num),
                "clause_number": c_num,
                "title": c_title,
                "content": f"{c_title}: {c_body}",
                "page_start": page_num,
                "page_end": page_num + 1,
                "page_refs": [page_num, page_num + 1],
                "subclauses": []
            }
            clauses.append(clause_entry)
            page_num += 1

        elif line.startswith("Table "):
            # Example: Table 1: Air Delivery Requirements...
            parts = line.split(":", 1)
            t_num = parts[0].replace("Table ", "").strip()
            t_title = parts[1].strip() if len(parts) > 1 else "Requirements Table"

            table_entry = {
                "table_id": make_table_id(doc_id, t_num),
                "table_number": t_num,
                "title": t_title,
                "clause_ref": "8.1" if "fan" in doc_id.lower() or "374" in std_num else "6.1",
                "page_refs": [page_num],
                "content": f"Table {t_num}: {t_title}",
                "rows": [
                    {"parameter": t_title, "value": "Refer to Table specifications", "normative_status": "mandatory"}
                ]
            }
            tables.append(table_entry)
            page_num += 1

        elif line.startswith("Referenced Standards:"):
            refs_str = line.replace("Referenced Standards:", "").strip()
            referenced_stds = [r.strip() for r in refs_str.split(",") if r.strip()]

    # Canonical Phase 2C Processed Structure
    processed_doc = {
        "document_id": doc_id,
        "source_id": src_id,
        "document_metadata": {
            "title": title,
            "standard_number": std_num,
            "edition": spec["version_edition"],
            "publication_date": spec["pub_date"],
            "product_domain": spec["domain"],
            "product_category": spec["category"],
            "product_type": spec["product_type"],
            "temporal_validity": {
                "status": "current" if spec["valid_until"] is None else "superseded",
                "valid_from": spec["valid_from"],
                "valid_until": spec["valid_until"]
            },
            "issuing_authority": spec["authority"]
        },
        "pages": [
            {
                "page_number": p,
                "text": f"Page {p} of {std_num} - {title}",
                "has_tables": bool(tables),
                "has_diagrams": False
            } for p in range(1, max(page_num, 3))
        ],
        "clauses": clauses,
        "tables": tables,
        "annexes": [],
        "referenced_standards": referenced_stds
    }
    return processed_doc


def process_and_chunk_all() -> None:
    logger.info("Executing Universal 2C -> 2D -> 2E Ingestion Pipeline...")
    normalizer = DocumentNormalizer()
    chunker = StructureAwareChunker()

    total_chunks_created = 0

    for spec in CORPUS_SPECS:
        doc_id = spec["doc_id"]
        
        # 1. Phase 2C: Extraction
        processed_doc = parse_content_into_processed_doc(spec)
        processed_file = PROCESSED_DIR / f"{doc_id}.json"
        with open(processed_file, "w", encoding="utf-8") as f:
            json.dump(processed_doc, f, indent=2, ensure_ascii=False)

        # 2. Phase 2D: Semantic Normalization
        normalized_doc = normalizer.normalize_document(doc_id)
        normalized_file_alias = NORMALIZED_DIR / f"{doc_id}.normalized.json"
        with open(normalized_file_alias, "w", encoding="utf-8") as f:
            json.dump(normalized_doc, f, indent=2, ensure_ascii=False)

        # 3. Phase 2E: Structure-Aware Universal Chunking
        chunks = chunker.chunk_document(doc_id)

        total_chunks_created += len(chunks)
        logger.info("Processed %s (%s): %d clauses, %d entities, %d chunks",
                    doc_id, spec["std_num"], len(processed_doc["clauses"]), len(normalized_doc.get("entities", [])), len(chunks))

    logger.info("✅ Multi-Domain Pipeline Finished. Generated %d universal chunks across %d standards.",
                total_chunks_created, len(CORPUS_SPECS))


if __name__ == "__main__":
    process_and_chunk_all()
