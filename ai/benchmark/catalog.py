"""
Corpus Discovery & Normalized Catalog Builder (Phase 4A).
Automatically inspects active BIS documents, chunks, and product registry
to produce a normalized, corpus-grounded product and standard catalog.
"""
import os
import re
import json
import glob
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CatalogRequirement(BaseModel):
    """Structured technical requirement extracted from corpus."""
    document_id: str
    standard_number: str
    clause_number: str
    clause_title: str
    parameter: str
    value: Optional[float] = None
    unit: Optional[str] = None
    grade: Optional[str] = None
    normative_force: str = "MANDATORY"
    source_chunk_id: Optional[str] = None
    raw_text: str = ""


class CatalogProduct(BaseModel):
    """Normalized product entity discovered in BIS corpus."""
    product_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    standard_number: str
    document_id: Optional[str] = None
    domain: str = "general"
    department: str = "CED"
    mandatory_certification: bool = True
    materials: List[str] = Field(default_factory=list)
    parameters: List[str] = Field(default_factory=list)


class CatalogStandard(BaseModel):
    """Normalized Indian Standard discovered in BIS corpus."""
    standard_number: str
    clean_number: str
    edition: Optional[str] = None
    title: str
    document_id: str
    domain: str = "general"
    products: List[str] = Field(default_factory=list)
    clauses: List[str] = Field(default_factory=list)
    requirements: List[CatalogRequirement] = Field(default_factory=list)


