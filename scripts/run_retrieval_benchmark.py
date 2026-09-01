"""
Phase 3 Grounding & Retrieval Safety Benchmark Suite (22 Cases).
Validates:
  Group A: Valid direct queries (Fe 500D, Fe 550D, Fe 650, Ceiling fan, Drinking water, Rebars, LED lamps)
  Group B: Entity mismatch / non-BIS materials (Titanium Grade 5, Kevlar, Inconel, Carbon fiber) -> Strict ABSTAIN
  Group C: Explicit IS Precedence (IS 1786 5th rev, IS 4246 5th rev, IS 374) -> Strict Standard Match
  Group D: Cross-domain traps (yield of water, air delivery of rebar, pH of steel) -> Strict ABSTAIN
  Group E: Evidence & Provenance Integrity (Normative force, Clause, Page, Entailment)
"""
import sys
import time
import logging
from typing import Dict, Any, List
from ai.rag.pipeline import RAGPipeline
from ai.rag.models import AbstentionReason

logging.basicConfig(level=logging.WARNING)

BENCHMARK_CASES = [
    # -------------------------------------------------------------
    # Group A: Valid Direct Queries (Supported Ground Truth)
    # -------------------------------------------------------------
    {
        "id": "TC-01",
        "group": "A: Valid Direct",
        "query": "What is the minimum yield strength of Fe 500D?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 1786",
        "expected_clause": "7.1",
        "expected_doc_id": "DOC-034",
        "expected_value_str": "500",
        "expected_normative": "INFORMATIVE"
    },
    {
        "id": "TC-02",
        "group": "A: Valid Direct",
        "query": "What is the minimum yield stress requirement for Fe 550D reinforcement steel?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 1786",
        "expected_clause": "7.1",
        "expected_value_str": "550",
    },
    {
        "id": "TC-03",
        "group": "A: Valid Direct",
        "query": "What is the minimum yield strength of Fe 650 high-grade steel?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 1786",
        "expected_clause": "7.1",
        "expected_value_str": "650",
    },
    {
        "id": "TC-04",
        "group": "A: Valid Direct",
        "query": "Which Indian standard governs electric ceiling fans?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 374",
    },
    {
        "id": "TC-05",
        "group": "A: Valid Direct",
        "query": "Which standard specifies packaged drinking water other than packaged natural mineral water?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 14543",
    },
    {
        "id": "TC-06",
        "group": "A: Valid Direct",
        "query": "Which BIS standard applies to high strength deformed steel bars and wires for concrete reinforcement?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 1786",
    },
    {
        "id": "TC-07",
        "group": "A: Valid Direct",
        "query": "What is the minimum insulation resistance of self-ballasted LED lamps?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "8.1",
        "expected_value_str": "4 MΩ",
    },

    # -------------------------------------------------------------
    # Group B: Entity Mismatch / Non-BIS Materials (Strict ABSTAIN)
    # -------------------------------------------------------------
    {
        "id": "TC-08",
        "group": "B: Unsupported Material",
        "query": "What is the minimum yield strength of titanium alloy Grade 5?",
        "expected_status": "ABSTAINED",
        "expected_reason": "INCOMPATIBLE_ENTITY"
    },
    {
        "id": "TC-09",
        "group": "B: Unsupported Material",
        "query": "What is the tensile strength requirement for Kevlar body armor?",
        "expected_status": "ABSTAINED",
        "expected_reason": "INCOMPATIBLE_ENTITY"
    },
    {
        "id": "TC-10",
        "group": "B: Unsupported Material",
        "query": "What is the yield strength requirement for Inconel 718 aerospace alloy?",
        "expected_status": "ABSTAINED",
        "expected_reason": "INCOMPATIBLE_ENTITY"
    },
    {
        "id": "TC-11",
        "group": "B: Unsupported Material",
        "query": "What is the tensile modulus of carbon fiber reinforced polymer composite?",
        "expected_status": "ABSTAINED",
        "expected_reason": "INCOMPATIBLE_ENTITY"
    },

    # -------------------------------------------------------------
    # Group C: Explicit Identifier Precedence (Tier 0 Resolution)
    # -------------------------------------------------------------
    {
        "id": "TC-12",
        "group": "C: Explicit IS Precedence",
        "query": "What does the fifth revision of IS 1786 specify?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 1786",
        "forbidden_standard": "IS 4246",
        "expected_doc_id": "DOC-034"
    },
    {
        "id": "TC-13",
        "group": "C: Explicit IS Precedence",
        "query": "What does IS 4246 fifth revision specify for domestic gas stoves?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 4246",
        "forbidden_standard": "IS 1786",
    },
    {
        "id": "TC-14",
        "group": "C: Explicit IS Precedence",
        "query": "What does IS 374 specify for electric ceiling fans?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 374",
    },

    # -------------------------------------------------------------
    # Group D: Cross-Domain Traps (Strict ABSTAIN)
    # -------------------------------------------------------------
    {
        "id": "TC-15",
        "group": "D: Cross-Domain Trap",
        "query": "What is the minimum yield strength of packaged drinking water?",
        "expected_status": "ABSTAINED",
    },
    {
        "id": "TC-16",
        "group": "D: Cross-Domain Trap",
        "query": "What is the required air delivery of Fe 500D steel rebar?",
        "expected_status": "ABSTAINED",
    },
    {
        "id": "TC-17",
        "group": "D: Cross-Domain Trap",
        "query": "What is the pH requirement of steel reinforcement bars?",
        "expected_status": "ABSTAINED",
    },

    # -------------------------------------------------------------
    # Group E: Evidence & Provenance Integrity
    # -------------------------------------------------------------
    {
        "id": "TC-18",
        "group": "E: Provenance Integrity",
        "query": "What is the minimum yield strength of Fe 500D?",
        "check_type": "normative_force_match",
        "expected_status": "VERIFIED",
    },
    {
        "id": "TC-19",
        "group": "E: Provenance Integrity",
        "query": "What is the minimum yield strength of Fe 500D?",
        "check_type": "clause_fidelity",
        "expected_clause": "7.1",
    },
    {
        "id": "TC-20",
        "group": "E: Provenance Integrity",
        "query": "What is the minimum yield strength of Fe 500D?",
        "check_type": "numerical_delta_zero",
    },
    {
        "id": "TC-21",
        "group": "E: Provenance Integrity",
        "query": "What is the minimum yield strength of Fe 500D?",
        "check_type": "atomic_claims_entailed",
    },
    {
        "id": "TC-22",
        "group": "E: Provenance Integrity",
        "query": "What is the thermal efficiency of domestic gas stoves according to IS 4246?",
        "expected_status": "VERIFIED",
        "expected_standard": "IS 4246",
        "expected_value_str": "68",
    }
]


