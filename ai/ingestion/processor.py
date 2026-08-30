"""
Document Ingestion Processor Pipeline.
Orchestrates PDF text extraction, OCR fallback, structure parsing, and table extraction,
generating structured machine-readable JSON in data/processed/ with full provenance tracking.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.ingestion.extractor import PDFExtractor
from ai.ingestion.ocr import OCRFallbackEngine
from ai.ingestion.structure_parser import StructureParser
from ai.ingestion.table_parser import TableParser

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
METADATA_DIR = ROOT_DIR / "data" / "metadata"
DOCUMENTS_PATH = METADATA_DIR / "documents.json"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"
EXTRACTION_LOG_PATH = METADATA_DIR / "extraction_log.json"


class DocumentProcessor:
    """Orchestrates extraction, structure detection, and JSON normalization for acquired documents."""

    def __init__(self):
        self.extractor = PDFExtractor()
        self.ocr_engine = OCRFallbackEngine()
        self.structure_parser = StructureParser()
        self.table_parser = TableParser()
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Executes the extraction pipeline for a specific document_id.
        Produces data/processed/{document_id}.json and updates extraction log.
        """
        # 1. Load document record
        if not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(f"Documents manifest missing: {DOCUMENTS_PATH}")

        with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
            documents = json.load(f)

        doc_record = next((d for d in documents if d["document_id"] == document_id), None)
        if not doc_record:
            raise ValueError(f"Document ID '{document_id}' not found in {DOCUMENTS_PATH}")

        raw_file_path = ROOT_DIR / doc_record["file_path"]
        if not raw_file_path.exists():
            raise FileNotFoundError(f"Raw PDF file missing: {raw_file_path}")

        logger.info("Processing document %s (%s)", document_id, raw_file_path.name)
        start_time = datetime.now(timezone.utc).isoformat()

        # 2. Extract pages with rich metadata and quality metrics
        pages_data = self.extractor.extract_pages(raw_file_path)

        # 3. Apply OCR fallback if scanned or low text
        pages_data = self.ocr_engine.process_scanned_pages(raw_file_path, pages_data)

        # 4. Parse document structure (sections, clauses, annexes)
        structure_data = self.structure_parser.parse_document_structure(pages_data)

        # 5. Extract tables
        tables_data = self.table_parser.extract_tables_from_pdf(raw_file_path)

        # 6. Quality summary calculation
        ok_pages = [p["page_number"] for p in pages_data if p["quality_flag"] == "OK"]
        suspicious_pages = [p["page_number"] for p in pages_data if p["quality_flag"] != "OK"]

        quality_summary = {
            "total_pages": len(pages_data),
            "ok_pages_count": len(ok_pages),
            "suspicious_pages_count": len(suspicious_pages),
            "suspicious_pages": suspicious_pages,
            "overall_quality": "HIGH" if len(suspicious_pages) == 0 else ("MEDIUM" if len(ok_pages) > len(suspicious_pages) else "LOW"),
        }

        # 7. Assemble normalized document JSON
        processed_document = {
            "document_id": document_id,
            "source_id": doc_record.get("source_id"),
            "standard_or_document_number": doc_record.get("standard_or_document_number"),
            "title": doc_record.get("title"),
            "version_edition": doc_record.get("version_edition"),
            "raw_file_path": doc_record.get("file_path"),
            "file_sha256": doc_record.get("file_sha256"),
            "processed_date": datetime.now(timezone.utc).isoformat(),
            "total_pages": len(pages_data),
            "total_sections": len(structure_data["sections"]),
            "total_clauses": len(structure_data["clauses"]),
            "total_annexes": len(structure_data["annexes"]),
            "total_tables": len(tables_data),
            "quality_summary": quality_summary,
            "pages": pages_data,
            "sections": structure_data["sections"],
            "clauses": structure_data["clauses"],
            "annexes": structure_data["annexes"],
            "tables": tables_data,
        }

        # 8. Save to data/processed/{document_id}.json
        out_file = PROCESSED_DIR / f"{document_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(processed_document, f, indent=2, ensure_ascii=False)

        # 9. Update extraction_log.json
        extraction_logs = []
        if EXTRACTION_LOG_PATH.exists():
            try:
                with open(EXTRACTION_LOG_PATH, "r", encoding="utf-8") as f:
                    extraction_logs = json.load(f)
            except json.JSONDecodeError:
                extraction_logs = []

        log_entry = {
            "document_id": document_id,
            "source_id": doc_record.get("source_id"),
            "start_time": start_time,
            "completion_time": datetime.now(timezone.utc).isoformat(),
            "total_pages": len(pages_data),
            "total_clauses": len(structure_data["clauses"]),
            "total_tables": len(tables_data),
            "quality_summary": quality_summary,
            "processed_file_path": str(out_file.relative_to(ROOT_DIR)),
            "status": "extraction_successful",
        }
        extraction_logs = [l for l in extraction_logs if l["document_id"] != document_id] + [log_entry]
        with open(EXTRACTION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(extraction_logs, f, indent=2, ensure_ascii=False)

        # 10. Advance document status to content_verified in documents.json & source_registry.json
        doc_record["status"] = "content_verified"
        with open(DOCUMENTS_PATH, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
            for item in registry:
                if item.get("document_id") == document_id:
                    item["status"] = "content_verified"
                    break
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)

        logger.info(
            "✅ Successfully processed %s -> %s (%d pages, %d clauses, quality: %s)",
            document_id,
            out_file.name,
            len(pages_data),
            len(structure_data["clauses"]),
            quality_summary["overall_quality"],
        )

        return processed_document

    def process_all_acquired_documents(self) -> Dict[str, Any]:
        """Processes all documents currently in data/metadata/documents.json."""
        if not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(f"Documents manifest missing: {DOCUMENTS_PATH}")

        with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
            documents = json.load(f)

        results = {}
        for doc in documents:
            doc_id = doc["document_id"]
            results[doc_id] = self.process_document(doc_id)

        return results


def process_document(document_id: str) -> Dict[str, Any]:
    """Convenience helper function to process a single document."""
    processor = DocumentProcessor()
    return processor.process_document(document_id)


def process_all_documents() -> Dict[str, Any]:
    """Convenience helper function to process all documents."""
    processor = DocumentProcessor()
    return processor.process_all_acquired_documents()
