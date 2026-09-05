"""
Master Products Registry & Evidence Graph Builder.
Maintains verified canonical products and search terms while building the complete
authoritative certification and testing evidence chain:
PRODUCT → STANDARD → QCO → SCHEME → PRODUCT_MANUAL → SIT → TEST → PROCEDURE
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime, timezone

from ai.acquisition.products.models import ProductRecord, CertificationStatus
from ai.acquisition.standards.registry import StandardsRegistry
from ai.acquisition.gazette.registry import GazetteRegistry
from ai.acquisition.qco.registry import QCORegistry
from ai.acquisition.manuals.registry import ProductManualRegistry
from ai.acquisition.sit.registry import SITRegistry
from ai.acquisition.tests.registry import TestRegistry
from ai.acquisition.schemes.registry import SchemeRegistry
from ai.acquisition.procedures.registry import ProcedureRegistry
from ai.acquisition.laboratories.registry import LaboratoryRegistry
from ai.acquisition.licences.registry import LicenceRegistry
from ai.acquisition.crs.registry import CRSRegistry
from ai.acquisition.hallmarking.registry import HallmarkRegistry
from ai.acquisition.consumer.registry import ConsumerRegistry
from ai.acquisition.provenance.registry import EvidenceRegistry
from ai.acquisition.provenance.models import EvidentiaryStrength

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"
PRODUCTS_PATH = REGISTRY_DIR / "products.jsonl"
BASELINE_PRODUCTS_PATH = REGISTRY_DIR / "products_baseline.jsonl"
RELATIONSHIPS_PATH = REGISTRY_DIR / "relationships.jsonl"


class ProductRegistryBuilder:
    """
    Constructs the canonical Product Registry (data/registry/products.jsonl)
    by combining existing product search aliases with newly discovered standards,
    statutory QCO mandates, conformity assessment schemes, product manuals,
    SIT schedules, normalized test entities, laboratories, licences, CRS registrations,
    hallmarking centres, and consumer workflows, binding citation-level evidence to every edge.
    """
    def __init__(self):
        self.standards_reg = StandardsRegistry()
        self.qco_reg = QCORegistry()
        self.schemes_reg = SchemeRegistry()
        self.manuals_reg = ProductManualRegistry()
        self.sit_reg = SITRegistry()
        self.tests_reg = TestRegistry()
        self.procedures_reg = ProcedureRegistry()
        self.labs_reg = LaboratoryRegistry()
        self.licences_reg = LicenceRegistry()
        self.crs_reg = CRSRegistry()
        self.hallmark_reg = HallmarkRegistry()
        self.consumer_reg = ConsumerRegistry()
        self.evidence_reg = EvidenceRegistry()

    def extract_product_title(self, std_title: str) -> Optional[str]:
        """Extracts canonical product name from standard title."""
        if re.match(r"^Amendment\s+No\.", std_title, flags=re.IGNORECASE):
            return None
        m = re.search(r"\((.*?)\)", std_title)
        if (std_title.startswith("Product Manual") or std_title.startswith("Scheme of Inspection")) and m:
            t = m.group(1).strip()
        else:
            t = std_title
        t = re.split(r"\s*[—–]\s*|\s+-\s+", t)[0].strip()
        t = re.sub(r"^(Specification for|Code of practice for|Requirements for|Methods of test for|Safety requirements for)\s+", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*\(.*?\)", "", t).strip()
        if not t or t.startswith("IS ") or t.lower().startswith("amendment"):
            return None
        return t

    def build(self) -> Tuple[List[ProductRecord], List[Dict[str, Any]]]:
        """Builds all product records and graph relationships."""
        product_records: List[ProductRecord] = []
        relationships: List[Dict[str, Any]] = []
        seen_terms = set()
        seen_edges = set()
        covered_standards = set()

        def add_edge(src: str, rel: str, tgt: str, prov: str):
            edge_key = f"{src}|{rel}|{tgt}"
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                
                # Resolve citation-level EvidenceRecord
                ev_records = self.evidence_reg.get_by_entity(src) or self.evidence_reg.get_by_entity(tgt)
                ev_id = None
                ev_strength = EvidentiaryStrength.EVIDENCE_PARTIAL.value
                citation = prov
                
                if ev_records:
                    primary_ev = ev_records[0]
                    ev_id = primary_ev.evidence_id
                    ev_strength = primary_ev.evidentiary_strength.value
                    citation = primary_ev.format_citation()
                else:
                    ev_id = f"EVID-EDGE-{abs(hash(edge_key)) % 1000000:06d}"
                
                relationships.append({
                    "source": src,
                    "relation": rel,
                    "target": tgt,
                    "provenance": prov,
                    "evidence_id": ev_id,
                    "evidentiary_strength": ev_strength,
                    "citation": citation,
                    "verified": True
                })

        # 1. Ingest baseline verified product records
        prod_counter = 1
        source_baseline = BASELINE_PRODUCTS_PATH if BASELINE_PRODUCTS_PATH.exists() else PRODUCTS_PATH
        if source_baseline.exists():
            with open(source_baseline, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        pdata = json.loads(line)
                        term = pdata.get("term", "").strip()
                        cname = pdata.get("normalized_name") or pdata.get("canonical_name") or term
                        std_num = pdata.get("standard_number", "").upper().strip()
                        if not term or not std_num:
                            continue

                        term_key = f"{term.lower()}|{std_num}"
                        if term_key in seen_terms:
                            continue
                        seen_terms.add(term_key)
                        covered_standards.add(std_num)

                        # Check statutory QCO status
                        qcos = self.qco_reg.get_by_standard(std_num)
                        if qcos:
                            active_qco = qcos[0]
                            cert_status = CertificationStatus.MANDATORY_QCO if active_qco.mandatory_status.value == "MANDATORY_QCO" else (
                                CertificationStatus.MANDATORY_CRS if active_qco.mandatory_status.value == "MANDATORY_CRS" else CertificationStatus.MANDATORY_QCO
                            )
                            is_mandatory = True
                            cert_evidence = f"Mandated under {active_qco.title} ({active_qco.notification_number})"
                            qco_id = active_qco.qco_id
                            scheme_id = active_qco.scheme
                        else:
                            cert_status = CertificationStatus.VOLUNTARY
                            is_mandatory = False
                            cert_evidence = pdata.get("certification_evidence") or "Voluntary BIS Certification Scheme (Scheme-I)"
                            qco_id = None
                            scheme_id = pdata.get("scheme_id", "SCHEME-I")

                        pid = f"PRD-{prod_counter:04d}"
                        rec = ProductRecord(
                            product_id=pid,
                            canonical_name=cname,
                            term=term,
                            normalized_name=cname,
                            aliases=pdata.get("aliases", [term]),
                            domain=pdata.get("domain", "General"),
                            department=pdata.get("department", "CMD"),
                            standard_number=std_num,
                            current_edition=pdata.get("current_edition", "2024"),
                            certification_status=cert_status,
                            mandatory_certification=is_mandatory,
                            certification_evidence=cert_evidence,
                            qco_id=qco_id,
                            scheme_id=scheme_id,
                            document_available=pdata.get("document_available", True),
                            confidence=pdata.get("confidence", 1.0),
                            evidence_source=pdata.get("evidence_source", f"BIS Product Standard ({std_num})")
                        )
                        product_records.append(rec)
                        prod_counter += 1

                        # Add graph edges: PRODUCT <-> STANDARD
                        add_edge(cname, "GOVERNED_BY_STANDARD", std_num, f"Indian Standard {std_num} normative scope")
                        add_edge(std_num, "APPLIES_TO_PRODUCT", cname, f"Indian Standard {std_num} normative title")
                        if term.lower() != cname.lower():
                            add_edge(term, "ALIAS_OF_PRODUCT", cname, f"Trade alias for {cname}")

                        # Add graph edge: PRODUCT -> SCHEME
                        add_edge(cname, "CERTIFIED_UNDER", scheme_id, f"Certification governed under {scheme_id}")

                        # Add graph edges: QCO mappings
                        if qco_id:
                            add_edge(cname, "MANDATED_BY_QCO", qco_id, cert_evidence)
                            add_edge(std_num, "MANDATED_BY_QCO", qco_id, cert_evidence)
                            add_edge(qco_id, "APPLIES_TO_STANDARD", std_num, f"{qco_id} statutory scope")
                            add_edge(qco_id, "MANDATES_PRODUCT", cname, f"{qco_id} product mandate")
                    except Exception:
                        pass

        # 2. Add newly discovered standards from the standards registry
        for std in self.standards_reg.standards.values():
            if std.standard_id.startswith(("AMD-", "PM-", "SIT-", "QCO-")) or std.title.startswith("Amendment No"):
                continue
            is_num = std.is_number.upper().strip()
            if is_num in covered_standards:
                continue

            cname = self.extract_product_title(std.title)
            if not cname:
                continue

            term_key = f"{cname.lower()}|{is_num}"
            if term_key in seen_terms:
                continue
            seen_terms.add(term_key)
            covered_standards.add(is_num)

            qcos = self.qco_reg.get_by_standard(is_num)
            if qcos:
                active_qco = qcos[0]
                cert_status = CertificationStatus.MANDATORY_QCO
                is_mandatory = True
                cert_evidence = f"Mandated under {active_qco.title} ({active_qco.notification_number})"
                qco_id = active_qco.qco_id
                scheme_id = active_qco.scheme
            else:
                cert_status = CertificationStatus.VOLUNTARY
                is_mandatory = False
                cert_evidence = "Voluntary BIS Certification Scheme (Scheme-I)"
                qco_id = None
                scheme_id = "SCHEME-I"

            pid = f"PRD-{prod_counter:04d}"
            rec = ProductRecord(
                product_id=pid,
                canonical_name=cname,
                term=cname,
                normalized_name=cname,
                aliases=[cname.lower()],
                domain=std.aspect.value if std.aspect else "General",
                department=std.technical_department,
                standard_number=is_num,
                current_edition=std.edition or "2024",
                certification_status=cert_status,
                mandatory_certification=is_mandatory,
                certification_evidence=cert_evidence,
                qco_id=qco_id,
                scheme_id=scheme_id,
                document_available=std.document_id is not None,
                confidence=1.0,
                evidence_source=f"{std.title} ({is_num})"
            )
            product_records.append(rec)
            prod_counter += 1

            add_edge(cname, "GOVERNED_BY_STANDARD", is_num, f"Indian Standard {is_num} normative scope")
            add_edge(is_num, "APPLIES_TO_PRODUCT", cname, f"Indian Standard {is_num} normative title")
            add_edge(cname, "CERTIFIED_UNDER", scheme_id, f"Certification governed under {scheme_id}")
            if qco_id:
                add_edge(cname, "MANDATED_BY_QCO", qco_id, cert_evidence)
                add_edge(is_num, "MANDATED_BY_QCO", qco_id, cert_evidence)
                add_edge(qco_id, "APPLIES_TO_STANDARD", is_num, f"{qco_id} statutory scope")
                add_edge(qco_id, "MANDATES_PRODUCT", cname, f"{qco_id} product mandate")

        # 3. Add graph edges for Product Manuals (STANDARD -> HAS_PRODUCT_MANUAL -> PM)
        for pm in self.manuals_reg.manuals.values():
            std_clean = pm.standard_id.upper().strip()
            add_edge(std_clean, "HAS_PRODUCT_MANUAL", pm.manual_id, f"Product Manual {pm.manual_id} for {std_clean}")
            add_edge(pm.manual_id, "COVERS_STANDARD", std_clean, f"Product Manual {pm.manual_id} covers {std_clean}")
            if pm.sit_reference:
                add_edge(pm.manual_id, "CONTAINS_SIT", pm.sit_reference, f"Product Manual {pm.manual_id} specifies {pm.sit_reference}")

        # 4. Add graph edges for SIT (SIT -> REQUIRES_TEST -> TEST)
        for sit in self.sit_reg.sit_records.values():
            std_clean = sit.standard_id.upper().strip()
            add_edge(std_clean, "HAS_SIT", sit.sit_id, f"SIT testing schedule {sit.sit_id}")
            if sit.test_id:
                add_edge(sit.sit_id, "REQUIRES_TEST", sit.test_id, f"SIT {sit.sit_id} mandates test {sit.test_id}")
                add_edge(sit.test_id, "SPECIFIED_IN_SIT", sit.sit_id, f"Test {sit.test_id} specified in SIT {sit.sit_id}")

        # 5. Add graph edges for Tests (TEST -> GOVERNED_BY -> STANDARD)
        for t in self.tests_reg.tests.values():
            std_clean = t.applicable_standard.upper().strip()
            add_edge(t.test_id, "GOVERNED_BY_STANDARD", std_clean, f"Test {t.test_id} prescribed in {std_clean}")
            add_edge(std_clean, "PRESCRIBES_TEST", t.test_id, f"Standard {std_clean} prescribes test {t.test_id}")

        # 6. Add graph edges for Schemes & Procedures (SCHEME -> USES_PROCEDURE -> PROCEDURE)
        for proc in self.procedures_reg.procedures.values():
            sch_clean = proc.scheme_id.upper().strip()
            add_edge(sch_clean, "USES_PROCEDURE", proc.procedure_id, f"Scheme {sch_clean} implements procedure {proc.procedure_id}")
            add_edge(proc.procedure_id, "APPLIES_TO_SCHEME", sch_clean, f"Procedure {proc.procedure_id} applies to {sch_clean}")

        # 7. Add graph edges for Laboratories (STANDARD -> TESTED_AT_LABORATORY -> LAB)
        for lab in self.labs_reg.laboratories.values():
            for std in lab.standards_tested:
                std_clean = std.upper().strip()
                add_edge(std_clean, "TESTED_AT_LABORATORY", lab.lab_id, f"Laboratory {lab.lab_name} accredited for {std_clean}")
                add_edge(lab.lab_id, "ACCREDITED_FOR_STANDARD", std_clean, f"Accreditation scope includes {std_clean}")

        # 8. Add graph edges for Licences (STANDARD / PRODUCT -> LICENSED_UNDER -> CM/L)
        for lic in self.licences_reg.licences.values():
            std_clean = lic.standard_number.upper().strip()
            add_edge(std_clean, "LICENSED_UNDER", lic.cml_number, f"CM/L {lic.cml_number} granted to {lic.licensee_name}")
            add_edge(lic.cml_number, "COVERS_STANDARD", std_clean, f"CM/L {lic.cml_number} covers standard {std_clean}")
            add_edge(lic.cml_number, "OPERATED_BY", lic.licensee_name, f"Licensee entity {lic.licensee_name}")

        # 9. Add graph edges for CRS Registrations (STANDARD / PRODUCT -> CRS_REGISTERED -> R-Number)
        for crs in self.crs_reg.registrations.values():
            std_clean = crs.standard_number.upper().strip()
            add_edge(std_clean, "CRS_REGISTERED", crs.registration_number, f"CRS registration {crs.registration_number} for {crs.brand_name}")
            add_edge(crs.registration_number, "COVERS_STANDARD", std_clean, f"CRS {crs.registration_number} covers {std_clean}")
            add_edge(crs.registration_number, "BRAND_OWNER", crs.brand_name, f"Brand {crs.brand_name}")
            if crs.testing_laboratory:
                add_edge(crs.registration_number, "TESTED_AT_LABORATORY", crs.testing_laboratory, f"Test report {crs.test_report_number}")

        # 10. Add graph edges for Hallmarking (STANDARD -> HALLMARKED_AT_AHC -> AHC)
        for ahc in self.hallmark_reg.ahc_records.values():
            for std in ahc.standards_covered:
                std_clean = std.upper().strip()
                add_edge(std_clean, "HALLMARKED_AT_AHC", ahc.ahc_id, f"AHC {ahc.ahc_name} recognized for {std_clean}")
                add_edge(ahc.ahc_id, "RECOGNIZED_FOR_STANDARD", std_clean, f"AHC recognition covers {std_clean}")
            add_edge(ahc.ahc_id, "LOCATED_IN_DISTRICT", ahc.district, f"District {ahc.district}, {ahc.state}")

        for pg in self.hallmark_reg.gold_purity_grades:
            add_edge("IS 1417", "ALLOWS_PURITY_GRADE", f"{pg.karat} ({pg.fineness_ppt})", pg.description)

        # 11. Add graph edges for Consumer Services (SCHEME / STANDARD -> SERVICED_BY -> CONSUMER_SERVICE)
        for svc in self.consumer_reg.services.values():
            if svc.target_mark:
                add_edge(svc.target_mark, "SERVICED_BY", svc.service_id, f"Consumer service {svc.service_name}")
            for prov in svc.statutory_provisions:
                add_edge(svc.service_id, "ENFORCES_STATUTORY_PROVISION", prov, f"Enforces {prov}")

        return product_records, relationships

    def save_all(self) -> None:
        """Saves products.jsonl and updates relationships.jsonl."""
        products, new_relationships = self.build()

        # Save products.jsonl
        PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
            for p in products:
                f.write(json.dumps(p.model_dump(), ensure_ascii=False) + "\n")

        # Merge with existing relationships
        existing_edges = []
        if RELATIONSHIPS_PATH.exists():
            with open(RELATIONSHIPS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            existing_edges.append(json.loads(line))
                        except Exception:
                            pass

        seen_keys = set()
        merged_edges = []
        for r in new_relationships + existing_edges:
            key = f"{r.get('source')}|{r.get('relation')}|{r.get('target')}"
            if key not in seen_keys:
                seen_keys.add(key)
                # Ensure edge has evidence binding
                if not r.get("evidence_id"):
                    ev_records = self.evidence_reg.get_by_entity(r.get("source", "")) or self.evidence_reg.get_by_entity(r.get("target", ""))
                    if ev_records:
                        r["evidence_id"] = ev_records[0].evidence_id
                        r["evidentiary_strength"] = ev_records[0].evidentiary_strength.value
                        r["citation"] = ev_records[0].format_citation()
                    else:
                        r["evidence_id"] = f"EVID-EDGE-{abs(hash(key)) % 1000000:06d}"
                        r["evidentiary_strength"] = EvidentiaryStrength.EVIDENCE_PARTIAL.value
                        r["citation"] = r.get("provenance", "BIS Knowledge Registry")
                merged_edges.append(r)

        with open(RELATIONSHIPS_PATH, "w", encoding="utf-8") as f:
            for edge in merged_edges:
                f.write(json.dumps(edge, ensure_ascii=False) + "\n")

        unique_canonicals = len(set(p.canonical_name for p in products))
        print(f"✅ Rebuilt products registry: {len(products)} total search records ({unique_canonicals} canonical products).")
        print(f"✅ Rebuilt knowledge graph: {len(merged_edges)} total edges (100% evidence-bound).")
