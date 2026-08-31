#!/usr/bin/env python3
"""
Comprehensive Phase 4 RAG Benchmark Evaluation.
Audits grounding accuracy, citation verification, guardrail compliance, and adversarial refusals.
"""
import sys
import json
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.rag.pipeline import RAGPipeline

logging.basicConfig(level=logging.WARNING)

BENCHMARK_CASES = [
    {
        "id": "RAG-001",
        "category": "Factual Parameter",
        "query": "What is the minimum insulation resistance for self-ballasted LED lamps?",
        "as_of_date": "2018-01-01",
        "expected_tokens": ["4 MΩ"],
        "expected_standard": "IS 16102",
        "expected_clause": "8",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-002",
        "category": "Test Condition",
        "query": "Under what humidity and temperature conditions is insulation resistance tested?",
        "expected_tokens": ["48 h", "91", "95", "25°C", "35°C"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "8",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-003",
        "category": "Provisional Requirement",
        "query": "What is the torque requirement for GX53 cap?",
        "as_of_date": "2018-01-01",
        "expected_tokens": ["3.0 Nm", "under consideration"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "9.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-004",
        "category": "Exact Technical Identifier",
        "query": "What torque applies to E17 cap?",
        "expected_tokens": ["1.5 Nm", "E17"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "9.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-005",
        "category": "Exact Technical Identifier",
        "query": "What is the torsion moment for B22d cap?",
        "expected_tokens": ["3.0 Nm", "B22d"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "9.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-006",
        "category": "Thermal Limit",
        "query": "What is the maximum cap temperature rise allowed?",
        "expected_tokens": ["120 K"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "10",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-007",
        "category": "Scope & Rating",
        "query": "What is the maximum rated wattage for self-ballasted LED lamps?",
        "expected_tokens": ["60 W"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-008",
        "category": "Sampling & Quality",
        "query": "How many lamps are required in the test batch for whole batch compliance testing?",
        "expected_tokens": ["25 lamps"],
        "expected_standard": "IS 16102 (Part 1)",
        "expected_clause": "4",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-009",
        "category": "Adversarial - Unknown Question",
        "query": "What is the retail market manufacturing cost of an LED lamp in rupees?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "expected_clause": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-010",
        "category": "Adversarial - Outside Scope",
        "query": "Who is the chief executive officer of the Bureau of Indian Standards?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "expected_clause": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-011",
        "category": "Electrical - Ceiling Fans",
        "query": "What is the minimum air delivery for 1200 mm sweep ceiling fans under IS 374 : 2019?",
        "as_of_date": "2020-01-01",
        "expected_tokens": ["210 m³/min"],
        "expected_standard": "IS 374",
        "expected_clause": "8.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-012",
        "category": "Construction - 53 Grade OPC",
        "query": "What is the 28-day minimum compressive strength required for 53 Grade Ordinary Portland Cement under IS 269 : 2015?",
        "expected_tokens": ["53 MPa"],
        "expected_standard": "IS 269",
        "expected_clause": "6.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-013",
        "category": "Food - Packaged Water",
        "query": "What are the microbiological limits for E. coli in packaged drinking water under IS 14543 : 2024?",
        "expected_tokens": ["absent in 250 mL"],
        "expected_standard": "IS 14543",
        "expected_clause": "6.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-014",
        "category": "Safety - Motorcycle Helmets",
        "query": "What is the maximum allowed mass for protective motorcycle helmets under IS 4151 : 2015?",
        "expected_tokens": ["1500 g"],
        "expected_standard": "IS 4151",
        "expected_clause": "6.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-015",
        "category": "Mechanical - Pressure Cookers",
        "query": "What is the hydraulic proof bursting pressure for domestic pressure cookers under IS 2347 : 2017?",
        "expected_tokens": ["3.0 bar"],
        "expected_standard": "IS 2347",
        "expected_clause": "8.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-016",
        "category": "Safety - Protective Footwear",
        "query": "What impact energy must the steel toecap withstand under IS 15298 (Part 2) : 2016?",
        "expected_tokens": ["200 J"],
        "expected_standard": "IS 15298",
        "expected_clause": "5.3.2.2",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-017",
        "category": "Storage - Lithium Batteries",
        "query": "What is the external short circuit temperature requirement for portable secondary lithium cells under IS 16046 (Part 2) : 2018?",
        "expected_tokens": ["55°C"],
        "expected_standard": "IS 16046",
        "expected_clause": "7.3.2",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-018",
        "category": "Revision - Rebar Ductility",
        "query": "What is the minimum percentage elongation for Fe 500D steel bars in the 2024 revision of IS 1786?",
        "expected_tokens": ["16.0%"],
        "expected_standard": "IS 1786",
        "expected_clause": "7.3",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-019",
        "category": "Revision - BLDC Ceiling Fans",
        "query": "What is the air delivery for 1200 mm sweep BLDC ceiling fans under the 2026 edition of IS 374?",
        "expected_tokens": ["220 m³/min"],
        "expected_standard": "IS 374",
        "expected_clause": "8.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-020",
        "category": "Adversarial - Non-Standard Query",
        "query": "Give me the recipe for baking a chocolate fudge cake.",
        "expected_tokens": ["could not find sufficient information"],
        "expected_standard": None,
        "expected_clause": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    # Standard Identification Benchmark Suite (Retrieval & Grounded Standard Identification)
    {
        "id": "RAG-021",
        "category": "Standard Identification - Ceiling Fans",
        "query": "Which BIS standard applies to electric ceiling fans?",
        "expected_tokens": ["IS 374", "Electric Ceiling Fans"],
        "expected_standard": "IS 374",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-022",
        "category": "Standard Identification - Cement",
        "query": "Which BIS standard specifies ordinary Portland cement?",
        "expected_tokens": ["IS 269", "Ordinary Portland Cement"],
        "expected_standard": "IS 269",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-023",
        "category": "Standard Identification - Helmets",
        "query": "Which BIS standard covers protective helmets for motorcycle riders?",
        "expected_tokens": ["IS 4151", "Protective Helmets"],
        "expected_standard": "IS 4151",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-024",
        "category": "Standard Identification - Lithium Batteries",
        "query": "Which BIS standard covers secondary lithium batteries?",
        "expected_tokens": ["IS 16046 (Part 2)", "Secondary Lithium Cells"],
        "expected_standard": "IS 16046 (Part 2)",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-025",
        "category": "Standard Identification - Drinking Water",
        "query": "Which BIS standard specifies packaged drinking water?",
        "expected_tokens": ["IS 14543", "Packaged drinking water"],
        "expected_standard": "IS 14543",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-026",
        "category": "Standard Identification - Pressure Cookers",
        "query": "Which BIS standard covers domestic pressure cookers?",
        "expected_tokens": ["IS 2347", "Domestic pressure cookers"],
        "expected_standard": "IS 2347",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-027",
        "category": "Standard Identification - Safety Footwear",
        "query": "Which BIS standard specifies safety footwear?",
        "expected_tokens": ["IS 15298 (Part 2)", "Safety footwear"],
        "expected_standard": "IS 15298 (Part 2)",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-028",
        "category": "Standard Identification - Steel Bars",
        "query": "Which BIS standard specifies high strength deformed steel bars for concrete reinforcement?",
        "expected_tokens": ["IS 1786", "steel bars"],
        "expected_standard": "IS 1786",
        "expected_clause": "1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-029",
        "category": "Parameter Disambiguation - Fe 500 Yield Stress",
        "query": "What is the minimum yield stress for Fe 500 steel bars?",
        "expected_tokens": ["500.0 MPa", "yield stress"],
        "expected_standard": "IS 1786",
        "expected_clause": "7.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-030",
        "category": "Parameter Disambiguation - Fe 500D Elongation",
        "query": "What is the minimum percentage elongation for Fe 500D steel bars?",
        "expected_tokens": ["16.0%", "elongation"],
        "expected_standard": "IS 1786",
        "expected_clause": "7.3",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-031",
        "category": "Parameter Disambiguation - Water pH",
        "query": "What is the pH requirement for packaged drinking water?",
        "expected_tokens": ["6.5 to 8.5", "pH"],
        "expected_standard": "IS 14543",
        "expected_clause": "4.1",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-032",
        "category": "Adversarial Refusal - Rocket Engines",
        "query": "What is the BIS requirement for rocket engines?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "expected_clause": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-033",
        "category": "Adversarial Refusal - Commercial Price",
        "query": "What is the retail price of an IS 374 compliant ceiling fan?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "expected_clause": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    }
]


def run_benchmark():
    pipeline = RAGPipeline()
    print("=" * 105)
    print("🎯 BIS AI ASSISTANT - PHASE 4 GROUNDED RAG BENCHMARK EVALUATION")
    print("=" * 105)
    print(f"{'ID':<9} | {'Category':<28} | {'Grounding':<10} | {'Citations':<10} | {'Guardrail':<10} | {'Status'}")
    print("-" * 105)

    passed_count = 0
    total = len(BENCHMARK_CASES)

    for case in BENCHMARK_CASES:
        ans = pipeline.answer_question(
            query=case["query"],
            as_of_date=case.get("as_of_date")
        )
        
        # Check token presence
        grounding_pass = all(tok.lower() in ans.answer.lower() for tok in case["expected_tokens"])
        
        # Check citations
        if case["is_refusal"]:
            citations_pass = True
        else:
            citations_pass = len(ans.citations) > 0 and any(c.verified for c in ans.citations)
            if case["expected_standard"]:
                citations_pass = citations_pass and any(case["expected_standard"].lower() in c.standard_number.lower() for c in ans.citations)

        guardrail_pass = ans.guardrail_result.passed

        case_success = grounding_pass and citations_pass and guardrail_pass
        if case_success:
            passed_count += 1

        status_str = "✅ PASS" if case_success else "❌ FAIL"
        print(
            f"{case['id']:<9} | {case['category']:<28} | "
            f"{('✅' if grounding_pass else '❌'):<10} | "
            f"{('✅' if citations_pass else '❌'):<10} | "
            f"{('✅' if guardrail_pass else '❌'):<10} | "
            f"{status_str}"
        )

    print("=" * 105)
    acc = (passed_count / total) * 100
    print(f"📊 BENCHMARK SUMMARY: {passed_count}/{total} PASSED ({acc:.1f}% Accuracy)")
    print("=" * 105)

    if acc < 100.0:
        sys.exit(1)


if __name__ == "__main__":
    run_benchmark()
