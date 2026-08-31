"""
Dataset-Driven Exact Inverted Index for Phase 2E.
Extracts exact identifiers, standard codes, grades, cap codes, and parameter keys directly from chunk data.
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


class ExactInvertedIndex:
    """Inverted index mapping exact technical tokens to matching chunk IDs."""

    def __init__(self, chunks_dir: Optional[Path] = None):
        self.chunks_dir = chunks_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "chunks")
        self.identifier_to_chunks: Dict[str, Set[str]] = {}
        self.parameter_to_chunks: Dict[str, Set[str]] = {}
        self.grade_to_chunks: Dict[str, Set[str]] = {}
        self.standard_to_chunks: Dict[str, Set[str]] = {}
        self._build_index()

    def _normalize_key(self, token: str) -> str:
        return token.strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    def _build_index(self):
        """Scans all chunk JSON files and constructs inverted posting lists."""
        if not self.chunks_dir.exists():
            logger.warning("Chunks directory does not exist: %s", self.chunks_dir)
            return

        chunk_files = list(self.chunks_dir.glob("*.json"))
        for cf in chunk_files:
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
            except Exception as e:
                logger.error("Error reading %s: %s", cf, e)
                continue

            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                if not chunk_id:
                    continue

                text = chunk.get("text", "")
                text_lower = text.lower()
                std_num = chunk.get("standard_number", "")
                clause_num = chunk.get("clause_number", "")
                structured = chunk.get("structured_data", {}) or {}

                # 1. Index Standard Number
                if std_num:
                    clean_std = self._normalize_key(std_num)
                    self.standard_to_chunks.setdefault(clean_std, set()).add(chunk_id)
                    # Index main number (e.g. IS 16102)
                    main_std_match = re.search(r"IS\s*(\d+)", std_num, re.IGNORECASE)
                    if main_std_match:
                        self.standard_to_chunks.setdefault(f"is{main_std_match.group(1)}", set()).add(chunk_id)

                # 2. Index Cap Codes / Technical Identifiers
                cap_matches = re.findall(r"\b(B22d|B15d|GX53|E17|E27|E14|E26|E40|G9|G4|GU10|R7s)\b", text, re.IGNORECASE)
                for cap in cap_matches:
                    norm_cap = self._normalize_key(cap)
                    self.identifier_to_chunks.setdefault(norm_cap, set()).add(chunk_id)

                # 3. Index Material & Steel / Cement Grades
                grades = re.findall(r"\b(Fe\s*550D|Fe\s*550|Fe\s*500D|Fe\s*500|Fe\s*415D|Fe\s*415|Fe\s*600|53\s*Grade|43\s*Grade|33\s*Grade|OPC\s*53|OPC\s*43|OPC\s*33)\b", text, re.IGNORECASE)
                for g in grades:
                    norm_g = self._normalize_key(g)
                    self.grade_to_chunks.setdefault(norm_g, set()).add(chunk_id)

                # 4. Index Canonical Parameters from Structured Requirements and Text
                # Check structured requirements
                reqs = structured.get("requirements", [])
                for req in reqs:
                    p_name = req.get("parameter", "")
                    if p_name:
                        self.parameter_to_chunks.setdefault(p_name, set()).add(chunk_id)

                # Keyword based parameter indexing
                if "insulation resistance" in text_lower or clause_num.startswith("8"):
                    self.parameter_to_chunks.setdefault("insulation_resistance", set()).add(chunk_id)
                if "yield stress" in text_lower or "0.2 percent proof stress" in text_lower or "0.2% proof stress" in text_lower:
                    self.parameter_to_chunks.setdefault("yield_stress", set()).add(chunk_id)
                if "elongation" in text_lower or "percentage elongation" in text_lower:
                    self.parameter_to_chunks.setdefault("percentage_elongation", set()).add(chunk_id)
                if "torque" in text_lower or "torsion moment" in text_lower or clause_num.startswith("9"):
                    self.parameter_to_chunks.setdefault("torque_moment", set()).add(chunk_id)
                if "compressive strength" in text_lower:
                    self.parameter_to_chunks.setdefault("compressive_strength", set()).add(chunk_id)
                if "air delivery" in text_lower:
                    self.parameter_to_chunks.setdefault("air_delivery", set()).add(chunk_id)
                if "proof pressure" in text_lower or "hydraulic" in text_lower:
                    self.parameter_to_chunks.setdefault("proof_pressure", set()).add(chunk_id)
                if "mass" in text_lower and ("helmet" in text_lower or "1500" in text_lower):
                    self.parameter_to_chunks.setdefault("mass", set()).add(chunk_id)
                if "ph" in text_lower:
                    self.parameter_to_chunks.setdefault("ph", set()).add(chunk_id)

        logger.info(
            "ExactInvertedIndex built: %d identifiers, %d standards, %d grades, %d parameter keys",
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
        standard_code: Optional[str] = None
    ) -> Set[str]:
        """Returns candidate chunk IDs matching exact search keys."""
        matches: Set[str] = set()

        if exact_identifiers:
            for ident in exact_identifiers:
                norm_ident = self._normalize_key(ident)
                if norm_ident in self.identifier_to_chunks:
                    matches.update(self.identifier_to_chunks[norm_ident])
                if norm_ident in self.grade_to_chunks:
                    matches.update(self.grade_to_chunks[norm_ident])

        if parameter and parameter in self.parameter_to_chunks:
            matches.update(self.parameter_to_chunks[parameter])

        if grade:
            norm_g = self._normalize_key(grade)
            if norm_g in self.grade_to_chunks:
                matches.update(self.grade_to_chunks[norm_g])

        if standard_code:
            norm_std = self._normalize_key(standard_code)
            if norm_std in self.standard_to_chunks:
                matches.update(self.standard_to_chunks[norm_std])

        return matches
