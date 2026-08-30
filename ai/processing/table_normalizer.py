"""
Table Normalizer Module.
Transforms raw extracted table structures into typed semantic table records
with normalized keys, parsed numerical values, units, and clause associations.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TableNormalizer:
    """Normalizes raw table rows into structured semantic dictionaries."""

    def normalize_tables(self, processed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes all tables in the document and returns typed normalized table records.
        """
        doc_id = processed_doc.get("document_id", "DOC-UNKNOWN")
        raw_tables = processed_doc.get("tables", [])
        normalized_tables: List[Dict[str, Any]] = []

        for idx, tab in enumerate(raw_tables):
            table_id = tab.get("table_id") or f"DOC{doc_id.replace('-', '')}-T{idx + 1}"
            caption = tab.get("caption", f"Table {idx + 1}")
            page_num = tab.get("page_number", 1)
            clause_num = tab.get("clause_number", "")
            headers = tab.get("headers", [])
            raw_rows = tab.get("rows", [])

            # Clean header keys (e.g. "Dimension (1)" -> "dimension", "B15 (2)" -> "b15")
            clean_headers = []
            for h in headers:
                cleaned = re.sub(r"\([0-9]+\)", "", h).strip().lower()
                cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned).strip("_")
                clean_headers.append(cleaned or "column")

            typed_rows = []
            for r in raw_rows:
                row_dict: Dict[str, Any] = {}
                for col_idx, cell in enumerate(r):
                    key = clean_headers[col_idx] if col_idx < len(clean_headers) else f"col_{col_idx}"
                    cell_val = str(cell).strip()

                    # Try parsing float / int
                    try:
                        if "." in cell_val:
                            parsed_val: Any = float(cell_val)
                        else:
                            parsed_val = int(cell_val)
                    except ValueError:
                        parsed_val = cell_val

                    row_dict[key] = parsed_val
                typed_rows.append(row_dict)

            normalized_tables.append({
                "table_id": table_id,
                "title": caption,
                "clause": clause_num,
                "source_page": page_num,
                "headers": headers,
                "normalized_headers": clean_headers,
                "rows": typed_rows,
                "raw_markdown": tab.get("raw_markdown", ""),
            })

        logger.info("Normalized %d tables for %s", len(normalized_tables), doc_id)
        return normalized_tables
