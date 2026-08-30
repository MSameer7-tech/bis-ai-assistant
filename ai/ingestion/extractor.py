"""
PDF Extraction Module for page-level text extraction with exact page preservation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts raw text and structural layout from PDF documents, preserving exact page numbers."""

    def __init__(self, min_text_len_threshold: int = 10):
        self.min_text_len_threshold = min_text_len_threshold

    def extract_pages(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts text from each page of the PDF file.
        Returns a list of page dictionaries preserving 1-indexed page numbers.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = pymupdf.open(str(pdf_path))
        pages_data: List[Dict[str, Any]] = []

        try:
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_num = page_idx + 1
                text = page.get_text("text")

                # Detect if page contains images / drawings (potential scanned content)
                image_list = page.get_images(full=True)
                has_images = len(image_list) > 0

                page_record = {
                    "page_number": page_num,
                    "text": text,
                    "char_count": len(text),
                    "line_count": len(text.splitlines()),
                    "has_images": has_images,
                    "image_count": len(image_list),
                    "is_scanned_likely": len(text.strip()) < self.min_text_len_threshold and has_images,
                }
                pages_data.append(page_record)

            logger.info("Extracted %d pages from %s", len(pages_data), pdf_path.name)
            return pages_data
        finally:
            doc.close()


def extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    """Convenience helper function to extract pages from a PDF."""
    extractor = PDFExtractor()
    return extractor.extract_pages(pdf_path)
