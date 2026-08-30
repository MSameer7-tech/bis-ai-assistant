"""
Selective OCR Fallback Module for scanned PDF pages and low-text diagrams.
Applies OCR only when text extraction quality is below threshold and records OCR provenance.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import pymupdf

logger = logging.getLogger(__name__)


class OCRFallbackEngine:
    """Selectively applies OCR fallback on low-text or scanned pages with provenance recording."""

    def __init__(self, min_char_threshold: int = 50, min_word_threshold: int = 10):
        self.min_char_threshold = min_char_threshold
        self.min_word_threshold = min_word_threshold

    def process_scanned_pages(
        self, pdf_path: Path, pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Inspects extracted pages and applies OCR fallback only when page text quality < threshold.
        Updates page metadata with extraction_method='ocr' and ocr_used=True if OCR succeeds.
        """
        doc = pymupdf.open(str(pdf_path))
        try:
            for page_record in pages_data:
                # Selective trigger: only when text is suspiciously low or page is flagged scanned
                needs_ocr = (
                    page_record.get("quality_flag") in ("SUSPICIOUS_LOW_TEXT", "SUSPICIOUS_EMPTY")
                    or page_record.get("is_scanned_likely")
                    or page_record.get("char_count", 0) < self.min_char_threshold
                )

                if needs_ocr:
                    page_idx = page_record["page_number"] - 1
                    page = doc[page_idx]
                    logger.info("Executing selective OCR on page %d of %s", page_record["page_number"], pdf_path.name)

                    try:
                        # Attempt PyMuPDF built-in OCR (Tesseract bindings)
                        tp = page.get_textpage_ocr(language="eng", dpi=150, full=True)
                        ocr_text = tp.extractText()

                        if len(ocr_text.strip()) > len(page_record["text"].strip()):
                            page_record["text"] = ocr_text
                            page_record["char_count"] = len(ocr_text)
                            page_record["word_count"] = len(ocr_text.split())
                            page_record["line_count"] = len(ocr_text.splitlines())
                            page_record["extraction_method"] = "ocr"
                            page_record["ocr_used"] = True
                            page_record["quality_flag"] = "OK"
                            logger.info("✅ OCR succeeded on page %d (%d chars)", page_record["page_number"], len(ocr_text))
                    except Exception as e:
                        logger.warning("OCR fallback not available or failed on page %d: %s", page_record["page_number"], e)
                        page_record["ocr_used"] = False

            return pages_data
        finally:
            doc.close()


def apply_ocr_fallback_if_needed(
    pdf_path: Path, pages_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Convenience helper function to apply selective OCR fallback."""
    engine = OCRFallbackEngine()
    return engine.process_scanned_pages(pdf_path, pages_data)
