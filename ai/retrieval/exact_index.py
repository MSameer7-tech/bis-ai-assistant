"""
Dataset-Driven Exact Inverted Index for Phase 2E.

Builds exact retrieval indexes directly from the Chroma SQLite store.

Indexes:
    - technical identifiers / cap codes
    - BIS standard numbers
    - material / cement grades
    - canonical parameters

The Chroma embedding_id is used as the external chunk ID.
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
        # Retained for backwards compatibility with callers that pass
        # chunks_dir, although the authoritative source is now Chroma.
        self.chunks_dir = chunks_dir or (
            Path(__file__).resolve().parents[2]
            / "data"
            / "chunks"
        )

        # Repository root:
        # ai/retrieval/exact_index.py
        #       ↑
        # parents[2] == repository root
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

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _normalize_key(token: str) -> str:
        """
        Normalize exact-index keys.

        Examples:
            "IS 16102" -> "is16102"
            "Fe 500"   -> "fe500"
            "B22d"     -> "b22d"
        """
        return (
            str(token)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

    @staticmethod
    def _metadata_value(
        string_value,
        int_value,
        float_value,
        bool_value,
    ):
        """Return the populated Chroma metadata value."""
        if string_value is not None:
            return string_value

        if int_value is not None:
            return int_value

        if float_value is not None:
            return float_value

        return bool_value

    def _add(
        self,
        index: Dict[str, Set[str]],
        key: str,
        chunk_id: str,
    ) -> None:
        """Add a normalized key to a posting list."""
        if not key or not chunk_id:
            return

        normalized = self._normalize_key(key)

        if normalized:
            index.setdefault(normalized, set()).add(chunk_id)

    # ============================================================
    # Chroma loading
    # ============================================================

    def _load_chroma_chunks(self) -> List[Dict]:
        """
        Load all Chroma embeddings and their metadata.

        Chroma stores:

            embeddings.id
                |
                +---- embedding_metadata.id

        The value in embeddings.embedding_id is the external
        chunk ID, e.g.:

            DOC-001-v028::3.1::DEF-001
        """

        if not self.chroma_path.exists():
            logger.warning(
                "Chroma database does not exist: %s",
                self.chroma_path,
            )
            return []

        logger.info(
            "Loading exact-index data from Chroma: %s",
            self.chroma_path,
        )

        conn = sqlite3.connect(
            f"file:{self.chroma_path}?mode=ro",
            uri=True,
        )

        try:
            cur = conn.cursor()

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
                "Found %d Chroma embeddings",
                len(embeddings),
            )

            chunks: List[Dict] = []

            for embedding_db_id, chunk_id in embeddings:

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
                    (embedding_db_id,),
                )

                metadata_rows = cur.fetchall()

                metadata: Dict = {}

                for (
                    key,
                    string_value,
                    int_value,
                    float_value,
                    bool_value,
                ) in metadata_rows:

                    if not key:
                        continue

                    metadata[key] = self._metadata_value(
                        string_value,
                        int_value,
                        float_value,
                        bool_value,
                    )

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "metadata": metadata,
                    }
                )

            logger.info(
                "Loaded %d unique Chroma chunks",
                len(chunks),
            )

            return chunks

        finally:
            conn.close()

    # ============================================================
    # Build index
    # ============================================================

    def _build_index(self) -> None:
        """Build all exact indexes from Chroma metadata."""

        chunks = self._load_chroma_chunks()

        if not chunks:
            logger.warning(
                "No Chroma chunks available; exact index will be empty"
            )
            return

        # --------------------------------------------------------
        # Canonical parameter patterns
        # --------------------------------------------------------

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
                "pH",
            ],
        }

        # --------------------------------------------------------
        # Process every Chroma chunk
        # --------------------------------------------------------

        for chunk in chunks:

            chunk_id = chunk.get("chunk_id")

            if not chunk_id:
                continue

            metadata = chunk.get("metadata") or {}

            # Chroma stores actual chunk text under chroma:document.
            text = metadata.get(
                "chroma:document",
                "",
            )

            if not isinstance(text, str):
                text = str(text or "")

            text_lower = text.lower()

            # ----------------------------------------------------
            # Standard number
            # ----------------------------------------------------

            standard_number = metadata.get(
                "standard_number",
                "",
            )

            if standard_number:

                standard_number = str(standard_number)

                # Full normalized standard.
                #
                # IS 16102 (Part 1) : 2012
                # ->
                # is16102(part1):2012
                #
                self._add(
                    self.standard_to_chunks,
                    standard_number,
                    chunk_id,
                )

                # Main BIS number.
                #
                # IS 16102 (Part 1) : 2012
                # ->
                # is16102
                #

                match = re.search(
                    r"\bIS\s*(\d+)",
                    standard_number,
                    re.IGNORECASE,
                )

                if match:

                    standard_number_only = match.group(1)

                    self._add(
                        self.standard_to_chunks,
                        f"IS{standard_number_only}",
                        chunk_id,
                    )

                    # Also allow raw numeric lookup.
                    self._add(
                        self.standard_to_chunks,
                        standard_number_only,
                        chunk_id,
                    )

            # ----------------------------------------------------
            # Cap codes / technical identifiers
            # ----------------------------------------------------

            cap_matches = re.findall(
                r"\b("
                r"B22d|"
                r"B15d|"
                r"GX53|"
                r"E17|"
                r"E27|"
                r"E14|"
                r"E26|"
                r"E40|"
                r"G9|"
                r"G4|"
                r"GU10|"
                r"R7s"
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

            # ----------------------------------------------------
            # Material / steel / cement grades
            # ----------------------------------------------------

            grade_matches = re.findall(
                r"\b("
                r"Fe\s*550D|"
                r"Fe\s*550|"
                r"Fe\s*500D|"
                r"Fe\s*500|"
                r"Fe\s*415D|"
                r"Fe\s*415|"
                r"Fe\s*600|"
                r"53\s*Grade|"
                r"43\s*Grade|"
                r"33\s*Grade|"
                r"OPC\s*53|"
                r"OPC\s*43|"
                r"OPC\s*33"
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

            # ----------------------------------------------------
            # Canonical parameters
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # Structured requirements
            # ----------------------------------------------------

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

    # ============================================================
    # Query
    # ============================================================

    def get_matching_chunks(
        self,
        exact_identifiers: Optional[List[str]] = None,
        parameter: Optional[str] = None,
        grade: Optional[str] = None,
        standard_code: Optional[str] = None,
    ) -> Set[str]:
        """
        Return chunk IDs matching exact search keys.
        """

        matches: Set[str] = set()

        # --------------------------------------------------------
        # Exact identifiers
        # --------------------------------------------------------

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

                # Grades are also valid exact technical tokens.
                matches.update(
                    self.grade_to_chunks.get(
                        normalized,
                        set(),
                    )
                )

        # --------------------------------------------------------
        # Canonical parameter
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Grade
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Standard
        # --------------------------------------------------------

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

            # Support:
            #
            # IS 16102
            # IS 16102 (Part 1)
            # IS 16102 (Part 1) : 2012
            #

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
