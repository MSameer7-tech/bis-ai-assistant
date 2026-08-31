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
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


class ExactInvertedIndex:
    """Inverted index mapping exact technical tokens to chunk IDs."""

    def __init__(self, chroma_path: Optional[Path] = None):
        self.chroma_path = chroma_path or (
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

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Index helper
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Chroma loading
    # ---------------------------------------------------------

    def _build_index(self) -> None:
        """Build exact indexes directly from Chroma SQLite."""

        if not self.chroma_path.exists():
            logger.warning(
                "Chroma database does not exist: %s",
                self.chroma_path,
            )
            return

        try:
            conn = sqlite3.connect(
                f"file:{self.chroma_path}?mode=ro",
                uri=True,
            )
        except Exception as exc:
            logger.exception(
                "Unable to open Chroma database: %s",
                exc,
            )
            return

        try:
            cur = conn.cursor()

            # -------------------------------------------------
            # Locate the collection
            # -------------------------------------------------

            cur.execute(
                """
                SELECT id
                FROM collections
                WHERE name = ?
                LIMIT 1
                """,
                ("bis_standards_knowledge",),
            )

            collection_row = cur.fetchone()

            if not collection_row:
                logger.warning(
                    "Chroma collection 'bis_standards_knowledge' not found"
                )
                return

            collection_id = collection_row[0]

            # -------------------------------------------------
            # Get embeddings belonging to collection
            # -------------------------------------------------

            cur.execute(
                """
                SELECT
                    e.id,
                    e.embedding_id
                FROM embeddings e
                JOIN segments s
                    ON s.id = e.segment_id
                WHERE s.collection = ?
                ORDER BY e.id
                """,
                (collection_id,),
            )

            embeddings = cur.fetchall()

            logger.info(
                "Loading %d Chroma embeddings for exact index",
                len(embeddings),
            )

            for embedding_pk, chunk_id in embeddings:

                if not chunk_id:
                    continue

                # ---------------------------------------------
                # Metadata
                # ---------------------------------------------

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

                text = metadata.get(
                    "chroma:document",
                    "",
                )

                if not isinstance(text, str):
                    text = str(text or "")

                text_lower = text.lower()

                standard_number = metadata.get(
                    "standard_number",
                    "",
                )

                clause_number = str(
                    metadata.get(
                        "clause_number",
                        "",
                    )
                    or ""
                )

                # =============================================
                # 1. Standard number
                # =============================================

                if standard_number:

                    self._add(
                        self.standard_to_chunks,
                        standard_number,
                        chunk_id,
                    )

                    match = re.search(
                        r"\bIS\s*(\d+)",
                        str(standard_number),
                        re.IGNORECASE,
                    )

                    if match:
                        self._add(
                            self.standard_to_chunks,
                            f"IS {match.group(1)}",
                            chunk_id,
                        )

                # =============================================
                # 2. Technical identifiers
                # =============================================

                cap_matches = re.findall(
                    r"\b("
                    r"B22d|B15d|GX53|E17|E27|E14|E26|"
                    r"E40|G9|G4|GU10|R7s"
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

                # =============================================
                # 3. Grades
                # =============================================

                grades = re.findall(
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

                for grade in grades:
                    self._add(
                        self.grade_to_chunks,
                        grade,
                        chunk_id,
                    )

                # =============================================
                # 4. Structured parameters
                # =============================================

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
                                "parameter",
                                "",
                            )

                            if parameter:
                                self._add(
                                    self.parameter_to_chunks,
                                    parameter,
                                    chunk_id,
                                )

                # =============================================
                # 5. Keyword parameter detection
                # =============================================

                if (
                    "insulation resistance"
                    in text_lower
                    or clause_number.startswith("8")
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "insulation_resistance",
                        chunk_id,
                    )

                if (
                    "yield stress" in text_lower
                    or "0.2 percent proof stress" in text_lower
                    or "0.2% proof stress" in text_lower
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "yield_stress",
                        chunk_id,
                    )

                if (
                    "elongation" in text_lower
                    or "percentage elongation" in text_lower
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "percentage_elongation",
                        chunk_id,
                    )

                if (
                    "torque" in text_lower
                    or "torsion moment" in text_lower
                    or clause_number.startswith("9")
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "torque_moment",
                        chunk_id,
                    )

                if "compressive strength" in text_lower:
                    self._add(
                        self.parameter_to_chunks,
                        "compressive_strength",
                        chunk_id,
                    )

                if "air delivery" in text_lower:
                    self._add(
                        self.parameter_to_chunks,
                        "air_delivery",
                        chunk_id,
                    )

                if (
                    "proof pressure" in text_lower
                    or "hydraulic" in text_lower
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "proof_pressure",
                        chunk_id,
                    )

                if (
                    "mass" in text_lower
                    and (
                        "helmet" in text_lower
                        or "1500" in text_lower
                    )
                ):
                    self._add(
                        self.parameter_to_chunks,
                        "mass",
                        chunk_id,
                    )

                if "ph" in text_lower:
                    self._add(
                        self.parameter_to_chunks,
                        "ph",
                        chunk_id,
                    )

        finally:
            conn.close()

        logger.info(
            "ExactInvertedIndex built: "
            "%d identifiers, %d standards, %d grades, "
            "%d parameter keys",
            len(self.identifier_to_chunks),
            len(self.standard_to_chunks),
            len(self.grade_to_chunks),
            len(self.parameter_to_chunks),
        )

    # ---------------------------------------------------------
    # Query
    # ---------------------------------------------------------

    def get_matching_chunks(
        self,
        exact_identifiers: Optional[List[str]] = None,
        parameter: Optional[str] = None,
        grade: Optional[str] = None,
        standard_code: Optional[str] = None,
    ) -> Set[str]:

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

            matches.update(
                self.parameter_to_chunks.get(
                    parameter,
                    set(),
                )
            )

        if grade:

            normalized = self._normalize_key(
                grade
            )

            matches.update(
                self.grade_to_chunks.get(
                    normalized,
                    set(),
                )
            )

        if standard_code:

            normalized = self._normalize_key(
                standard_code
            )

            matches.update(
                self.standard_to_chunks.get(
                    normalized,
                    set(),
                )
            )

        return matches