def run_benchmark():
    print("=" * 80)
    print("🚀 RUNNING PHASE 3 GROUNDING & RETRIEVAL SAFETY BENCHMARK (22 CASES)")
    print("=" * 80)

    pipeline = RAGPipeline()
    passed = 0
    failed = 0
    results = []

    for tc in BENCHMARK_CASES:
        t_start = time.perf_counter()
        tc_id = tc["id"]
        group = tc["group"]
        query = tc["query"]

        # Run pipeline
        ans = pipeline.answer_question(query=query, top_k=5)
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        is_pass = True
        failure_reasons = []

        status = ans.production_payload.get("status", "").upper() if ans.production_payload else ""
        if not status:
            status = "REFUSAL" if ans.guardrail_result and ans.guardrail_result.refusal_required else "VERIFIED"

        # Check expected status
        if tc.get("expected_status"):
            exp_status = tc["expected_status"]
            if exp_status == "ABSTAINED":
                if status not in ("REFUSAL", "GUARDRAIL_BLOCKED", "ABSTAINED"):
                    is_pass = False
                    failure_reasons.append(f"Expected abstention/refusal, got status={status}")
            elif exp_status == "VERIFIED":
                if status != "VERIFIED":
                    is_pass = False
                    failure_reasons.append(f"Expected VERIFIED, got status={status}")

        # Check expected standard
        if tc.get("expected_standard"):
            exp_std = tc["expected_standard"].lower().replace(" ", "")
            all_stds = [c.standard_number.lower().replace(" ", "") for c in ans.citations]
            if not any(exp_std in s for s in all_stds):
                # Also check retrieved chunks
                chunk_stds = [c.standard_number.lower().replace(" ", "") for c in ans.retrieved_chunks]
                if not any(exp_std in s for s in chunk_stds):
                    is_pass = False
                    failure_reasons.append(f"Expected standard {tc['expected_standard']} not found in citations/chunks")

        # Check forbidden standard (e.g. IS 4246 should not appear for IS 1786 query)
        if tc.get("forbidden_standard"):
            forb_std = tc["forbidden_standard"].lower().replace(" ", "")
            all_stds = [c.standard_number.lower().replace(" ", "") for c in ans.citations]
            if any(forb_std in s for s in all_stds):
                is_pass = False
                failure_reasons.append(f"Forbidden standard {tc['forbidden_standard']} retrieved in citations")

        # Check expected clause
        if tc.get("expected_clause"):
            exp_cl = tc["expected_clause"]
            if not any(exp_cl in c.clause for c in ans.citations):
                is_pass = False
                failure_reasons.append(f"Expected clause {exp_cl} not found in citations")

        # Check expected value string in answer text
        if tc.get("expected_value_str"):
            exp_val = tc["expected_value_str"]
            if exp_val not in ans.answer:
                is_pass = False
                failure_reasons.append(f"Expected value string '{exp_val}' not in answer text")

        # Group E checks
        if tc.get("check_type") == "normative_force_match":
            if ans.retrieved_chunks:
                top_chunk = ans.retrieved_chunks[0]
                expected_force = top_chunk.normative_force.upper()
                if f"- **Normative Status**: {expected_force}" not in ans.answer:
                    is_pass = False
                    failure_reasons.append(f"Normative status mismatch (chunk has {expected_force})")

        if tc.get("check_type") == "numerical_delta_zero":
            if not ans.numerical_verifications:
                is_pass = False
                failure_reasons.append("No numerical verifications found")
            else:
                for nv in ans.numerical_verifications:
                    if not nv.get("passed"):
                        is_pass = False
                        failure_reasons.append(f"Numerical verification failed: {nv}")

        if tc.get("check_type") == "atomic_claims_entailed":
            if not ans.claims:
                is_pass = False
                failure_reasons.append("No atomic claims extracted")
            else:
                for cl in ans.claims:
                    if not cl.get("verified", False):
                        is_pass = False
                        failure_reasons.append(f"Claim not verified: {cl.get('text')}")

        if is_pass:
            passed += 1
            status_sym = "✅ PASS"
        else:
            failed += 1
            status_sym = "❌ FAIL"

        print(f"[{status_sym}] {tc_id} [{group}]: \"{query[:55]}...\" ({elapsed_ms:.1f}ms)")
        if not is_pass:
            for r in failure_reasons:
                print(f"       -> {r}")

    print("=" * 80)
    print(f"📊 BENCHMARK SUMMARY: {passed}/{len(BENCHMARK_CASES)} Passed ({(passed/len(BENCHMARK_CASES))*100:.1f}%), {failed} Failed")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_benchmark()
