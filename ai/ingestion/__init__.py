"""
Ingestion Subpackage for BIS AI Assistant.
Handles PDF loading, OCR quality assessment, structural parsing, table extraction,
and change detection / data freshness gates.
"""

from ai.ingestion.change_detector import ChangeDetector, check_source_freshness, compute_sha256
from ai.ingestion.extractor import PDFExtractor
from ai.ingestion.ocr import OCRFallbackEngine
from ai.ingestion.processor import DocumentProcessor
from ai.ingestion.structure_parser import StructureParser
from ai.ingestion.table_parser import TableParser

__all__ = [
    "PDFExtractor",
    "OCRFallbackEngine",
    "StructureParser",
    "TableParser",
    "DocumentProcessor",
    "ChangeDetector",
    "check_source_freshness",
    "compute_sha256",
]
