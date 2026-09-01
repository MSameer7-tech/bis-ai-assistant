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
        self.chunks_by_id: Dict[str, Dict[str, Any]] = {}
        self._build_index()

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Returns the full chunk dictionary by ID."""
        return self.chunks_by_id.get(chunk_id)

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

                self.chunks_by_id[chunk_id] = chunk

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
                if "insulation resistance" in text_lower or clause_num.startswith("8") or "humidity" in text_lower or "preconditioning" in text_lower or "25°c" in text_lower or "35°c" in text_lower:
                    self.parameter_to_chunks.setdefault("insulation_resistance", set()).add(chunk_id)
                if "yield stress" in text_lower or "0.2 percent proof stress" in text_lower or "0.2% proof stress" in text_lower or "proof stress" in text_lower:
                    self.parameter_to_chunks.setdefault("yield_stress", set()).add(chunk_id)
                if "elongation" in text_lower or "percentage elongation" in text_lower or "16.0%" in text_lower:
                    self.parameter_to_chunks.setdefault("percentage_elongation", set()).add(chunk_id)
                if "torque" in text_lower or "torsion moment" in text_lower or clause_num.startswith("9"):
                    self.parameter_to_chunks.setdefault("torque_moment", set()).add(chunk_id)
                if "compressive strength" in text_lower:
                    self.parameter_to_chunks.setdefault("compressive_strength", set()).add(chunk_id)
                if "air delivery" in text_lower:
                    self.parameter_to_chunks.setdefault("air_delivery", set()).add(chunk_id)
                if "proof pressure" in text_lower or "hydraulic" in text_lower or "burst" in text_lower:
                    self.parameter_to_chunks.setdefault("proof_pressure", set()).add(chunk_id)
                if "mass" in text_lower and ("helmet" in text_lower or "1500" in text_lower):
                    self.parameter_to_chunks.setdefault("mass", set()).add(chunk_id)
                if "ph" in text_lower:
                    self.parameter_to_chunks.setdefault("ph", set()).add(chunk_id)
                if "thermal efficiency" in text_lower or "gas stove" in text_lower or "68%" in text_lower:
                    self.parameter_to_chunks.setdefault("thermal_efficiency", set()).add(chunk_id)
                if "shock absorption" in text_lower or "transmitted force" in text_lower or "headform deceleration" in text_lower:
                    self.parameter_to_chunks.setdefault("shock_absorption", set()).add(chunk_id)
                if "bacterial filtration" in text_lower or "bfe" in text_lower or "filtration efficiency" in text_lower or "98%" in text_lower:
                    self.parameter_to_chunks.setdefault("filtration_efficiency", set()).add(chunk_id)
                if "carbon" in text_lower or "sulfur" in text_lower or "phosphorus" in text_lower:
                    self.parameter_to_chunks.setdefault("chemical_limits", set()).add(chunk_id)
                if "agt" in text_lower or "total elongation at maximum force" in text_lower or "gauge length" in text_lower:
                    self.parameter_to_chunks.setdefault("total_elongation_agt", set()).add(chunk_id)
                if "water bath" in text_lower or "leakage" in text_lower:
                    self.parameter_to_chunks.setdefault("leakage_temperature", set()).add(chunk_id)
                if "15 kn" in text_lower or "sustained" in text_lower or "harness" in text_lower or "static" in text_lower:
                    self.parameter_to_chunks.setdefault("static_test_duration", set()).add(chunk_id)
                if "hydrostatic" in text_lower or "2.5 minutes" in text_lower or "coupling" in text_lower or "proof pressure" in text_lower:
                    self.parameter_to_chunks.setdefault("hydrostatic_duration", set()).add(chunk_id)
                if "accelerated ageing" in text_lower or "ageing" in text_lower or "glove" in text_lower or "surgical" in text_lower or "24.0 mpa" in text_lower:
                    self.parameter_to_chunks.setdefault("ageing_condition", set()).add(chunk_id)
                if "water meter" in text_lower or "flow zone" in text_lower or "permissible error" in text_lower or "class a" in text_lower or "±2%" in text_lower:
                    self.parameter_to_chunks.setdefault("flow_error", set()).add(chunk_id)
                if "2000 h" in text_lower or "lumen maintenance" in text_lower or "25 000 h" in text_lower or "25000" in text_lower:
                    self.parameter_to_chunks.setdefault("lumen_maintenance", set()).add(chunk_id)

        logger.info(
            "ExactInvertedIndex built: %d identifiers, %d standards, %d grades, %d parameter keys",
            len(self.identifier_to_chunks),
            len(self.standard_to_chunks),
            len(self.grade_to_chunks),
            len(self.parameter_to_chunks),
        )

    PRODUCT_TO_STANDARDS = {
        "domestic water meters": "is779",
        "pvc industrial boots": "is12254",
        "diagnostic medical x-ray equipment": "is7620(part1)",
        "safety footwear": "is15298(part2)",
        "safety belts and harnesses": "is3521(part1)",
        "full body harnesses": "is3521(part1)",
        "full body harness": "is3521(part1)",
        "fall protection": "is3521(part1)",
        "fire hose delivery couplings": "is903",
        "portable fire extinguishers": "is15683",
        "rubber surgical gloves": "is13422",
        "sterile rubber surgical gloves": "is13422",
        "medical face masks": "is16289",
        "medical masks": "is16289",
        "respiratory protective filtering half masks": "is9473",
        "unplasticized pvc pipes": "is4985",
        "aggregates for concrete": "is383",
        "domestic gas stoves": "is4246",
        "non-refillable metallic lpg containers": "is13745",
        "domestic pressure cookers": "is2347",
        "industrial safety helmets": "is2925",
        "protective helmets for two wheeler riders": "is4151",
        "protective helmets for motorcycle riders": "is4151",
        "crash helmets": "is4151",
        "ordinary portland cement": "is269",
        "portland pozzolana cement": "is1489(part1)",
        "high strength deformed steel bars": "is1786",
        "tmt reinforcement bars": "is1786",
        "reinforcement steel bars": "is1786",
        "reinforcement steel": "is1786",
        "secondary lithium batteries": "is16046(part2)",
        "self-ballasted led lamps": "is16102(part1)",
        "electric ceiling fans": "is374",
        "drinking water": "is10500",
        "drinking water quality": "is10500",
        "packaged drinking water": "is14543",
        "infant milk substitutes": "is14433",
        "infant milk": "is14433",
        "hot rolled medium and high tensile structural steel": "is2062",
        "structural steel": "is2062",
        "domestic cooking gas burners": "is4246",
        "cooking gas burners": "is4246",
        "gas burners": "is4246",
        "hard hats": "is2925",
        "work boots": "is15298(part2)",
        "steel toe cap work boots": "is15298(part2)",
        "safety belts and harnesses": "is3521(part1)",
        "full body harnesses": "is3521(part1)",
        "safety harness": "is3521(part1)",
        "safety belts": "is3521(part1)",
        "fall protection": "is3521(part1)",
        "domestic water meters": "is779",
        "water meters": "is779",
        "portland pozzolana cement fly ash based": "is1489(part1)",
        "fly ash based cement": "is1489(part1)",
    }

    def get_matching_chunks(
        self,
        exact_identifiers: Optional[List[str]] = None,
        parameter: Optional[str] = None,
        grade: Optional[str] = None,
        standard_code: Optional[str] = None,
        product: Optional[str] = None,
    ) -> Set[str]:
        """Returns set of chunk IDs matching any of the exact structured filters."""
        matched: Set[str] = set()

        if exact_identifiers:
            for ident in exact_identifiers:
                norm = self._normalize_key(ident)
                if norm in self.identifier_to_chunks:
                    matched.update(self.identifier_to_chunks[norm])

        if parameter:
            norm_param = parameter.strip().lower()
            if norm_param in self.parameter_to_chunks:
                matched.update(self.parameter_to_chunks[norm_param])

        if grade:
            norm_grade = self._normalize_key(grade)
            if norm_grade in self.grade_to_chunks:
                matched.update(self.grade_to_chunks[norm_grade])

        if standard_code:
            norm_std = self._normalize_key(standard_code)
            for std_key, cids in self.standard_to_chunks.items():
                if norm_std in std_key or std_key in norm_std:
                    matched.update(cids)

        if product:
            prod_clean = product.strip().lower()
            try:
                from ai.retrieval.product_resolver import resolve_product
                resolved = resolve_product(prod_clean)
                if resolved and resolved.get("standard_number"):
                    std_norm = self._normalize_key(resolved["standard_number"])
                    for std_key, cids in self.standard_to_chunks.items():
                        if std_norm in std_key or std_key in std_norm:
                            matched.update(cids)
                else:
                    std_target = self.PRODUCT_TO_STANDARDS.get(prod_clean)
                    if std_target:
                        for std_key, cids in self.standard_to_chunks.items():
                            if std_target in std_key or std_key in std_target:
                                matched.update(cids)
            except Exception:
                std_target = self.PRODUCT_TO_STANDARDS.get(prod_clean)
                if std_target:
                    for std_key, cids in self.standard_to_chunks.items():
                        if std_target in std_key or std_key in std_target:
                            matched.update(cids)

        return matched
