"""
PDF Extraction Module for page-level text extraction with exact page preservation,
rich per-page metadata, and extraction quality metrics.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts raw text and structural layout from PDF documents, preserving exact page numbers and quality metrics."""

    def __init__(self, min_char_threshold: int = 50, min_word_threshold: int = 10):
        self.min_char_threshold = min_char_threshold
        self.min_word_threshold = min_word_threshold

    def extract_pages(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts text from each page of the PDF file with complete audit metadata.
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

                char_count = len(text)
                words = text.split()
                word_count = len(words)
                lines = text.splitlines()
                line_count = len(lines)

                # Image inspection
                image_list = page.get_images(full=True)
                has_images = len(image_list) > 0

                # Quality check & suspicion flag
                is_empty = char_count == 0 or len(text.strip()) == 0
                if is_empty:
                    quality_flag = "SUSPICIOUS_EMPTY"
                elif char_count < self.min_char_threshold or word_count < self.min_word_threshold:
                    quality_flag = "SUSPICIOUS_LOW_TEXT"
                else:
                    quality_flag = "OK"

                page_record = {
                    "page_number": page_num,
                    "text": text,
                    "char_count": char_count,
                    "word_count": word_count,
                    "line_count": line_count,
                    "extraction_method": "pymupdf",
                    "is_empty": is_empty,
                    "ocr_used": False,
                    "has_images": has_images,
                    "image_count": len(image_list),
                    "quality_flag": quality_flag,
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