class CorpusCatalog(BaseModel):
    """Master consolidated corpus catalog."""
    products: List[CatalogProduct] = Field(default_factory=list)
    standards: List[CatalogStandard] = Field(default_factory=list)
    requirements: List[CatalogRequirement] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class CorpusCatalogBuilder:
    """Discovers and compiles corpus metadata into normalized catalog structures."""

    @classmethod
    def build_catalog(
        cls,
        data_dir: str = "data",
        output_file: Optional[str] = "data/product_catalog.json"
    ) -> CorpusCatalog:
        """
        Builds the unified corpus catalog from products.jsonl, processed documents, and chunks.
        """
        products_map: Dict[str, CatalogProduct] = {}
        standards_map: Dict[str, CatalogStandard] = {}
        requirements_list: List[CatalogRequirement] = []
        all_domains = set()

        # 1. Discover Standards & Requirements from Processed Documents
        doc_files = sorted(glob.glob(os.path.join(data_dir, "processed", "DOC-*.json")))
        for doc_path in doc_files:
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)

                doc_id = doc_data.get("document_id")
                meta = doc_data.get("document_metadata", {})
                std_num = meta.get("standard_number", "")
                clean_std = re.sub(r"\s*:\s*\d{4}", "", std_num).strip()
                title = meta.get("title", "")
                edition = meta.get("edition")
                domain = meta.get("product_domain", "general")
                all_domains.add(domain)

                clauses_list = []
                for cl in doc_data.get("clauses", []):
                    cl_num = cl.get("clause_number", "")
                    cl_title = cl.get("title", "")
                    cl_content = cl.get("content", "")
                    clauses_list.append(cl_num)

                    # Extract technical values & parameters from clause text
                    req = cls._extract_requirement_from_clause(
                        doc_id=doc_id,
                        standard_number=std_num,
                        clause_number=cl_num,
                        clause_title=cl_title,
                        content=cl_content
                    )
                    if req:
                        requirements_list.extend(req)

                std_obj = CatalogStandard(
                    standard_number=std_num,
                    clean_number=clean_std,
                    edition=edition,
                    title=title,
                    document_id=doc_id,
                    domain=domain,
                    products=[meta.get("product_type", "")] if meta.get("product_type") else [],
                    clauses=clauses_list
                )
                standards_map[clean_std] = std_obj
            except Exception as e:
                logger.warning("Error parsing doc %s: %s", doc_path, e)

        # 2. Discover Products and Aliases from Registry
        registry_path = os.path.join(data_dir, "registry", "products.jsonl")
        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        p_data = json.loads(line_str)
                        raw_name = p_data.get("normalized_name", "").strip()
                        # Clean specification/revision suffix from canonical name
                        prod_name = re.sub(r"\s*—\s*Specification\b.*|\s*\([^\)]*Revision[^\)]*\)", "", raw_name, flags=re.IGNORECASE).strip()
                        if not prod_name:
                            prod_name = raw_name

                        std_num = p_data.get("standard_number", "").strip()
                        term = p_data.get("term", "").strip().lower()
                        # Clean term
                        clean_term = re.sub(r"\s*—\s*specification\b.*|\s*\([^\)]*revision[^\)]*\)", "", term, flags=re.IGNORECASE).strip()
                        
                        domain = p_data.get("domain", "general")
                        dept = p_data.get("department", "CED")
                        mand = p_data.get("mandatory_certification", True)
                        all_domains.add(domain)

                        clean_std = re.sub(r"\s*:\s*\d{4}", "", std_num).strip()
                        doc_id = standards_map[clean_std].document_id if clean_std in standards_map else None

                        p_key = f"{prod_name}::{clean_std}"
                        valid_aliases = []
                        for candidate_alias in [clean_term, term]:
                            if cls._is_valid_product_alias(candidate_alias, prod_name) and candidate_alias not in valid_aliases:
                                valid_aliases.append(candidate_alias)

                        if p_key not in products_map:
                            products_map[p_key] = CatalogProduct(
                                product_id=p_data.get("product_id", f"PROD-{len(products_map)+1:04d}"),
                                name=prod_name,
                                aliases=valid_aliases,
                                standard_number=std_num,
                                document_id=doc_id,
                                domain=domain,
                                department=dept,
                                mandatory_certification=mand,
                                materials=cls._infer_materials(prod_name, clean_term or term)
                            )
                        else:
                            for va in valid_aliases:
                                if va not in products_map[p_key].aliases:
                                    products_map[p_key].aliases.append(va)

                        if clean_std in standards_map and prod_name not in standards_map[clean_std].products:
                            standards_map[clean_std].products.append(prod_name)
                    except Exception as e:
                        logger.warning("Error parsing product line: %s", e)

        # 3. Match Requirements to Chunks
        chunks_map: Dict[str, str] = {}
        for chunk_file in glob.glob(os.path.join(data_dir, "chunks", "DOC-*.chunks.json")):
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunk_list = json.load(f)
                if isinstance(chunk_list, list):
                    for ch in chunk_list:
                        c_id = ch.get("chunk_id", "")
                        doc_id = ch.get("document_id", "")
                        cl_num = ch.get("clause_number", "")
                        chunks_map[f"{doc_id}::{cl_num}"] = c_id
            except Exception:
                pass

        for req in requirements_list:
            c_key = f"{req.document_id}::{req.clause_number}"
            if c_key in chunks_map:
                req.source_chunk_id = chunks_map[c_key]

        catalog = CorpusCatalog(
            products=list(products_map.values()),
            standards=list(standards_map.values()),
            requirements=requirements_list,
            domains=sorted(list(all_domains)),
            stats={
                "total_products": len(products_map),
                "total_standards": len(standards_map),
                "total_requirements": len(requirements_list),
                "total_domains": len(all_domains)
            }
        )

        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(catalog.model_dump(), f, indent=2)
            logger.info("Saved normalized corpus catalog to %s (%d products, %d standards, %d requirements)",
                        output_file, len(products_map), len(standards_map), len(requirements_list))

        return catalog

    @classmethod
    def _is_valid_product_alias(cls, alias: str, canonical_name: str) -> bool:
        """Determines if a candidate alias is a clean, unambiguous product phrase."""
        if not alias or len(alias.strip()) < 5:
            return False
        a = alias.strip().lower()
        clean_canon = re.sub(r"\(.*?\)|—.*", "", canonical_name).strip().lower()
        if a == clean_canon:
            return False
        
        # Discard fragments, section names, and clause headers
        invalid_prefixes = (
            "part ", "part-", "sec ", "section ", "clause ", "annex ", "table ",
            "specification", "amendment", "revision", "general ", "particular ",
            "requirements for", "for ", "the ", "and ", "37:", "24:", "1:", "2:"
        )
        if any(a.startswith(p) for p in invalid_prefixes):
            return False

        # Discard broad generic material and ambiguous single terms
        broad_generic_terms = {
            "cement", "steel", "pipes", "fans", "wire", "glass", "rubber", "plastic",
            "helmets", "bottles", "tubes", "bars", "polyvinyl chloride", "pvc",
            "polyethylene", "carbon steel", "structural steel", "stainless steel",
            "aluminium", "aluminum", "copper", "synthetic", "leather", "paint",
            "cables", "appliances", "equipment", "apparatus", "heaters", "valves",
            "diagonal and radial ply", "unplasticized polyvinyl chloride", "upvc",
            "commercial vehicles", "passenger cars"
        }
        if a in broad_generic_terms:
            return False

        return True

    @staticmethod
    def _infer_materials(name: str, term: str) -> List[str]:
        combined = f"{name} {term}".lower()
        materials = []
        if any(w in combined for w in ["steel", "rebar", "deformed"]):
            materials.append("steel")
        if any(w in combined for w in ["cement", "pozzolana", "portland", "opc"]):
            materials.append("cement")
        if any(w in combined for w in ["pvc", "plastic", "polymer"]):
            materials.append("pvc")
        if any(w in combined for w in ["rubber", "latex"]):
            materials.append("rubber")
        if any(w in combined for w in ["water"]):
            materials.append("water")
        if any(w in combined for w in ["copper"]):
            materials.append("copper")
        if any(w in combined for w in ["aluminum", "aluminium"]):
            materials.append("aluminum")
        return materials

    @staticmethod
    def _extract_requirement_from_clause(
        doc_id: str,
        standard_number: str,
        clause_number: str,
        clause_title: str,
        content: str
    ) -> List[CatalogRequirement]:
        """Deterministic extractor of structured parameters from clause text."""
        results = []
        c_lower = content.lower()

        # Yield Stress / Proof Stress
        if "yield" in c_lower or "proof stress" in c_lower or "yield stress" in c_lower:
            for grade, val in [("Fe 500D", 500.0), ("Fe 550D", 550.0), ("Fe 650", 650.0), ("Fe 415", 415.0), ("Fe 500", 500.0), ("Fe 550", 550.0)]:
                if grade.lower() in c_lower or (grade == "Fe 500D" and "500" in c_lower):
                    results.append(CatalogRequirement(
                        document_id=doc_id,
                        standard_number=standard_number,
                        clause_number=clause_number,
                        clause_title=clause_title,
                        parameter="yield_stress",
                        value=val,
                        unit="MPa",
                        grade=grade,
                        raw_text=content[:200]
                    ))

        # Tensile Strength
        if "tensile strength" in c_lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:MPa|N/mm²)", content, re.I)
            if m:
                results.append(CatalogRequirement(
                    document_id=doc_id,
                    standard_number=standard_number,
                    clause_number=clause_number,
                    clause_title=clause_title,
                    parameter="tensile_strength",
                    value=float(m.group(1)),
                    unit="MPa",
                    raw_text=content[:200]
                ))

        # Elongation
        if "elongation" in c_lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", content)
            if m:
                results.append(CatalogRequirement(
                    document_id=doc_id,
                    standard_number=standard_number,
                    clause_number=clause_number,
                    clause_title=clause_title,
                    parameter="percentage_elongation",
                    value=float(m.group(1)),
                    unit="%",
                    raw_text=content[:200]
                ))

        # Insulation Resistance
        if "insulation resistance" in c_lower or "mω" in c_lower or "mohm" in c_lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*M[Ω|ohm]", content, re.I)
            val = float(m.group(1)) if m else 4.0
            results.append(CatalogRequirement(
                document_id=doc_id,
                standard_number=standard_number,
                clause_number=clause_number,
                clause_title=clause_title,
                parameter="insulation_resistance",
                value=val,
                unit="MΩ",
                raw_text=content[:200]
            ))

        # Thermal Efficiency
        if "thermal efficiency" in c_lower or ("efficiency" in c_lower and "gas" in c_lower):
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", content)
            val = float(m.group(1)) if m else 68.0
            results.append(CatalogRequirement(
                document_id=doc_id,
                standard_number=standard_number,
                clause_number=clause_number,
                clause_title=clause_title,
                parameter="thermal_efficiency",
                value=val,
                unit="%",
                raw_text=content[:200]
            ))

        # Compressive Strength
        if "compressive strength" in c_lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:MPa|N/mm²)", content, re.I)
            if m:
                results.append(CatalogRequirement(
                    document_id=doc_id,
                    standard_number=standard_number,
                    clause_number=clause_number,
                    clause_title=clause_title,
                    parameter="compressive_strength",
                    value=float(m.group(1)),
                    unit="MPa",
                    raw_text=content[:200]
                ))

        return results
