"""
Unit Test Suite for Phase 4 Batch F: Evidence Completion & Provenance Binding.
Tests the 6-level evidentiary taxonomy, EvidenceRecord hashing, EvidenceRegistry,
EvidenceGate safety rules, CitationBuilder, ProductChainPolicy, and EvidenceRepairQueue.
"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai.acquisition.provenance.models import (
    EvidenceRecord, EvidentiaryStrength, SourceAuthority, SourceType,
    LocatorType, SourceReliabilityTier, ValidationStatus, SourceFamily
)
from ai.acquisition.provenance.registry import EvidenceRegistry
from ai.acquisition.provenance.binder import ProvenanceBindingEngine
from ai.acquisition.provenance.chain_policy import ProductChainPolicy, get_policy_for_product, CHAIN_POLICIES
from ai.acquisition.provenance.repair_queue import EvidenceRepairQueue, EvidenceRepairItem
from ai.rag.evidence_gate import EvidenceGate, GateDecision, EvidenceEvaluationResult
from ai.rag.citation import CitationBuilder


@pytest.fixture
def sample_verified_evidence():
    return EvidenceRecord(
        evidence_id="EVID-STD-IS_374-MAIN",
        entity_id="IS 374",
        source_family=SourceFamily.STANDARDS,
        source_authority=SourceAuthority.BIS,
        source_type=SourceType.STANDARD_PDF,
        reliability_tier=SourceReliabilityTier.PRIMARY_NORMATIVE,
        document_id="DOC-035",
        citation_title="IS 374 : 2019 Electric Ceiling Fans",
        locator_type=LocatorType.PDF_CLAUSE,
        locator_value="Clause 10.4 (Air Delivery)",
        clause_number="Clause 10.4",
        page_number=8,
        table_figure_id="Table 2",
        verbatim_quote="Air delivery minimum 210 m3/min for 1200 mm sweep.",
        document_sha256="b6280e6ba2600d882ea2b7619e8a309de02cd8675c77fb78acb42f7666f75675",
        content_sha256=EvidenceRecord.compute_sha256("Air delivery minimum 210 m3/min for 1200 mm sweep."),
        effective_date="2019-01-01",
        evidentiary_strength=EvidentiaryStrength.EVIDENCE_VERIFIED,
        is_current_normative=True,
        provenance_url="https://standardsbis.bsbedge.com/is374_2019"
    )


@pytest.fixture
def sample_stale_evidence():
    return EvidenceRecord(
        evidence_id="EVID-STD-IS_374_1979-HISTORICAL",
        entity_id="IS 374:1979",
        source_family=SourceFamily.STANDARDS,
        source_authority=SourceAuthority.BIS,
        source_type=SourceType.STANDARD_PDF,
        reliability_tier=SourceReliabilityTier.PRIMARY_NORMATIVE,
        document_id="DOC-035-OLD",
        citation_title="IS 374 : 1979 Specification for Electric Ceiling Fans",
        locator_type=LocatorType.PDF_CLAUSE,
        locator_value="Clause 8.1",
        clause_number="Clause 8.1",
        page_number=6,
        verbatim_quote="Historical air delivery requirement.",
        effective_date="1979-01-01",
        evidentiary_strength=EvidentiaryStrength.STALE_EVIDENCE,
        is_current_normative=False,
        superseded_by_evidence_id="EVID-STD-IS_374-MAIN"
    )


class TestEvidenceModelAndRegistry:
    def test_evidence_record_sha256_computation(self, sample_verified_evidence):
        assert len(sample_verified_evidence.content_sha256) == 64
        h = EvidenceRecord.compute_sha256("Test text")
        assert len(h) == 64
        assert h == EvidenceRecord.compute_sha256("Test text")

    def test_citation_formatting(self, sample_verified_evidence):
        cit = sample_verified_evidence.format_citation()
        assert "IS 374" in cit
        assert "Clause 10.4" in cit
        assert "Page 8" in cit

    def test_evidence_registry_crud(self, sample_verified_evidence):
        with TemporaryDirectory() as tmp_dir:
            reg_path = Path(tmp_dir) / "evidence.jsonl"
            reg = EvidenceRegistry(registry_file=reg_path)
            assert reg.count() == 0

            reg.register_evidence(sample_verified_evidence)
            assert reg.count() == 1
            assert reg.get_by_id("EVID-STD-IS_374-MAIN") is not None
            
            by_entity = reg.get_by_entity("IS 374")
            assert len(by_entity) == 1
            assert by_entity[0].citation_title == sample_verified_evidence.citation_title

            dist = reg.get_strength_distribution()
            assert dist["EVIDENCE_VERIFIED"] == 1


class TestEvidenceGate:
    def test_verified_evidence_gate_decision(self, sample_verified_evidence):
        gate = EvidenceGate()
        res = gate.evaluate_evidence(sample_verified_evidence)
        assert res.decision == GateDecision.ALLOW_NORMATIVE_CLAIM
        assert res.can_state_normative_value is True
        assert res.can_quote_verbatim is True
        assert res.requires_supersession_warning is False

    def test_stale_evidence_gate_decision(self, sample_stale_evidence):
        gate = EvidenceGate()
        res = gate.evaluate_evidence(sample_stale_evidence)
        assert res.decision == GateDecision.HISTORICAL_CONTEXT_ONLY
        assert res.can_state_normative_value is False
        assert res.requires_supersession_warning is True
        assert "HISTORICAL ONLY" in (res.warning_or_disclaimer or "")

    def test_unverified_entity_abstention(self):
        gate = EvidenceGate()
        results = gate.evaluate_entity("NON_EXISTENT_STANDARD_9999")
        assert len(results) == 1
        assert results[0].decision == GateDecision.REFUSE_UNVERIFIED_CLAIM
        assert results[0].can_state_normative_value is False


class TestCitationBuilder:
    def test_format_inline_and_block(self, sample_verified_evidence):
        builder = CitationBuilder()
        inline = builder.format_inline_citation(sample_verified_evidence)
        assert inline.startswith("[") and inline.endswith("]")
        assert "IS 374" in inline

        block = builder.format_citation_block(sample_verified_evidence)
        assert "**Authority**: BIS" in block or "**Authority**: Bureau of Indian Standards" in block
        assert "**Locator**: Clause 10.4 (Air Delivery)" in block
        assert "**Clause**: Clause 10.4" in block


class TestProductChainPolicy:
    def test_scheme_i_industrial_policy(self):
        policy = get_policy_for_product("IS 1786", "SCHEME-I", is_mandatory=True)
        assert policy.policy_id == "POLICY-SCHEME-I-INDUSTRIAL"
        assert "STANDARD" in policy.required_nodes
        assert "PRODUCT_MANUAL" in policy.required_nodes
        assert "SIT" in policy.required_nodes
        assert "CRS" in policy.excluded_nodes

    def test_scheme_ii_crs_policy(self):
        policy = get_policy_for_product("IS 16046 (Part 2)", "SCHEME-II", is_mandatory=True)
        assert policy.policy_id == "POLICY-SCHEME-II-CRS"
        assert "CRS" in policy.required_nodes
        assert "LICENCE" in policy.excluded_nodes

    def test_scheme_iv_hallmarking_policy(self):
        policy = get_policy_for_product("IS 1417", "SCHEME-IV", is_mandatory=True)
        assert policy.policy_id == "POLICY-SCHEME-IV-HALLMARK"
        assert "HALLMARKING" in policy.required_nodes


class TestEvidenceRepairQueue:
    def test_repair_queue_operations(self):
        with TemporaryDirectory() as tmp_dir:
            q_path = Path(tmp_dir) / "repair_queue.jsonl"
            queue = EvidenceRepairQueue(queue_file=q_path)
            
            queue.enqueue(EvidenceRepairItem(
                item_id="REPAIR-IS-9999",
                entity_id="IS 9999",
                source_family=SourceFamily.STANDARDS,
                evidentiary_strength=EvidentiaryStrength.EVIDENCE_PARTIAL,
                missing_elements=["FULL_TEXT_PDF"],
                priority=2
            ))
            assert len(queue.get_pending()) == 1

            # Complete repair
            queue.complete("REPAIR-IS-9999", "EVID-STD-IS-9999-VERIFIED")
            assert len(queue.get_pending()) == 0
            assert len(queue.get_resolved()) == 1


class TestFullProvenanceBindingPipeline:
    def test_full_binding_execution(self):
        binder = ProvenanceBindingEngine()
        count, stats = binder.bind_all()
        assert count > 1500
        assert stats["EVIDENCE_VERIFIED"] > 800
        assert stats["EVIDENCE_PARTIAL"] > 500
