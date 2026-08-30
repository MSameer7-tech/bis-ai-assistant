"""
Ingestion Subpackage for BIS AI Assistant.
Handles acquisition, cryptographic provenance, PDF extraction, OCR fallback,
structure parsing, table extraction, and structured JSON generation.
"""

from ai.ingestion.acquisition import compute_sha256, register_acquired_document
from ai.ingestion.extractor import PDFExtractor, extract_pdf_pages
from ai.ingestion.ocr import OCRFallbackEngine, apply_ocr_fallback_if_needed
from ai.ingestion.processor import DocumentProcessor, process_all_documents, process_document
from ai.ingestion.structure_parser import StructureParser, parse_structure
from ai.ingestion.table_parser import TableParser, extract_tables

__all__ = [
    "compute_sha256",
    "register_acquired_document",
    "PDFExtractor",
    "extract_pdf_pages",
    "StructureParser",
    "parse_structure",
    "TableParser",
    "extract_tables",
    "OCRFallbackEngine",
    "apply_ocr_fallback_if_needed",
    "DocumentProcessor",
    "process_document",
    "process_all_documents",
]
