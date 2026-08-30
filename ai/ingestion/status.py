"""
Document Lifecycle Status Enum for BIS AI Assistant Ingestion Pipeline (Step 9).
"""

from enum import Enum


class DocumentStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    DOWNLOADED = "DOWNLOADED"
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    NORMALIZED = "NORMALIZED"
    CHUNKED = "CHUNKED"
    EMBEDDED = "EMBEDDED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"
