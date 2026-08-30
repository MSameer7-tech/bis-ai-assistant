"""
Ingestion Subpackage for BIS AI Assistant.
Handles PDF loading, OCR quality assessment, structural parsing, table extraction,
change detection gates, document statuses, ingestion manifests, and automated update pipelines.
"""

from ai.ingestion.change_detector import ChangeDetector, check_source_freshness, compute_sha256
from ai.ingestion.extractor import PDFExtractor
from ai.ingestion.manifest import IngestionManifestManager, update_ingestion_manifest
from ai.ingestion.ocr import OCRFallbackEngine
from ai.ingestion.processor import DocumentProcessor
from ai.ingestion.status import DocumentStatus
from ai.ingestion.structure_parser import StructureParser
from ai.ingestion.table_parser import TableParser
from ai.ingestion.update_pipeline import IncrementalUpdatePipeline

__all__ = [
    "PDFExtractor",
    "OCRFallbackEngine",
    "StructureParser",
    "TableParser",
    "DocumentProcessor",
    "ChangeDetector",
    "check_source_freshness",
    "compute_sha256",
    "DocumentStatus",
    "IngestionManifestManager",
    "update_ingestion_manifest",
    "IncrementalUpdatePipeline",
]
