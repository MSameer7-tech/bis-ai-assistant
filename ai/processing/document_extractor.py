"""
Generic Multi-Format Document Extractor & Structural Parser (Phase 4A).
Extracts real hierarchical sections, clauses, tables, and definitions from PDF, HTML, and JSON files using PyMuPDF and DOM parsing.
Zero hardcoded document IDs and zero synthetic fallback clauses.
"""
import hashlib
import json
import logging
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

logger = logging.getLogger(__name__)


class ExtractedTable(BaseModel):
    """Structured representation of an extracted regulatory or technical table."""
    table_id: str
    table_number: Optional[str] = None
    title: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    raw_markdown: Optional[str] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedClause(BaseModel):
    """Structured representation of a parsed normative clause or section."""
    clause_number: str
    heading: str
    content_text: str
    clause_type: str = "REQUIREMENT"  # SCOPE, REFERENCES, TERMINOLOGY, REQUIREMENT, TEST_METHOD, SAMPLING, MARKING, STATUTORY
    sub_clauses: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    page_number: Optional[int] = None


class ExtractedDocument(BaseModel):
    """Complete structured extraction of an acquired document."""
    document_id: str
    document_family_id: str
    title: str
    document_type: str
    is_success: bool = True
    error_reason: Optional[str] = None
    pages_count: int = 0
    clauses: List[ExtractedClause] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BISHTMLDOMParser(HTMLParser):
    """Custom HTML parser extracting hierarchical headings, paragraphs, and tables."""

    def __init__(self):
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.tables: List[ExtractedTable] = []
        self.current_tag = ""
        self.current_heading = "Overview"
        self.current_heading_level = 1
        self.current_text_buffer = []
        self.in_table = False
        self.current_table_headers = []
        self.current_table_rows = []
        self.current_row = []
        self.in_th = False
        self.in_td = False
        self.table_counter = 0

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        if tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            # Flush current section text
            self._flush_section()
            self.current_heading_level = int(tag[1])
            self.current_text_buffer = []
        elif tag.lower() == "table":
            self.in_table = True
            self.table_counter += 1
            self.current_table_headers = []
            self.current_table_rows = []
        elif tag.lower() == "tr" and self.in_table:
            self.current_row = []
        elif tag.lower() == "th" and self.in_table:
            self.in_th = True
        elif tag.lower() == "td" and self.in_table:
            self.in_td = True

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = "".join(self.current_text_buffer).strip()
            self.current_text_buffer = []
        elif tag_l == "th" and self.in_table:
            self.in_th = False
        elif tag_l == "td" and self.in_table:
            self.in_td = False
        elif tag_l == "tr" and self.in_table:
            if self.current_row:
                if not self.current_table_headers and self.current_row:
                    # Treat first row as headers if no th found
                    self.current_table_headers = list(self.current_row)
                else:
                    self.current_table_rows.append(list(self.current_row))
                self.current_row = []
        elif tag_l == "table" and self.in_table:
            self.in_table = False
            tab_id = f"TAB-HTML-{self.table_counter}"
            self.tables.append(
                ExtractedTable(
                    table_id=tab_id,
                    table_number=f"Table {self.table_counter}",
                    title=f"HTML Table {self.table_counter}",
                    headers=self.current_table_headers,
                    rows=self.current_table_rows,
                    page_number=1
                )
            )

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self.in_th:
            self.current_table_headers.append(text)
        elif self.in_td:
            self.current_row.append(text)
        else:
            self.current_text_buffer.append(text + " ")

    def _flush_section(self):
        body = "".join(self.current_text_buffer).strip()
        if body or self.current_heading:
            self.sections.append({
                "heading": self.current_heading or "Overview",
                "level": self.current_heading_level,
                "text": body
            })
        self.current_text_buffer = []

    def finalize(self):
        self._flush_section()


def classify_clause_type(heading: str, text: str) -> str:
    """Classifies clause type dynamically based on terminology and semantics."""
    combined = f"{heading} {text}".lower()
    if any(k in combined for k in ["scope", "field of application", "applicability"]):
        return "SCOPE"
    if any(k in combined for k in ["normative reference", "references"]):
        return "REFERENCES"
    if any(k in combined for k in ["terminology", "definition", "definitions", "terms and definitions"]):
        return "TERMINOLOGY"
    if any(k in combined for k in ["sampling", "scale of sampling", "lot size", "frequency of test"]):
        return "SAMPLING"
    if any(k in combined for k in ["marking", "packaging", "labelling", "packing", "isi mark"]):
        return "MARKING"
    if any(k in combined for k in ["test method", "method of test", "chemical analysis", "mechanical test"]):
        return "TEST_METHOD"
    if any(k in combined for k in ["gazette", "order", "short title", "commencement", "punishable"]):
        return "STATUTORY"
    return "REQUIREMENT"


