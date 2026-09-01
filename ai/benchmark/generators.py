"""
Corpus-Grounded Deterministic Test Generators (Phase 4B - 4E).
Generates benchmark test cases across 10 distinct categories directly from the corpus.
"""
import re
from typing import List, Dict, Any, Optional
from ai.benchmark.models import BenchmarkCase
from ai.benchmark.catalog import CorpusCatalog, CatalogProduct, CatalogStandard, CatalogRequirement


class BenchmarkGenerators:
    """Generates structured benchmark test cases grounded in the BIS corpus catalog."""

    @classmethod
    def generate_product_lookup_cases(cls, catalog: CorpusCatalog, max_per_product: int = 3) -> List[BenchmarkCase]:
        """Generates standard identification & lookup cases for all discovered products."""
        templates = [
            "Which Indian Standard governs {product}?",
            "What BIS standard applies to {product}?",
            "Which standard covers {product}?",
            "What is the applicable Indian Standard for {product}?",
            "Which IS standard specifies requirements for {product}?"
        ]
        cases: List[BenchmarkCase] = []

        for p in catalog.products:
            prod_names = [p.name] + p.aliases[:2]
            for name_idx, name in enumerate(prod_names):
                if len(name.strip()) < 5:
                    continue
                for idx, t in enumerate(templates[:max_per_product]):
                    clean_std = re.sub(r"\s*:\s*\d{4}", "", p.standard_number).strip()
                    c_id = f"PROD-{p.domain[:3].upper()}-{p.product_id[-4:]}-{name_idx+1}-{idx+1}"
                    cases.append(BenchmarkCase(
                        id=c_id,
                        category=p.domain,
                        query=t.format(product=name),
                        query_type="STANDARD_LOOKUP",
                        expected_status="VERIFIED",
                        expected_standard=clean_std,
                        expected_document_id=p.document_id,
                        expected_product=p.name,
                        expected_domain=p.domain,
                        generation_source=f"Registry::Product({p.product_id})::{name}"
                    ))
        return cases

    @classmethod
    def generate_technical_value_cases(cls, catalog: CorpusCatalog) -> List[BenchmarkCase]:
        """Generates technical parameter & value cases from verified corpus clauses."""
        cases: List[BenchmarkCase] = []
        param_descriptions = {
            "yield_stress": "yield strength",
            "tensile_strength": "tensile strength",
            "percentage_elongation": "percentage elongation",
            "insulation_resistance": "insulation resistance",
            "thermal_efficiency": "thermal efficiency",
            "compressive_strength": "compressive strength"
        }

        for i, req in enumerate(catalog.requirements, 1):
            p_desc = param_descriptions.get(req.parameter, req.parameter.replace("_", " "))
            subject = req.grade if req.grade else req.standard_number

            # Query 1: Direct Value
            q1 = f"What is the minimum {p_desc} of {subject}?" if req.parameter == "yield_stress" else f"What is the {p_desc} requirement for {subject}?"
            clean_std = re.sub(r"\s*:\s*\d{4}", "", req.standard_number).strip()

            cases.append(BenchmarkCase(
                id=f"TECH-DIR-{req.document_id}-{i:03d}",
                category="technical_values",
                query=q1,
                query_type="TECHNICAL_VALUE",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=req.document_id,
                expected_clause=req.clause_number,
                expected_parameter=req.parameter,
                expected_value=req.value,
                expected_unit=req.unit,
                expected_normative_force=req.normative_force,
                source_chunk_ids=[req.source_chunk_id] if req.source_chunk_id else [],
                generation_source=f"{req.document_id}::Clause {req.clause_number}"
            ))

            # Query 2: Clause Inquiry
            cases.append(BenchmarkCase(
                id=f"TECH-CLA-{req.document_id}-{i:03d}",
                category="clause_questions",
                query=f"What does Clause {req.clause_number} of {clean_std} specify for {subject}?",
                query_type="TECHNICAL_VALUE",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=req.document_id,
                expected_clause=req.clause_number,
                expected_parameter=req.parameter,
                expected_value=req.value,
                expected_unit=req.unit,
                source_chunk_ids=[req.source_chunk_id] if req.source_chunk_id else [],
                generation_source=f"{req.document_id}::Clause {req.clause_number}::ClauseInquiry"
            ))

        return cases

    @classmethod
    def generate_unsupported_materials_cases(cls) -> List[BenchmarkCase]:
        """Generates safety cases for 30+ unsupported metallurgical and chemical materials."""
        materials = [
            ("Titanium Grade 5", "yield strength"),
            ("Ti-6Al-4V aerospace alloy", "tensile strength"),
            ("Kevlar body armor", "tensile strength"),
            ("Inconel 718 aerospace alloy", "yield strength"),
            ("Inconel 625", "tensile strength"),
            ("Graphene nanoplatelets", "electrical conductivity"),
            ("Zirconium alloy nuclear cladding", "corrosion rate"),
            ("Carbon fiber reinforced polymer composite", "tensile modulus"),
            ("Aramid ballistic fabric", "puncture resistance"),
            ("Magnesium alloy AZ31", "yield strength"),
            ("Nickel superalloy turbine blade", "creep rupture life"),
            ("Tungsten carbide cutting insert", "Vickers hardness"),
            ("Molybdenum disilicide heating element", "operating temperature"),
            ("Cobalt chrome orthopedic alloy", "fatigue limit"),
            ("Beryllium copper spring", "yield strength"),
            ("Boron nitride ceramic", "thermal conductivity"),
            ("Shape memory Nitinol", "transformation temperature"),
            ("Ultra high molecular weight polyethylene", "impact resistance"),
            ("Aerogel insulation blanket", "thermal conductivity"),
            ("Gallium nitride semiconductor", "breakdown voltage")
        ]
        cases: List[BenchmarkCase] = []
        forbidden_defaults = ["IS 1786", "IS 2062", "IS 4246", "IS 374", "IS 16102", "IS 14543"]

        for i, (mat, param) in enumerate(materials, 1):
            cases.append(BenchmarkCase(
                id=f"SAFE-UNSUP-{i:03d}",
                category="safety_unsupported",
                query=f"What is the {param} of {mat}?",
                query_type="SAFETY_ABSTENTION",
                expected_status="ABSTAINED",
                abstention_reason="INCOMPATIBLE_ENTITY",
                forbidden_standards=forbidden_defaults,
                generation_source=f"SafetyAdversarial::UnsupportedMaterial::{mat}"
            ))
            cases.append(BenchmarkCase(
                id=f"SAFE-UNSUP-STD-{i:03d}",
                category="safety_unsupported",
                query=f"Which Indian Standard specifies {mat}?",
                query_type="SAFETY_ABSTENTION",
                expected_status="ABSTAINED",
                abstention_reason="INCOMPATIBLE_ENTITY",
                forbidden_standards=forbidden_defaults,
                generation_source=f"SafetyAdversarial::UnsupportedStandard::{mat}"
            ))

        return cases

    @classmethod
    def generate_cross_domain_cases(cls, catalog: CorpusCatalog) -> List[BenchmarkCase]:
        """Generates cross-domain traps combining valid entities with foreign domain parameters."""
        traps = [
            ("Fe 500D steel rebar", "pH requirement", "chemical"),
            ("Fe 500D steel reinforcement bars", "air delivery", "electrical"),
            ("Fe 550D rebar", "bacterial filtration efficiency", "medical"),
            ("Fe 650 steel bars", "milk fat percentage", "food"),
            ("high strength deformed steel bars", "thermal efficiency of burner", "mechanical"),
            ("packaged drinking water", "yield strength", "metallurgy"),
            ("packaged drinking water", "torsion resistance", "electrical"),
            ("packaged natural mineral water", "compressive crushing load", "civil"),
            ("electric ceiling fans", "pH value", "chemical"),
            ("electric ceiling fans", "28-day compressive strength", "civil"),
            ("self-ballasted LED lamps", "hydraulic proof pressure", "mechanical"),
            ("domestic gas stoves", "insulation resistance", "electrical"),
            ("domestic gas stoves", "bacterial filtration efficiency", "medical"),
            ("portland pozzolana cement", "air delivery in m3/min", "electrical"),
            ("ordinary Portland cement", "water bath leakage temperature", "mechanical"),
            ("protective helmets for two wheeler riders", "thermal efficiency", "mechanical"),
            ("industrial safety helmets", "fat percentage limit", "food")
        ]
        cases: List[BenchmarkCase] = []

        for i, (prod, param_name, foreign_domain) in enumerate(traps, 1):
            cases.append(BenchmarkCase(
                id=f"SAFE-CROSS-{i:03d}",
                category="safety_cross_domain",
                query=f"What is the required {param_name} of {prod}?",
                query_type="CROSS_DOMAIN_TRAP",
                expected_status="ABSTAINED",
                abstention_reason="CROSS_DOMAIN_MISMATCH",
                generation_source=f"CrossDomainTrap::{prod} x {param_name} ({foreign_domain})"
            ))

        return cases

    @classmethod
    def generate_explicit_is_precedence_cases(cls, catalog: CorpusCatalog) -> List[BenchmarkCase]:
        """Generates explicit IS identifier lookup & edition collision regression tests."""
        cases: List[BenchmarkCase] = []

        for i, std in enumerate(catalog.standards, 1):
            clean_std = std.clean_number
            cases.append(BenchmarkCase(
                id=f"PREC-STD-{i:03d}",
                category="precedence_explicit_is",
                query=f"What does {clean_std} specify?",
                query_type="EXPLICIT_IS_PRECEDENCE",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=std.document_id,
                generation_source=f"ExplicitISPrecedence::{clean_std}"
            ))

            # If standard has edition (e.g. Fifth Revision), test edition lookup
            if std.edition:
                ed_clean = std.edition.replace("Specification", "").replace("(", "").replace(")", "").strip()
                if "Revision" in ed_clean:
                    cases.append(BenchmarkCase(
                        id=f"PREC-REV-{i:03d}",
                        category="precedence_revision",
                        query=f"What does the {ed_clean.lower()} of {clean_std} specify?",
                        query_type="EXPLICIT_IS_PRECEDENCE",
                        expected_status="VERIFIED",
                        expected_standard=clean_std,
                        expected_document_id=std.document_id,
                        generation_source=f"RevisionPrecedence::{clean_std}::{ed_clean}"
                    ))

        # Explicit Hard Adversarial Collisions
        cases.append(BenchmarkCase(
            id="PREC-COLL-001",
            category="precedence_collision",
            query="What does the fifth revision of IS 1786 specify?",
            query_type="EXPLICIT_IS_PRECEDENCE",
            expected_status="VERIFIED",
            expected_standard="IS 1786",
            expected_document_id="DOC-034",
            forbidden_standards=["IS 4246"],
            generation_source="CollisionTrap::IS 1786 Fifth Rev vs IS 4246"
        ))
        cases.append(BenchmarkCase(
            id="PREC-COLL-002",
            category="precedence_collision",
            query="What does IS 4246 fifth revision specify for domestic gas stoves?",
            query_type="EXPLICIT_IS_PRECEDENCE",
            expected_status="VERIFIED",
            expected_standard="IS 4246",
            expected_document_id="DOC-002",
            forbidden_standards=["IS 1786"],
            generation_source="CollisionTrap::IS 4246 Fifth Rev vs IS 1786"
        ))

        return cases

    @classmethod
    def generate_ambiguity_cases(cls) -> List[BenchmarkCase]:
        """Generates underspecified queries requiring clarification or safe abstention."""
        ambiguous_queries = [
            ("Which standard applies to pipes?", "pipes"),
            ("What BIS standard applies to steel?", "steel"),
            ("Which standard covers fans?", "fans"),
            ("What is the specification for cement?", "cement"),
            ("Which Indian Standard applies to cables?", "cables"),
            ("What is the requirement for helmets?", "helmets"),
            ("Which standard governs boots?", "boots"),
            ("What is the standard for masks?", "masks")
        ]
        cases: List[BenchmarkCase] = []

        for i, (q, broad_term) in enumerate(ambiguous_queries, 1):
            cases.append(BenchmarkCase(
                id=f"AMB-{i:03d}",
                category="ambiguity",
                query=q,
                query_type="AMBIGUITY_CLARIFICATION",
                expected_status="ABSTAINED",
                abstention_reason="INSUFFICIENT_EVIDENCE",
                generation_source=f"AmbiguityTrap::BroadTerm({broad_term})"
            ))

        return cases

    @classmethod
    def generate_multilingual_cases(cls, catalog: CorpusCatalog) -> List[BenchmarkCase]:
        """Generates Hindi and Hinglish query variations for top products."""
        cases: List[BenchmarkCase] = []
        sample_products = catalog.products[:25]

        for i, p in enumerate(sample_products, 1):
            clean_std = re.sub(r"\s*:\s*\d{4}", "", p.standard_number).strip()
            # Hinglish 1: ke liye kaunsa standard
            cases.append(BenchmarkCase(
                id=f"MULTI-HING-STD-{i:03d}",
                category="multilingual_hinglish",
                query=f"{p.name} ke liye kaunsa BIS standard hai?",
                query_type="MULTILINGUAL",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=p.document_id,
                generation_source=f"Multilingual::Hinglish::{p.name}"
            ))
            # Hinglish 2: par kaunsa IS standard apply hota hai
            cases.append(BenchmarkCase(
                id=f"MULTI-HING-APP-{i:03d}",
                category="multilingual_hinglish",
                query=f"{p.name} par kaunsa Indian Standard apply hota hai?",
                query_type="MULTILINGUAL",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=p.document_id,
                generation_source=f"Multilingual::HinglishApply::{p.name}"
            ))

        # Technical Hinglish cases
        cases.append(BenchmarkCase(
            id="MULTI-HING-TECH-001",
            category="multilingual_hinglish",
            query="Fe 500D ka minimum yield strength kitna hai?",
            query_type="MULTILINGUAL",
            expected_status="VERIFIED",
            expected_standard="IS 1786",
            expected_clause="7.1",
            expected_parameter="yield_stress",
            expected_value=500.0,
            expected_unit="MPa",
            generation_source="Multilingual::Technical::Fe500D"
        ))

        return cases

    @classmethod
    def generate_certification_cases(cls, catalog: CorpusCatalog) -> List[BenchmarkCase]:
        """Generates certification, ISI mark, and QCO queries grounded in catalog evidence."""
        cases: List[BenchmarkCase] = []
        sample_prods = [p for p in catalog.products if p.mandatory_certification][:20]

        for i, p in enumerate(sample_prods, 1):
            clean_std = re.sub(r"\s*:\s*\d{4}", "", p.standard_number).strip()
            cases.append(BenchmarkCase(
                id=f"CERT-MAND-{i:03d}",
                category="certification",
                query=f"Is BIS certification mandatory for {p.name}?",
                query_type="CERTIFICATION_QUERY",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=p.document_id,
                generation_source=f"Certification::Mandatory::{p.name}"
            ))
            cases.append(BenchmarkCase(
                id=f"CERT-QCO-{i:03d}",
                category="certification",
                query=f"Does {p.name} require an ISI mark under Indian QCO?",
                query_type="CERTIFICATION_QUERY",
                expected_status="VERIFIED",
                expected_standard=clean_std,
                expected_document_id=p.document_id,
                generation_source=f"Certification::QCO::{p.name}"
            ))

        return cases
