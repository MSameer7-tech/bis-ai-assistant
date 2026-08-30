"""
Table Parser Module to detect and extract tabular data from PDF documents
with exact page numbers, enclosing clause association, and table IDs.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymupdf

logger = logging.getLogger(__name__)

TABLE_TITLE_PATTERN = re.compile(
    r"(?:Table\s+([0-9A-Za-z]+))\s*[:\-—]?\s*([^\n\r]+)",
    re.IGNORECASE,
)

CLAUSE_IN_TEXT_PATTERN = re.compile(
    r"\b(?:Clause\s+)?([0-9]{1,2}(?:\.[0-9]{1,2})?)\b",
    re.IGNORECASE,
)


class TableParser:
    """Detects and extracts structured tables from PDF pages with clause and page associations."""

    def extract_tables_from_pdf(
        self, pdf_path: Path, flat_clauses: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts structured tables from all pages of the PDF.
        Maps each table to its enclosing clause and records page numbers.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(str(pdf_path))
        extracted_tables: List[Dict[str, Any]] = []

        try:
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_num = page_idx + 1

                try:
                    tabs = page.find_tables()
                    for t_idx, tab in enumerate(tabs):
                        tab_data = tab.extract()
                        if tab_data and len(tab_data) > 1:
                            headers = [str(c or "").strip() for c in tab_data[0]]
                            rows = [[str(c or "").strip() for c in r] for r in tab_data[1:]]

                            # Attempt to find table title from page text
                            page_text = page.get_text()
                            title_match = TABLE_TITLE_PATTERN.search(page_text)
                            table_num = title_match.group(1) if title_match else f"{len(extracted_tables) + 1}"
                            caption = title_match.group(2).strip() if title_match else f"Table {table_num}"
                            table_id = f"T-{str(table_num).zfill(3)}"

                            # Associate with enclosing clause on that page
                            associated_clause = None
                            if flat_clauses:
                                for c in flat_clauses:
                                    if page_num in c.get("page_refs", [c.get("page_start")]):
                                        associated_clause = c["clause_number"]

                            # Markdown representation
                            md_header = "| " + " | ".join(headers) + " |"
                            md_divider = "| " + " | ".join(["---"] * len(headers)) + " |"
                            md_rows = ["| " + " | ".join(r) + " |" for r in rows]
                            raw_markdown = "\n".join([md_header, md_divider] + md_rows)

                            extracted_tables.append({
                                "table_id": table_id,
                                "caption": caption,
                                "page_number": page_num,
                                "clause_number": associated_clause,
                                "headers": headers,
                                "rows": rows,
                                "row_count": len(rows),
                                "col_count": len(headers),
                                "raw_markdown": raw_markdown,
                            })
                except Exception as e:
                    logger.debug("Table extraction skipped on page %d: %s", page_num, e)

            logger.info("Extracted %d tables from %s", len(extracted_tables), pdf_path.name)
            return extracted_tables
        finally:
            doc.close()


def extract_tables(
    pdf_path: Path, flat_clauses: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Convenience helper function to extract tables from a PDF."""
    parser = TableParser()
    return parser.extract_tables_from_pdf(pdf_path, flat_clauses)
