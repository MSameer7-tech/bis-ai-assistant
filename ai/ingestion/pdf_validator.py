"""
Multi-Tier PDF Integrity Validator.
Rigorously classifies document files into:
- VALID_PDF
- TEXT_PDF
- SCANNED_PDF
- HTML_IN_PDF_EXTENSION
- CORRUPTED
- ZERO_BYTE
- PARTIAL_DOWNLOAD
- PASSWORD_PROTECTED
"""
import os
import sys
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import pymupdf

logger = logging.getLogger(__name__)


class PDFValidationStatus(str, Enum):
    VALID_PDF = "VALID_PDF"
    TEXT_PDF = "TEXT_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    HTML_IN_PDF_EXTENSION = "HTML_IN_PDF_EXTENSION"
    CORRUPTED = "CORRUPTED"
    ZERO_BYTE = "ZERO_BYTE"
    PARTIAL_DOWNLOAD = "PARTIAL_DOWNLOAD"
    PASSWORD_PROTECTED = "PASSWORD_PROTECTED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"


class PDFValidator:
    """
    Validates file format, magic bytes, structure integrity, and extractability using PyMuPDF.
    """

    @staticmethod
    def validate_file(file_path: Path) -> Dict[str, Any]:
        """
        Validates a single PDF file and returns a structured validation report.
        """
        fp = Path(file_path)
        result = {
            "file_path": str(fp),
            "file_name": fp.name,
            "exists": False,
            "size_bytes": 0,
            "status": PDFValidationStatus.FILE_NOT_FOUND.value,
            "page_count": 0,
            "has_text": False,
            "extracted_characters": 0,
            "magic_bytes": False,
            "is_encrypted": False,
            "error_details": None
        }

        if not fp.exists():
            result["error_details"] = f"File not found: {fp}"
            return result

        result["exists"] = True
        size = fp.stat().st_size
        result["size_bytes"] = size

        if size == 0:
            result["status"] = PDFValidationStatus.ZERO_BYTE.value
            result["error_details"] = "File size is 0 bytes"
            return result

        # Read first 1024 bytes for magic bytes and HTML signatures
        try:
            with open(fp, "rb") as f:
                header = f.read(1024)
        except Exception as e:
            result["status"] = PDFValidationStatus.CORRUPTED.value
            result["error_details"] = f"Failed to read file header: {e}"
            return result

        # Check for HTML redirect/error page masquerading as PDF
        lower_header = header.lower()
        if (
            lower_header.startswith(b"<!doctype html")
            or lower_header.startswith(b"<html")
            or b"<html" in lower_header
            or b"<head>" in lower_header
            or b"404 not found" in lower_header
            or b"403 forbidden" in lower_header
        ):
            result["status"] = PDFValidationStatus.HTML_IN_PDF_EXTENSION.value
            result["error_details"] = "File contains HTML web markup, not PDF binary data"
            return result

        # Check %PDF- magic bytes
        has_magic = header.startswith(b"%PDF-") or b"%PDF-" in header[:128]
        result["magic_bytes"] = has_magic

        if not has_magic:
            result["status"] = PDFValidationStatus.CORRUPTED.value
            result["error_details"] = "Missing %PDF- magic bytes in file header"
            return result

        # Attempt to parse with PyMuPDF
        try:
            doc = pymupdf.open(str(fp))
            
            if doc.is_encrypted:
                result["is_encrypted"] = True
                result["status"] = PDFValidationStatus.PASSWORD_PROTECTED.value
                result["error_details"] = "PDF is password-protected or encrypted"
                doc.close()
                return result

            page_count = len(doc)
            result["page_count"] = page_count

            if page_count == 0:
                result["status"] = PDFValidationStatus.CORRUPTED.value
                result["error_details"] = "PDF parsed but has 0 pages"
                doc.close()
                return result

            # Check text extractability across first 5 pages
            total_text_len = 0
            for page_idx in range(min(5, page_count)):
                try:
                    page = doc[page_idx]
                    text = page.get_text() or ""
                    total_text_len += len(text.strip())
                except Exception:
                    pass

            doc.close()
            result["extracted_characters"] = total_text_len

            if total_text_len > 20:
                result["has_text"] = True
                result["status"] = PDFValidationStatus.TEXT_PDF.value
            else:
                result["has_text"] = False
                result["status"] = PDFValidationStatus.SCANNED_PDF.value

            return result

        except Exception as e:
            err_str = str(e).lower()
            if "eof" in err_str or "truncated" in err_str:
                result["status"] = PDFValidationStatus.PARTIAL_DOWNLOAD.value
                result["error_details"] = f"Incomplete / truncated download: {e}"
            else:
                result["status"] = PDFValidationStatus.CORRUPTED.value
                result["error_details"] = f"PDF syntax / xref error: {e}"
            return result

    @classmethod
    def validate_directory(cls, directory_path: Path) -> List[Dict[str, Any]]:
        """
        Validates all PDF files in a directory recursively.
        """
        dp = Path(directory_path)
        results = []
        if not dp.exists():
            return results

        for p in sorted(dp.glob("**/*.pdf")):
            if p.is_file() and not p.name.startswith("."):
                results.append(cls.validate_file(p))
        return results
