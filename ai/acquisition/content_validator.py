"""
Binary Content and Magic-Byte Validator (Phase 3D).
Guards the raw corpus against corrupted downloads, empty files, and HTML error pages masquerading as PDFs.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

PDF_MAGIC_HEADER = b"%PDF-"
HTML_SIGNATURES = [b"<!doctype html", b"<html", b"<head", b"<body"]


class ContentValidator:
    """Validates raw acquired file bytes against format signatures and content-type headers."""

    def validate_file(
        self,
        file_path: Path,
        expected_format: str,
        reported_content_type: Optional[str] = None,
        min_bytes: int = 16
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates binary content of downloaded file.
        Returns (is_valid, failure_reason).
        """
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"

        size = file_path.stat().st_size
        if size < min_bytes:
            return False, f"File payload too small ({size} bytes < minimum {min_bytes} bytes)"

        with open(file_path, "rb") as f:
            header_sample = f.read(512).lower()

        fmt = expected_format.upper()

        # 1. PDF Validation
        if fmt == "PDF":
            if not header_sample.startswith(PDF_MAGIC_HEADER.lower()):
                # Check if it is an HTML error page masquerading as PDF
                if any(sig in header_sample for sig in HTML_SIGNATURES):
                    return False, "Corrupted/Masquerading payload: Expected PDF but received HTML error/redirect page"
                return False, "Invalid PDF: Missing '%PDF-' magic byte header"

            if reported_content_type and "html" in reported_content_type.lower():
                return False, f"Content-Type mismatch: Reported '{reported_content_type}' for PDF download"

        # 2. HTML Validation
        elif fmt == "HTML":
            if not any(sig in header_sample for sig in HTML_SIGNATURES):
                return False, "Invalid HTML: Missing doctype or html tag in header"

        # 3. JSON Validation
        elif fmt == "JSON":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
            except Exception as e:
                return False, f"Invalid JSON payload: {e}"

        return True, None
