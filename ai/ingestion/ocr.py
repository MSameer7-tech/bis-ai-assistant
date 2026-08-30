"""
OCR Fallback Module for scanned PDF pages and diagram text extraction.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

logger = logging.getLogger(__name__)


class OCRFallbackEngine:
    """Handles scanned pages where standard text extraction returns empty or minimal text."""

    def __init__(self, min_char_threshold: int = 15):
        self.min_char_threshold = min_char_threshold

    def process_scanned_pages(
        self, pdf_path: Path, pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Inspects extracted pages and applies OCR fallback if a page is likely scanned.
        Returns the updated pages data list.
        """
        doc = pymupdf.open(str(pdf_path))
        try:
            for page_record in pages_data:
                if page_record.get("is_scanned_likely"):
                    page_idx = page_record["page_number"] - 1
                    page = doc[page_idx]
                    logger.info("Attempting OCR fallback on page %d of %s", page_record["page_number"], pdf_path.name)

                    try:
                        # Attempt PyMuPDF built-in OCR if OCR support / Tesseract is available
                        tp = page.get_textpage_ocr(language="eng", dpi=150, full=True)
                        ocr_text = tp.extractText()
                        if len(ocr_text.strip()) > len(page_record["text"].strip()):
                            page_record["text"] = ocr_text
                            page_record["ocr_applied"] = True
                            page_record["char_count"] = len(ocr_text)
                    except Exception as e:
                        logger.warning("OCR fallback not available or failed on page %d: %s", page_record["page_number"], e)
                        page_record["ocr_applied"] = False

            return pages_data
        finally:
            doc.close()


def apply_ocr_fallback_if_needed(
    pdf_path: Path, pages_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Convenience helper function to apply OCR fallback."""
    engine = OCRFallbackEngine()
    return engine.process_scanned_pages(pdf_path, pages_data)