class DocumentExtractor:
    """Generic multi-format document parser extracting authentic hierarchical content."""

    def extract_document(self, raw_file_path: Path, metadata_path: Optional[Path] = None) -> ExtractedDocument:
        """
        Extracts structured document sections, clauses, and tables from raw file.
        Rejects invalid or unparseable files with is_success=False.
        """
        if not raw_file_path.exists():
            return ExtractedDocument(
                document_id=raw_file_path.parent.name,
                document_family_id=raw_file_path.parent.name.split("-")[0],
                title=raw_file_path.parent.name,
                document_type="UNKNOWN",
                is_success=False,
                error_reason=f"Raw file not found: {raw_file_path}"
            )

        meta = {}
        if metadata_path and metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        doc_info = meta.get("document", {})
        doc_id = doc_info.get("document_id", raw_file_path.parent.name)
        fam_id = doc_info.get("document_family_id", doc_id.split("-")[0])
        title = doc_info.get("title", doc_id)
        doc_type = doc_info.get("document_type", "INDIAN_STANDARD")

        suffix = raw_file_path.suffix.lower()

        try:
            if suffix == ".json":
                return self._extract_json(raw_file_path, doc_id, fam_id, title, doc_type, meta)
            elif suffix in {".html", ".htm"}:
                return self._extract_html(raw_file_path, doc_id, fam_id, title, doc_type, meta)
            elif suffix == ".pdf":
                return self._extract_pdf(raw_file_path, doc_id, fam_id, title, doc_type, meta)
            else:
                return ExtractedDocument(
                    document_id=doc_id,
                    document_family_id=fam_id,
                    title=title,
                    document_type=doc_type,
                    is_success=False,
                    error_reason=f"Unsupported file format: {suffix}"
                )
        except Exception as e:
            logger.error("Extraction error on %s: %s", raw_file_path, str(e), exc_info=True)
            return ExtractedDocument(
                document_id=doc_id,
                document_family_id=fam_id,
                title=title,
                document_type=doc_type,
                is_success=False,
                error_reason=f"Extraction failed: {str(e)}"
            )

    def _extract_pdf(self, path: Path, doc_id: str, fam_id: str, title: str, doc_type: str, meta: Dict[str, Any]) -> ExtractedDocument:
        """Extracts text, pages, clauses, and tables from PDF files using PyMuPDF."""
        pdf_doc = pymupdf.open(path)
        pages_count = len(pdf_doc)

        all_page_texts: List[Tuple[int, str]] = []
        total_raw_text = []

        for page_idx in range(pages_count):
            page = pdf_doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text()
            if text.strip():
                all_page_texts.append((page_num, text))
                total_raw_text.append(f"--- Page {page_num} ---\n{text}")

        if not all_page_texts:
            return ExtractedDocument(
                document_id=doc_id,
                document_family_id=fam_id,
                title=title,
                document_type=doc_type,
                is_success=False,
                error_reason="EXTRACTION_FAILED: Empty or scanned PDF with no extractable text layer",
                pages_count=pages_count
            )

        clauses: List[ExtractedClause] = []
        tables: List[ExtractedTable] = []
        table_counter = 0

        # Regex patterns for clause and section headers
        clause_pattern = re.compile(
            r"(?:^|\n)(?:(?:Clause|Section)\s+)?([0-9]+(?:\.[0-9]+)*)\s*[:\-–]?\s*([A-Z][A-Za-z0-9\s,\-\(\)/]+)\n([\s\S]*?)(?=(?:\n(?:(?:Clause|Section)\s+)?[0-9]+(?:\.[0-9]+)*\s*[:\-–]?\s*[A-Z])|\Z)",
            re.MULTILINE
        )

        table_pattern = re.compile(
            r"(?:^|\n)(Table\s+([0-9A-Za-z]+)\s*[:\-–]?\s*([^\n]+))\n([\s\S]*?)(?=(?:\nTable\s+[0-9A-Za-z]+)|\n[0-9]+(?:\.[0-9]+)*\s+[A-Z]|\Z)",
            re.IGNORECASE
        )

        for page_num, text in all_page_texts:
            # 1. Parse Tables from text layout
            for match in table_pattern.finditer(text):
                table_counter += 1
                t_label = match.group(1).strip()
                t_num = match.group(2).strip()
                t_title = match.group(3).strip()
                t_body = match.group(4).strip()

                # Parse rows & headers
                lines = [l.strip() for l in t_body.split("\n") if l.strip()]
                headers = []
                rows = []
                for idx, line in enumerate(lines):
                    # Delimiter detection: pipe, tab, or multi-space
                    if "|" in line:
                        cells = [c.strip() for c in line.split("|") if c.strip() and not c.strip().startswith("-")]
                    elif "\t" in line:
                        cells = [c.strip() for c in line.split("\t") if c.strip()]
                    else:
                        cells = [c.strip() for c in re.split(r"\s{2,}", line) if c.strip()]

                    if cells:
                        if idx == 0 or not headers:
                            headers = cells
                        else:
                            rows.append(cells)

                if headers or rows:
                    tables.append(
                        ExtractedTable(
                            table_id=f"TAB-{doc_id}-P{page_num}-T{t_num}",
                            table_number=f"Table {t_num}",
                            title=t_title,
                            headers=headers,
                            rows=rows,
                            page_number=page_num
                        )
                    )

            # 2. Parse Clauses
            clause_matches = list(clause_pattern.finditer(text))
            if clause_matches:
                for match in clause_matches:
                    cl_num = match.group(1).strip()
                    cl_head = match.group(2).strip()
                    cl_body = match.group(3).strip()

                    # Avoid capturing pure table text as a clause body
                    if len(cl_body) > 10:
                        ctype = classify_clause_type(cl_head, cl_body)
                        clauses.append(
                            ExtractedClause(
                                clause_number=cl_num,
                                heading=cl_head,
                                content_text=cl_body,
                                clause_type=ctype,
                                page_number=page_num
                            )
                        )
            else:
                # If no formal clause regex match, break page into paragraphs
                paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
                for idx, p in enumerate(paragraphs):
                    cl_num = f"{page_num}.{idx + 1}"
                    lines = p.split("\n")
                    first_line = lines[0]
                    body = "\n".join(lines[1:]) if len(lines) > 1 else p
                    ctype = classify_clause_type(first_line, body)
                    clauses.append(
                        ExtractedClause(
                            clause_number=cl_num,
                            heading=first_line[:80],
                            content_text=body if body else first_line,
                            clause_type=ctype,
                            page_number=page_num
                        )
                    )

        raw_str = "\n\n".join(total_raw_text)
        return ExtractedDocument(
            document_id=doc_id,
            document_family_id=fam_id,
            title=title,
            document_type=doc_type,
            is_success=True,
            pages_count=pages_count,
            clauses=clauses,
            tables=tables,
            raw_text=raw_str,
            metadata=meta
        )

    def _extract_html(self, path: Path, doc_id: str, fam_id: str, title: str, doc_type: str, meta: Dict[str, Any]) -> ExtractedDocument:
        """Extracts hierarchical sections and tables from HTML documents."""
        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()

        parser = BISHTMLDOMParser()
        parser.feed(html_content)
        parser.finalize()

        clauses: List[ExtractedClause] = []
        for idx, sec in enumerate(parser.sections):
            heading = sec["heading"]
            text = sec["text"]
            if len(text) > 10 or heading:
                cl_num = f"SEC-{idx + 1}"
                ctype = classify_clause_type(heading, text)
                clauses.append(
                    ExtractedClause(
                        clause_number=cl_num,
                        heading=heading,
                        content_text=text if text else heading,
                        clause_type=ctype,
                        page_number=1
                    )
                )

        if not clauses:
            # Clean text fallback
            clean_text = re.sub(r"<[^>]+>", " ", html_content)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            if len(clean_text) > 20:
                clauses.append(
                    ExtractedClause(
                        clause_number="1.0",
                        heading=title,
                        content_text=clean_text,
                        clause_type="STATUTORY",
                        page_number=1
                    )
                )

        return ExtractedDocument(
            document_id=doc_id,
            document_family_id=fam_id,
            title=title,
            document_type=doc_type,
            is_success=len(clauses) > 0,
            pages_count=1,
            clauses=clauses,
            tables=parser.tables,
            raw_text=html_content,
            metadata=meta
        )

    def _extract_json(self, path: Path, doc_id: str, fam_id: str, title: str, doc_type: str, meta: Dict[str, Any]) -> ExtractedDocument:
        """Schema-aware recursive parser for database registry JSON records."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        clauses: List[ExtractedClause] = []
        tables: List[ExtractedTable] = []

        if isinstance(data, dict):
            # Parse record properties into structured clauses
            for key, val in data.items():
                if isinstance(val, (dict, list)):
                    val_str = json.dumps(val, indent=2)
                else:
                    val_str = str(val)

                clauses.append(
                    ExtractedClause(
                        clause_number=key,
                        heading=key.replace("_", " ").title(),
                        content_text=val_str,
                        clause_type="STATUTORY",
                        page_number=1
                    )
                )

        elif isinstance(data, list):
            # Parse list of records as a structured table
            headers = []
            rows = []
            if data and isinstance(data[0], dict):
                headers = list(data[0].keys())
                for item in data:
                    rows.append([str(item.get(h, "")) for h in headers])

                tables.append(
                    ExtractedTable(
                        table_id=f"TAB-{doc_id}-REGISTRY",
                        table_number="Registry Table 1",
                        title=f"{title} Directory Records",
                        headers=headers,
                        rows=rows,
                        page_number=1
                    )
                )

            for idx, item in enumerate(data):
                clauses.append(
                    ExtractedClause(
                        clause_number=f"REC-{idx + 1}",
                        heading=f"Record {idx + 1}",
                        content_text=json.dumps(item, indent=2),
                        clause_type="STATUTORY",
                        page_number=1
                    )
                )

        return ExtractedDocument(
            document_id=doc_id,
            document_family_id=fam_id,
            title=title,
            document_type=doc_type,
            is_success=len(clauses) > 0 or len(tables) > 0,
            pages_count=1,
            clauses=clauses,
            tables=tables,
            raw_text=json.dumps(data, indent=2),
            metadata=meta
        )
