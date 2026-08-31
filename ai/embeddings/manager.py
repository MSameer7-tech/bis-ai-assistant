"""
Dataset-Driven Exact Inverted Index for Phase 2E.

Builds exact retrieval indexes directly from the Chroma SQLite store.

Indexes:
    - technical identifiers / cap codes
    - BIS standard numbers
    - material / cement grades
    - canonical parameters
"""

import logging
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ExactInvertedIndex:
    """Inverted index mapping exact technical tokens to chunk IDs."""

    def __init__(self, chunks_dir: Optional[Path] = None):
        self.chunks_dir = chunks_dir or (
            Path(__file__).resolve().parents[2]
            / "data"
            / "chunks"
        )

        self.chroma_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "vector_store"
            / "chroma"
            / "chroma.sqlite3"
        )

        self.identifier_to_chunks: Dict[str, Set[str]] = {}
        self.parameter_to_chunks: Dict[str, Set[str]] = {}
        self.grade_to_chunks: Dict[str, Set[str]] = {}
        self.standard_to_chunks: Dict[str, Set[str]] = {}

        self._build_index()

    @staticmethod
    def _normalize_key(token: str) -> str:
        return (
            str(token)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

    def _add(
        self,
        index: Dict[str, Set[str]],
        key: str,
        chunk_id: str,
    ) -> None:
        if not key or not chunk_id:
            return

        normalized = self._normalize_key(key)

        if normalized:
            index.setdefault(normalized, set()).add(chunk_id)

    @staticmethod
    def _metadata_value(
        string_value,
        int_value,
        float_value,
        bool_value,
    ):
        if string_value is not None:
            return string_value

        if int_value is not None:
            return int_value

        if float_value is not None:
            return float_value

        return bool_value

    def _load_chroma_chunks(self) -> List[Dict]:
        """Load chunk IDs and metadata directly from Chroma SQLite."""
        if not self.chroma_path.exists():
            logger.warning("Chroma database does not exist: %s", self.chroma_path)
            return []

        conn = sqlite3.connect(f"file:{self.chroma_path}?mode=ro", uri=True)
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, embedding_id
                FROM embeddings
                WHERE embedding_id IS NOT NULL
                ORDER BY id
            """)
            embeddings = cur.fetchall()
            logger.info("Found %d Chroma embeddings", len(embeddings))

            chunks = []
            for embedding_db_id, chunk_id in embeddings:
                cur.execute("""
                    SELECT key, string_value, int_value, float_value, bool_value
                    FROM embedding_metadata
                    WHERE id = ?
                """, (embedding_db_id,))

                metadata = {}
                for key, string_value, int_value, float_value, bool_value in cur.fetchall():
                    if string_value is not None:
                        value = string_value
                    elif int_value is not None:
                        value = int_value
                    elif float_value is not None:
                        value = float_value
                    else:
                        value = bool_value
                    metadata[key] = value

                chunks.append({"chunk_id": chunk_id, "metadata": metadata})

            logger.info("Loaded %d Chroma chunks for exact index", len(chunks))
            return chunks
        finally:
            conn.close()

    def _build_index(self) -> None:
        """Build exact indexes from Chroma metadata."""

        chunks = self._load_chroma_chunks()

        if not chunks:
            logger.warning(
                "No Chroma chunks available; exact index is empty"
            )
            return

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
                "hydraulic",
            ],
            "mass": [
                "mass",
            ],
            "ph": [
                "ph",
            ],
        }

        for chunk in chunks:

            chunk_id = chunk.get("chunk_id")

            if not chunk_id:
                continue

            metadata = chunk.get("metadata") or {}

            text = metadata.get(
                "chroma:document",
                "",
            )

            if not isinstance(text, str):
                text = str(text or "")

            text_lower = text.lower()

            # --------------------------------------------------
            # Standard
            # --------------------------------------------------

            standard_number = metadata.get(
                "standard_number",
                "",
            )

            if standard_number:

                standard_number = str(standard_number)

                self._add(
                    self.standard_to_chunks,
                    standard_number,
                    chunk_id,
                )

                match = re.search(
                    r"\bIS\s*(\d+)",
                    standard_number,
                    re.IGNORECASE,
                )

                if match:

                    number = match.group(1)

                    self._add(
                        self.standard_to_chunks,
                        f"IS{number}",
                        chunk_id,
                    )

                    self._add(
                        self.standard_to_chunks,
                        number,
                        chunk_id,
                    )

            # --------------------------------------------------
            # Cap / technical identifiers
            # --------------------------------------------------

            cap_matches = re.findall(
                r"\b("
                r"B22d|B15d|GX53|E17|E27|E14|E26|E40|"
                r"G9|G4|GU10|R7s"
                r")\b",
                text,
                re.IGNORECASE,
            )

            for cap in cap_matches:
                self._add(
                    self.identifier_to_chunks,
                    cap,
                    chunk_id,
                )

            # --------------------------------------------------
            # Grades
            # --------------------------------------------------

            grade_matches = re.findall(
                r"\b("
                r"Fe\s*550D|Fe\s*550|"
                r"Fe\s*500D|Fe\s*500|"
                r"Fe\s*415D|Fe\s*415|"
                r"Fe\s*600|"
                r"53\s*Grade|43\s*Grade|33\s*Grade|"
                r"OPC\s*53|OPC\s*43|OPC\s*33"
                r")\b",
                text,
                re.IGNORECASE,
            )

            for grade in grade_matches:
                self._add(
                    self.grade_to_chunks,
                    grade,
                    chunk_id,
                )

            # --------------------------------------------------
            # Parameters
            # --------------------------------------------------

            for parameter, patterns in parameter_patterns.items():

                if any(
                    pattern.lower() in text_lower
                    for pattern in patterns
                ):
                    self._add(
                        self.parameter_to_chunks,
                        parameter,
                        chunk_id,
                    )

            # --------------------------------------------------
            # Structured requirements
            # --------------------------------------------------

            structured = metadata.get(
                "structured_data",
                {},
            )

            if isinstance(structured, dict):

                requirements = structured.get(
                    "requirements",
                    [],
                )

                if isinstance(requirements, list):

                    for requirement in requirements:

                        if not isinstance(requirement, dict):
                            continue

                        parameter = requirement.get(
                            "parameter"
                        )

                        if parameter:
                            self._add(
                                self.parameter_to_chunks,
                                str(parameter),
                                chunk_id,
                            )

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
        exact_identifiers: Optional[List[str]] = None,
        parameter: Optional[str] = None,
        grade: Optional[str] = None,
        standard_code: Optional[str] = None,
    ) -> Set[str]:
        """Return chunk IDs matching exact search keys."""

        matches: Set[str] = set()

        if exact_identifiers:

            for identifier in exact_identifiers:

                normalized = self._normalize_key(
                    identifier
                )

                matches.update(
                    self.identifier_to_chunks.get(
                        normalized,
                        set(),
                    )
                )

                matches.update(
                    self.grade_to_chunks.get(
                        normalized,
                        set(),
                    )
                )

        if parameter:

            normalized_parameter = str(
                parameter
            ).strip().lower()

            matches.update(
                self.parameter_to_chunks.get(
                    normalized_parameter,
                    set(),
                )
            )

        if grade:

            normalized_grade = self._normalize_key(
                grade
            )

            matches.update(
                self.grade_to_chunks.get(
                    normalized_grade,
                    set(),
                )
            )

        if standard_code:

            normalized_standard = self._normalize_key(
                standard_code
            )

            matches.update(
                self.standard_to_chunks.get(
                    normalized_standard,
                    set(),
                )
            )

            match = re.search(
                r"\bIS\s*(\d+)",
                str(standard_code),
                re.IGNORECASE,
            )

            if match:

                matches.update(
                    self.standard_to_chunks.get(
                        f"is{match.group(1)}",
                        set(),
                    )
                )

        return matches
