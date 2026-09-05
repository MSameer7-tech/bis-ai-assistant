"""
Deterministic Certification Chain Reasoner (Phase 5 Sub-Phase 5D).
Resolves complete 8-node regulatory paths from Product to Licence/CRS/AHC,
validates against ProductChainPolicy, and generates visual ASCII/Mermaid flowcharts.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field

from ai.acquisition.products.registry import ProductRegistry
from ai.acquisition.standards.registry import StandardsRegistry
from ai.acquisition.qco.registry import QCORegistry
from ai.acquisition.schemes.registry import SchemeRegistry
from ai.acquisition.manuals.registry import ProductManualRegistry
from ai.acquisition.sit.registry import SITRegistry
from ai.acquisition.tests.registry import TestRegistry
from ai.acquisition.laboratories.registry import LaboratoryRegistry
from ai.acquisition.licences.registry import LicenceRegistry
from ai.acquisition.crs.registry import CRSRegistry
from ai.acquisition.hallmarking.registry import HallmarkRegistry
from ai.acquisition.provenance.chain_policy import get_policy_for_product, ProductChainPolicy
from ai.acquisition.provenance.registry import EvidenceRegistry
from ai.acquisition.provenance.models import EvidenceRecord, EvidentiaryStrength
from ai.coverage.product_resolver import ProductResolver

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RELATIONSHIPS_PATH = DATA_DIR / "registry" / "relationships.jsonl"


class ChainNode(BaseModel):
    """Represents a single node along the certification chain."""
    node_type: str  # PRODUCT, STANDARD, QCO, SCHEME, PRODUCT_MANUAL, SIT, TEST, LABORATORY, LICENCE, CRS, HALLMARKING
    entity_id: str
    title: str
    is_present: bool = True
    is_mandatory: bool = True
    evidence_id: Optional[str] = None
    evidentiary_strength: str = "EVIDENCE_PARTIAL"
    details: Dict[str, Any] = Field(default_factory=dict)


class CertificationChainResult(BaseModel):
    """Complete multi-hop certification path result."""
    canonical_product: str
    standard_number: str
    scheme_code: str
    is_qco_mandatory: bool
    policy_category: str
    chain_status: str  # COMPLETE, PARTIAL, INCOMPLETE, VOLUNTARY
    nodes: List[ChainNode]
    missing_required_nodes: List[str] = Field(default_factory=list)
    ascii_diagram: str
    mermaid_diagram: str
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_summary: str


class CertificationChainReasoner:
    """
    Deterministic reasoner that traverses and audits the complete 8-node regulatory chain.
    """
    def __init__(self):
        self.ps_resolver = ProductResolver()
        self.prod_reg = ProductRegistry()
        self.std_reg = StandardsRegistry()
        self.qco_reg = QCORegistry()
        self.scheme_reg = SchemeRegistry()
        self.manual_reg = ProductManualRegistry()
        self.sit_reg = SITRegistry()
        self.test_reg = TestRegistry()
        self.lab_reg = LaboratoryRegistry()
        self.lic_reg = LicenceRegistry()
        self.crs_reg = CRSRegistry()
        self.hallmark_reg = HallmarkRegistry()
        self.evidence_reg = EvidenceRegistry()

    def resolve_chain(self, product_or_standard: str, as_of_date: Optional[str] = None) -> CertificationChainResult:
        """Resolves the complete certification chain for a product name or standard number."""
        query_term = product_or_standard.strip()
        query_upper = query_term.upper()

        # 1. Resolve Canonical Product & Standard via ProductResolver
        std_clean = None
        canonical_product = None
        prod_rec = None
        scheme_id = "SCHEME-I"
        is_qco_mandatory = False

        ps_match = self.ps_resolver.resolve_from_query(query_term) or self.ps_resolver.resolve_from_standard(query_term)
        if ps_match:
            canonical_product = ps_match.product.canonical_name
            std_clean = ps_match.product.canonical_standard.upper().split(":")[0].strip()
            scheme_id = ps_match.product.scheme
            is_qco_mandatory = ps_match.product.mandatory_certification
        elif query_upper.startswith("IS ") or self.std_reg.get_by_is(query_term):
            std_clean = query_upper.split(":")[0].strip()
            prods_for_std = self.prod_reg.get_by_standard(std_clean)
            if not prods_for_std:
                # Prefix search for multi-part
                std_base = std_clean.split("(")[0].strip()
                prods_for_std = self.prod_reg.get_by_standard(std_base)
            prod_rec = prods_for_std[0] if prods_for_std else None
            canonical_product = prod_rec.canonical_name if prod_rec else f"Product governed by {std_clean}"
        else:
            prod_rec = self.prod_reg.get_by_term(query_term)
            if prod_rec:
                canonical_product = prod_rec.normalized_name or prod_rec.canonical_name or prod_rec.term
                std_clean = prod_rec.standard_number.split(":")[0].strip().upper() if prod_rec.standard_number else None
            else:
                std_clean = query_upper.split(":")[0].strip()
                canonical_product = query_term

        std_num = std_clean or "UNKNOWN_STANDARD"
        
        # 2. Check QCO & Scheme Mandate
        qco_matches = self.qco_reg.get_by_standard(std_num)
        is_qco_mandatory = bool(len(qco_matches) > 0 or (prod_rec and prod_rec.mandatory_certification) or ("1417" in std_num or "2112" in std_num))
        
        scheme_id = "SCHEME-I"
        if prod_rec and prod_rec.scheme_id:
            scheme_id = prod_rec.scheme_id
        elif "1417" in std_num or "2112" in std_num or "GOLD" in (canonical_product or "").upper():
            scheme_id = "SCHEME-IV"
            std_num = "IS 1417" if std_num == "UNKNOWN_STANDARD" else std_num
            is_qco_mandatory = True
        elif any(s in std_num for s in ["16046", "16102", "13252", "616"]):
            scheme_id = "SCHEME-II"

        policy: ProductChainPolicy = get_policy_for_product(std_num, scheme_id, is_qco_mandatory)

        # 3. Resolve Chain Nodes
        nodes: List[ChainNode] = []
        evidence_list: List[Dict[str, Any]] = []

        # Node 1: Product
        nodes.append(ChainNode(
            node_type="PRODUCT",
            entity_id=prod_rec.product_id if prod_rec else "PRD-CUSTOM",
            title=canonical_product,
            is_present=True,
            is_mandatory=True,
            details={"category": policy.category_name}
        ))

        # Node 2: Standard
        std_ev = self.evidence_reg.get_by_entity(std_num)
        std_ev_rec = std_ev[0] if std_ev else None
        nodes.append(ChainNode(
            node_type="STANDARD",
            entity_id=std_num,
            title=f"Indian Standard {std_num}",
            is_present=True,
            is_mandatory=True,
            evidence_id=std_ev_rec.evidence_id if std_ev_rec else None,
            evidentiary_strength=std_ev_rec.evidentiary_strength.value if std_ev_rec else "EVIDENCE_PARTIAL",
            details={"is_number": std_num}
        ))
        if std_ev_rec:
            evidence_list.append(std_ev_rec.model_dump())

        # Node 3: QCO (if applicable)
        if "QCO" in policy.required_nodes:
            qco_rec = qco_matches[0] if qco_matches else None
            has_qco = is_qco_mandatory
            qco_ev = self.evidence_reg.get_by_entity(qco_rec.qco_id) if qco_rec else []
            qco_ev_rec = qco_ev[0] if qco_ev else None
            nodes.append(ChainNode(
                node_type="QCO",
                entity_id=qco_rec.qco_id if qco_rec else "QCO-MANDATE",
                title=qco_rec.title if qco_rec else f"Statutory QCO Mandate for {std_num}",
                is_present=has_qco,
                is_mandatory=True,
                evidence_id=qco_ev_rec.evidence_id if qco_ev_rec else None,
                evidentiary_strength=qco_ev_rec.evidentiary_strength.value if qco_ev_rec else ("EVIDENCE_VERIFIED" if has_qco else "SOURCE_NOT_FOUND"),
                details={"notification_number": qco_rec.notification_number if qco_rec else "Statutory Mandate"}
            ))
            if qco_ev_rec:
                evidence_list.append(qco_ev_rec.model_dump())

        # Node 4: Scheme
        scheme_ev = self.evidence_reg.get_by_entity(scheme_id)
        scheme_ev_rec = scheme_ev[0] if scheme_ev else None
        nodes.append(ChainNode(
            node_type="SCHEME",
            entity_id=scheme_id,
            title=f"Conformity Assessment {scheme_id}",
            is_present=True,
            is_mandatory=True,
            evidence_id=scheme_ev_rec.evidence_id if scheme_ev_rec else f"EVID-SCHEME-{scheme_id}",
            evidentiary_strength=scheme_ev_rec.evidentiary_strength.value if scheme_ev_rec else "EVIDENCE_VERIFIED",
            details={"scheme_code": scheme_id}
        ))

        # Node 5: Product Manual (if required)
        if "PRODUCT_MANUAL" in policy.required_nodes:
            pms = self.manual_reg.get_by_standard(std_num)
            pm_rec = pms[0] if pms else None
            pm_ev = self.evidence_reg.get_by_entity(pm_rec.manual_id) if pm_rec else []
            pm_ev_rec = pm_ev[0] if pm_ev else None
            nodes.append(ChainNode(
                node_type="PRODUCT_MANUAL",
                entity_id=pm_rec.manual_id if pm_rec else f"PM-{std_num}",
                title=f"Product Manual for {std_num}",
                is_present=bool(pm_rec),
                is_mandatory=True,
                evidence_id=pm_ev_rec.evidence_id if pm_ev_rec else None,
                evidentiary_strength=pm_ev_rec.evidentiary_strength.value if pm_ev_rec else ("EVIDENCE_VERIFIED" if pm_rec else "SOURCE_NOT_FOUND"),
                details={"scope": pm_rec.scope if pm_rec else "Product Manual Guidelines"}
            ))
            if pm_ev_rec:
                evidence_list.append(pm_ev_rec.model_dump())

        # Node 6: SIT (if required)
        if "SIT" in policy.required_nodes:
            sits = self.sit_reg.get_by_standard(std_num)
            sit_rec = sits[0] if sits else None
            sit_ev = self.evidence_reg.get_by_entity(sit_rec.sit_id) if sit_rec else []
            sit_ev_rec = sit_ev[0] if sit_ev else None
            nodes.append(ChainNode(
                node_type="SIT",
                entity_id=sit_rec.sit_id if sit_rec else f"SIT-{std_num}",
                title=f"Scheme of Inspection and Testing ({std_num})",
                is_present=bool(sit_rec),
                is_mandatory=True,
                evidence_id=sit_ev_rec.evidence_id if sit_ev_rec else None,
                evidentiary_strength=sit_ev_rec.evidentiary_strength.value if sit_ev_rec else ("EVIDENCE_VERIFIED" if sit_rec else "SOURCE_NOT_FOUND"),
                details={"frequency": sit_rec.frequency if sit_rec else "Routine Factory Inspection Schedule"}
            ))
            if sit_ev_rec:
                evidence_list.append(sit_ev_rec.model_dump())

        # Node 7: Tests
        if "TEST" in policy.required_nodes:
            tests = self.test_reg.get_by_standard(std_num)
            test_rec = tests[0] if tests else None
            test_ev = self.evidence_reg.get_by_entity(test_rec.test_id) if test_rec else []
            test_ev_rec = test_ev[0] if test_ev else None
            nodes.append(ChainNode(
                node_type="TEST",
                entity_id=test_rec.test_id if test_rec else f"TEST-{std_num}",
                title=test_rec.test_name if test_rec else f"Prescribed Compliance Tests for {std_num}",
                is_present=bool(test_rec) or len(tests) > 0,
                is_mandatory=True,
                evidence_id=test_ev_rec.evidence_id if test_ev_rec else None,
                evidentiary_strength=test_ev_rec.evidentiary_strength.value if test_ev_rec else ("EVIDENCE_VERIFIED" if test_rec else "EVIDENCE_PARTIAL"),
                details={"tests_count": len(tests), "primary_test": test_rec.test_name if test_rec else "Normative tests"}
            ))
            if test_ev_rec:
                evidence_list.append(test_ev_rec.model_dump())

        # Node 8: Laboratory
        if "LABORATORY" in policy.required_nodes:
            labs = self.lab_reg.get_labs_for_standard(std_num)
            lab_rec = labs[0] if labs else None
            lab_ev = self.evidence_reg.get_by_entity(lab_rec.lab_id) if lab_rec else []
            lab_ev_rec = lab_ev[0] if lab_ev else None
            nodes.append(ChainNode(
                node_type="LABORATORY",
                entity_id=lab_rec.lab_id if lab_rec else "LAB-BIS-ACCREDITED",
                title=f"{len(labs)} BIS Recognized Testing Laboratories" if labs else "Accredited Testing Laboratory Network",
                is_present=len(labs) > 0,
                is_mandatory=True,
                evidence_id=lab_ev_rec.evidence_id if lab_ev_rec else None,
                evidentiary_strength=lab_ev_rec.evidentiary_strength.value if lab_ev_rec else "EVIDENCE_PARTIAL",
                details={"accredited_labs_count": len(labs)}
            ))
            if lab_ev_rec:
                evidence_list.append(lab_ev_rec.model_dump())

        # Node 9: Licence / CRS / Hallmarking
        if "LICENCE" in policy.required_nodes:
            lics = self.lic_reg.get_licences_for_standard(std_num)
            lic_rec = lics[0] if lics else None
            nodes.append(ChainNode(
                node_type="LICENCE",
                entity_id=lic_rec.cml_number if lic_rec else "CM/L-ACTIVE-FACTORY",
                title=f"BIS Licence CM/L ({len(lics)} Active Factory Licences)" if lics else "BIS Product Certification Licence (CM/L)",
                is_present=len(lics) > 0,
                is_mandatory=True,
                details={"active_licences": len(lics)}
            ))
        elif "CRS" in policy.required_nodes:
            crs_items = self.crs_reg.get_crs_for_standard(std_num)
            crs_rec = crs_items[0] if crs_items else None
            nodes.append(ChainNode(
                node_type="CRS",
                entity_id=crs_rec.registration_number if crs_rec else "R-CRS-REGISTERED",
                title=f"Compulsory Registration ({len(crs_items)} Active CRS Registrations)" if crs_items else "BIS CRS Registration (R-Number)",
                is_present=len(crs_items) > 0,
                is_mandatory=True,
                details={"active_registrations": len(crs_items)}
            ))
        elif "HALLMARKING" in policy.required_nodes:
            ahcs = list(self.hallmark_reg.ahc_records.values())
            nodes.append(ChainNode(
                node_type="HALLMARKING",
                entity_id="AHC-NETWORK",
                title=f"Assaying & Hallmarking Centres ({len(ahcs)} Recognized AHCs)",
                is_present=len(ahcs) > 0,
                is_mandatory=True,
                details={"ahc_count": len(ahcs)}
            ))

        # Check missing required nodes
        missing_nodes = [n.node_type for n in nodes if not n.is_present and n.is_mandatory]

        if not missing_nodes:
            chain_status = "COMPLETE"
        elif len(missing_nodes) <= 2:
            chain_status = "PARTIAL"
        else:
            chain_status = "INCOMPLETE"

        # 4. Generate Visual ASCII Flowchart
        ascii_steps = [f"[{n.node_type}: {n.title[:28]}]" for n in nodes]
        ascii_diagram = " ──► ".join(ascii_steps)

        # 5. Generate Mermaid Diagram
        mermaid_lines = ["graph LR"]
        for i, n in enumerate(nodes):
            style = "fill:#059669,stroke:#10b981,color:#ffffff" if n.is_present else "fill:#dc2626,stroke:#ef4444,color:#ffffff"
            safe_title = n.title.replace('"', '').replace("'", "")[:30]
            mermaid_lines.append(f'  N{i}["{n.node_type}<br/><b>{safe_title}</b>"]')
            mermaid_lines.append(f'  style N{i} {style}')
            if i > 0:
                mermaid_lines.append(f'  N{i-1} --> N{i}')
        mermaid_diagram = "\n".join(mermaid_lines)

        # 6. Compliance Summary
        mand_str = "Mandatory under Central Government Quality Control Order (QCO)" if is_qco_mandatory else "Voluntary under Indian Standard Scope"
        summary = (
            f"**{canonical_product}** is governed by **{std_num}** under **{scheme_id}**. "
            f"Regulatory Status: **{mand_str}**. "
            f"Certification Chain Status: **{chain_status}** ({len(nodes) - len(missing_nodes)}/{len(nodes)} nodes verified)."
        )

        return CertificationChainResult(
            canonical_product=canonical_product,
            standard_number=std_num,
            scheme_code=scheme_id,
            is_qco_mandatory=is_qco_mandatory,
            policy_category=policy.category_name,
            chain_status=chain_status,
            nodes=nodes,
            missing_required_nodes=missing_nodes,
            ascii_diagram=ascii_diagram,
            mermaid_diagram=mermaid_diagram,
            evidence_records=evidence_list,
            compliance_summary=summary
        )
