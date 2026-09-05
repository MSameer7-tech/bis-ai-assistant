import json
from enum import Enum
from typing import Dict, Any, Optional

class RetrievalSourceType(str, Enum):
    DOCUMENT_EVIDENCE = "DOCUMENT_EVIDENCE"
    STANDARD_METADATA = "STANDARD_METADATA"
    PRODUCT_STANDARD_RELATIONSHIP = "PRODUCT_STANDARD_RELATIONSHIP"

class RetrievalResult:
    """Normalized retrieval result contract."""
    def __init__(
        self,
        source_type: RetrievalSourceType,
        record_id: str,
        score: float,
        standard_number: str,
        title: str,
        text: str,
        metadata: Dict[str, Any],
        provenance: Dict[str, Any]
    ):
        self.source_type = source_type
        self.record_id = record_id
        self.score = score
        self.standard_number = standard_number
        self.title = title
        self.text = text
        self.metadata = metadata
        self.provenance = provenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value if isinstance(self.source_type, Enum) else self.source_type,
            "record_id": self.record_id,
            "score": self.score,
            "standard_number": self.standard_number,
            "title": self.title,
            "text": self.text,
            "metadata": self.metadata,
            "provenance": self.provenance
        }
