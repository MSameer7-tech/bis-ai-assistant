"""
Dataset-Driven Exact Inverted Index for Phase 2E.

Extracts exact identifiers, standard codes, grades, cap codes,
and parameter keys directly from Chroma chunk metadata.
"""

import re
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


class ExactInvertedIndex:
    """Inverted index mapping exact technical tokens to matching chunk IDs."""

    def __init__(self, chunks_dir: Optional[Path] = None):
        self.chunks_dir = chunks_dir or (
            Path(__file__).resolve().parents[2]
            / "data"
            / "chunks"
        )

        self.chroma_path = (
            self.chunks_dir.parent
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

    def _normalize_key(self, token: str) -> str:
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

        index.setdefault(
            self._normalize_key(key),
            set(),
        ).add(chunk_id)

    # ============================================================
    # Chroma metadata
    # ============================================================

    def _load_chroma_chunks(self):
        """
        Read chunk IDs and metadata directly from Chroma SQLite.

        Chroma structure:

            embeddings.id
                ↓
            embedding_metadata.id

        embeddings.embedding_id is the external chunk ID.
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

            chunks = []

            for embedding_id, chunk_id in embeddings:

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
                    (embedding_id,),
                )

                metadata_rows = cur.fetchall()

                metadata = {}

                for (
                    key,
                    string_value,
                    int_value,
                    float_value,
                    bool_value,
                ) in metadata_rows:

                    if string_value is not None:
                        value = string_value
                    elif int_value is not None:
                        value = int_value
                    elif float_value is not None:
                        value = float_value
                    else:
                        value = bool_value

                    metadata[key] = value

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "metadata": metadata,
                    }
                )

            return chunks

        finally:
            conn.close()

    # ============================================================
    # Build index
    # ============================================================

    def _build_index(self):
        """Build inverted posting lists from Chroma."""

        chunks = self._load_chroma_chunks()

        if not chunks:
            logger.warning(
                "No Chroma chunks available for ExactInvertedIndex"
            )
            return

        for item in chunks:

            chunk_id = item["chunk_id"]
            metadata = item["metadata"]

            # ----------------------------------------------------
            # Text
            # ----------------------------------------------------

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

            std_num = metadata.get(
                "standard_number",
                "",
            )

            if std_num:

                clean_std = self._normalize_key(
                    std_num
                )

                self.standard_to_chunks.setdefault(
                    clean_std,
                    set(),
                ).add(chunk_id)

                # Main standard number
                #
                # IS 16102 (Part 1) : 2012
                #             ↓
                # IS16102
                #

                match = re.search(
                    r"\bIS\s*(\d+)",
                    str(std_num),
                    re.IGNORECASE,
                )

                if match:

                    self.standard_to_chunks.setdefault(
                        f"is{match.group(1)}",
                        set(),
                    ).add(chunk_id)

                    self.standard_to_chunks.setdefault(
                        match.group(1),
                        set(),
                    ).add(chunk_id)

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

            grades = re.findall(
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

            for grade in grades:

                self._add(
                    self.grade_to_chunks,
                    grade,
                    chunk_id,
                )

            # ----------------------------------------------------
            # Canonical parameters
            # ----------------------------------------------------

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
                    self.parameter_to_chunks.setdefault(
                        parameter,
                        set(),
                    ).add(chunk_id)

            # ----------------------------------------------------
            # Structured requirements, if present
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

                    for req in requirements:

                        if not isinstance(req, dict):
                            continue

                        parameter = req.get(
                            "parameter"
                        )

                        if parameter:

                            self.parameter_to_chunks.setdefault(
                                str(parameter).strip().lower(),
                                set(),
                            ).add(chunk_id)

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
        """Return candidate chunk IDs matching exact search keys."""

        matches: Set[str] = set()

        if exact_identifiers:

            for ident in exact_identifiers:

                norm_ident = self._normalize_key(
                    ident
                )

                matches.update(
                    self.identifier_to_chunks.get(
                        norm_ident,
                        set(),
                    )
                )

                matches.update(
                    self.grade_to_chunks.get(
                        norm_ident,
                        set(),
                    )
                )

        if parameter:

            matches.update(
                self.parameter_to_chunks.get(
                    parameter.strip().lower(),
                    set(),
                )
            )

        if grade:

            norm_grade = self._normalize_key(
                grade
            )

            matches.update(
                self.grade_to_chunks.get(
                    norm_grade,
                    set(),
                )
            )

        if standard_code:

            norm_std = self._normalize_key(
                standard_code
            )

            matches.update(
                self.standard_to_chunks.get(
                    norm_std,
                    set(),
                )
            )

            # Also support a query such as:
            #
            # IS 16102 (Part 1)
            #
            # → is16102

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
