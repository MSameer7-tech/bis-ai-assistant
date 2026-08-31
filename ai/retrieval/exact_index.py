"""
Dataset-backed Exact Inverted Index for BIS Standards.

Builds exact-match indexes directly from the Chroma vector store,
using the same 503 indexed chunks used by hybrid retrieval.

Indexes:
- technical identifiers
- standard numbers
- material / steel / cement grades
- canonical parameters
"""

import logging
import re
import sqlite3
from pathlib import Path
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class ExactInvertedIndex:
    """
    Exact inverted index built from the local Chroma SQLite database.

    Chroma mapping:

        embeddings.id
              │
              └── embedding_metadata.id
                       │
                       ├── standard_number
                       ├── document_id
                       ├── source_id
                       ├── clause_number
                       └── chroma:document

    embedding_id is the external chunk ID, e.g.:

        DOC-001-v028::3.1::DEF-001
    """

    def __init__(
        self,
        chroma_path: Optional[str] = None,
    ):
        self.chroma_path = Path(
            chroma_path
            or "data/vector_store/chroma/chroma.sqlite3"
        )

        self.identifier_to_chunks: Dict[str, Set[str]] = {}
        self.standard_to_chunks: Dict[str, Set[str]] = {}
        self.grade_to_chunks: Dict[str, Set[str]] = {}
        self.parameter_to_chunks: Dict[str, Set[str]] = {}

        self._build_index()

    @staticmethod
    def _add(
        index: Dict[str, Set[str]],
        key: str,
        chunk_id: str,
    ) -> None:
        if not key or not chunk_id:
            return

        key = str(key).strip().lower()

        if not key:
            return

        index.setdefault(key, set()).add(chunk_id)

    @staticmethod
    def _normalize_standard(value: str) -> Set[str]:
        """
        Generate several lookup forms for:

            IS 16102 (Part 1) : 2012

        including:

            is 16102 (part 1) : 2012
            is16102
            16102
        """

        value = str(value).strip()

        if not value:
            return set()

        result = {
            value.lower(),
        }

        match = re.search(
            r"\bIS\s*(\d+)",
            value,
            re.IGNORECASE,
        )

        if match:
            number = match.group(1)

            result.add(f"is {number}".lower())
            result.add(f"is{number}".lower())
            result.add(number.lower())

        return result

    def _build_index(self) -> None:

        logger.info(
            "Building ExactInvertedIndex from Chroma: %s",
            self.chroma_path,
        )

        if not self.chroma_path.exists():
            logger.error(
                "Chroma database not found: %s",
                self.chroma_path,
            )
            return

        try:
            conn = sqlite3.connect(
                f"file:{self.chroma_path}?mode=ro",
                uri=True,
            )

            cur = conn.cursor()

            # --------------------------------------------------
            # Verify Chroma data
            # --------------------------------------------------

            cur.execute(
                "SELECT COUNT(*) FROM embeddings"
            )

            embedding_count = cur.fetchone()[0]

            logger.info(
                "Chroma embeddings available: %d",
                embedding_count,
            )

            # --------------------------------------------------
            # Load embeddings
            #
            # embeddings.id:
            #     internal integer ID
            #
            # embeddings.embedding_id:
            #     external chunk ID
            # --------------------------------------------------

            cur.execute(
                """
                SELECT id, embedding_id
                FROM embeddings
                WHERE embedding_id IS NOT NULL
                ORDER BY id
                """
            )

            embeddings = cur.fetchall()

            logger.info(
                "Loading %d Chroma chunk IDs",
                len(embeddings),
            )

            for embedding_pk, chunk_id in embeddings:

                # --------------------------------------------------
                # Load metadata for this embedding
                # --------------------------------------------------

                cur.execute(
                    """
                    SELECT
                        key,
                        string_value,
                        int_value,
                        float_value,
                        bool_value
                    FROM embedding_metadata
                    WHERE id = ?
                    """,
                    (embedding_pk,),
                )

                rows = cur.fetchall()

                metadata = {}

                for (
                    key,
                    string_value,
                    int_value,
                    float_value,
                    bool_value,
                ) in rows:

                    if string_value is not None:
                        value = string_value

                    elif int_value is not None:
                        value = int_value

                    elif float_value is not None:
                        value = float_value

                    else:
                        value = bool_value

                    metadata[key] = value

                # --------------------------------------------------
                # Standard number
                # --------------------------------------------------

                standard_number = metadata.get(
                    "standard_number"
                )

                if standard_number:

                    for standard_key in self._normalize_standard(
                        standard_number
                    ):
                        self._add(
                            self.standard_to_chunks,
                            standard_key,
                            chunk_id,
                        )

                # --------------------------------------------------
                # Full document text
                # --------------------------------------------------

                text = metadata.get(
                    "chroma:document",
                    "",
                )

                if not isinstance(text, str):
                    text = str(text or "")

                text_lower = text.lower()

                # --------------------------------------------------
                # Technical identifiers
                # --------------------------------------------------

                identifier_patterns = [
                    r"\bB22d\b",
                    r"\bB15d\b",
                    r"\bGX53\b",
                    r"\bE14\b",
                    r"\bE17\b",
                    r"\bE26\b",
                    r"\bE27\b",
                    r"\bE40\b",
                    r"\bG4\b",
                    r"\bG9\b",
                    r"\bGU10\b",
                    r"\bR7s\b",
                ]

                for pattern in identifier_patterns:

                    for match in re.findall(
                        pattern,
                        text,
                        re.IGNORECASE,
                    ):
                        self._add(
                            self.identifier_to_chunks,
                            match,
                            chunk_id,
                        )

                # --------------------------------------------------
                # Material / product grades
                # --------------------------------------------------

                grade_patterns = [
                    r"\bFe\s*415D\b",
                    r"\bFe\s*415\b",
                    r"\bFe\s*500D\b",
                    r"\bFe\s*500\b",
                    r"\bFe\s*550D\b",
                    r"\bFe\s*550\b",
                    r"\bFe\s*600\b",
                    r"\bOPC\s*33\b",
                    r"\bOPC\s*43\b",
                    r"\bOPC\s*53\b",
                ]

                for pattern in grade_patterns:

                    for match in re.findall(
                        pattern,
                        text,
                        re.IGNORECASE,
                    ):
                        self._add(
                            self.grade_to_chunks,
                            match,
                            chunk_id,
                        )

                # --------------------------------------------------
                # Canonical parameters
                # --------------------------------------------------

                parameter_patterns = {
                    "insulation_resistance": [
                        "insulation resistance",
                    ],

                    "yield_stress": [
                        "yield stress",
                        "proof stress",
                        "0.2 percent proof stress",
                        "0.2% proof stress",
                    ],

                    "percentage_elongation": [
                        "percentage elongation",
                        "elongation",
                    ],

                    "torque_moment": [
                        "torque",
                        "torsion moment",
                    ],

                    "compressive_strength": [
                        "compressive strength",
                    ],

                    "air_delivery": [
                        "air delivery",
                    ],

                    "proof_pressure": [
                        "proof pressure",
                        "hydraulic pressure",
                    ],

                    "mass": [
                        "mass",
                    ],

                    "ph": [
                        "ph",
                    ],
                }

                for parameter, patterns in parameter_patterns.items():

                    if any(
                        pattern in text_lower
                        for pattern in patterns
                    ):
                        self._add(
                            self.parameter_to_chunks,
                            parameter,
                            chunk_id,
                        )

            conn.close()

        except Exception:
            logger.exception(
                "Failed to build ExactInvertedIndex"
            )
            return

        logger.info(
            "ExactInvertedIndex built: "
            "%d identifiers, "
            "%d standards, "
            "%d grades, "
            "%d parameter keys",
            len(self.identifier_to_chunks),
            len(self.standard_to_chunks),
            len(self.grade_to_chunks),
            len(self.parameter_to_chunks),
        )

    def get_matching_chunks(
        self,
        exact_identifiers=None,
        grade=None,
        standard_code=None,
        parameter=None,
    ) -> Set[str]:

        matches: Set[str] = set()

        if exact_identifiers:

            for identifier in exact_identifiers:

                matches.update(
                    self.identifier_to_chunks.get(
                        str(identifier).lower(),
                        set(),
                    )
                )

        if grade:

            matches.update(
                self.grade_to_chunks.get(
                    str(grade).lower(),
                    set(),
                )
            )

        if standard_code:

            for key in self._normalize_standard(
                standard_code
            ):
                matches.update(
                    self.standard_to_chunks.get(
                        key,
                        set(),
                    )
                )

        if parameter:

            matches.update(
                self.parameter_to_chunks.get(
                    str(parameter).lower(),
                    set(),
                )
            )

        return matches
