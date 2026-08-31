import json
from scripts.evaluate_rag import BENCHMARK_CASES
from ai.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

failures = []
for case in BENCHMARK_CASES:
    ans = pipeline.answer_question(
        query=case["query"],
        as_of_date=case.get("as_of_date")
    )
    grounding_pass = all(tok.lower() in ans.answer.lower() for tok in case["expected_tokens"])
    if case["is_refusal"]:
        citations_pass = True
    else:
        citations_pass = len(ans.citations) > 0 and any(c.verified for c in ans.citations)
        if case["expected_standard"]:
            citations_pass = citations_pass and any(case["expected_standard"].lower() in c.standard_number.lower() for c in ans.citations)

    guardrail_pass = ans.guardrail_result.passed
    if not (grounding_pass and citations_pass and guardrail_pass):
        failures.append({
            "id": case["id"],
            "query": case["query"],
            "grounding": grounding_pass,
            "citations": citations_pass,
            "guardrail": guardrail_pass,
            "retrieved_stds": [c.standard_number for c in ans.retrieved_chunks],
            "ans_snippet": ans.answer[:120],
            "guardrail_warnings": ans.guardrail_result.warnings
        })

print(f"Total failures: {len(failures)}")
for f in failures:
    print(f"\n[{f['id']}] Q: {f['query']}")
    print(f"  Grounding: {f['grounding']} | Citations: {f['citations']} | Guardrail: {f['guardrail']}")
    print(f"  Retrieved: {f['retrieved_stds']}")
    print(f"  Ans: {f['ans_snippet']}")
    print(f"  Warnings: {f['guardrail_warnings']}")
