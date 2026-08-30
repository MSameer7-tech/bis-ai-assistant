"""
Table Parser Module to detect and extract tabular data from PDF documents
with exact page numbers and column/row structures.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

logger = logging.getLogger(__name__)

TABLE_TITLE_PATTERN = re.compile(
    r"(?:Table\s+(\d+[A-Za-z]?))\s*[:\-—]?\s*([^\n\r]+)",
    re.IGNORECASE,
)


class TableParser:
    """Detects and extracts structured tables from PDF pages."""

    def extract_tables_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts structured tables from all pages of the PDF.
        Returns a list of table dictionaries with headers, rows, and page numbers.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(str(pdf_path))
        extracted_tables: List[Dict[str, Any]] = []

        try:
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_num = page_idx + 1

                # 1. Use PyMuPDF table finder if available
                try:
                    tabs = page.find_tables()
                    for t_idx, tab in enumerate(tabs):
                        tab_data = tab.extract()
                        if tab_data and len(tab_data) > 1:
                            headers = [str(c or "").strip() for c in tab_data[0]]
                            rows = [[str(c or "").strip() for c in r] for r in tab_data[1:]]

                            # Attempt to find table title from surrounding text
                            page_text = page.get_text()
                            title_match = TABLE_TITLE_PATTERN.search(page_text)
                            table_id = f"Table {title_match.group(1)}" if title_match else f"Table {len(extracted_tables) + 1}"
                            table_title = title_match.group(2).strip() if title_match else "Tabular Data"

                            extracted_tables.append({
                                "table_id": table_id,
                                "title": table_title,
                                "page_number": page_num,
                                "headers": headers,
                                "rows": rows,
                                "row_count": len(rows),
                                "col_count": len(headers),
                            })
                except Exception as e:
                    logger.debug("Table extraction skipped on page %d: %s", page_num, e)

            logger.info("Extracted %d tables from %s", len(extracted_tables), pdf_path.name)
            return extracted_tables
        finally:
            doc.close()


def extract_tables(pdf_path: Path) -> List[Dict[str, Any]]:
    """Convenience helper function to extract tables from a PDF."""
    parser = TableParser()
    return parser.extract_tables_from_pdf(pdf_path)
