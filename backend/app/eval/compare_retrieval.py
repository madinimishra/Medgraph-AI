"""Compare three retrieval strategies on the same questions:
graph-only, vector-only, and hybrid - to demonstrate concretely why a
graph is necessary for this problem, rather than just asserting it.

Uses a representative subset of BENCHMARK (not the full 22) to conserve
LLM quota - each question here costs 3x the calls of the main eval.

Usage (from backend/ with venv active):
    python -m app.eval.compare_retrieval
"""

import json

from app.agents.graph_agent import GraphRAGAgent
from app.agents.hybrid_agent import HybridRAGAgent
from app.agents.vector_only_agent import VectorOnlyAgent
from app.eval.benchmark import BENCHMARK
from app.core import observability

# A representative subset: a couple of lookups, a couple of aggregations,
# and all multi-hop questions (the ones that make the "why graph" case).
COMPARE_IDS = [
    "count_patients",
    "mount_auburn_patients",
    "top5_hospitals",
    "hospital_pair_shared_patients",
    "comorbidity_clustering",
    "patient_hospital_mobility",
    "providers_crossing_hospitals",
]


def _answer_contains_expected(answer: str, check: dict) -> bool:
    answer_lower = answer.lower()
    answer_no_commas = answer.replace(",", "")

    if check["type"] == "scalar_equals":
        return str(check["value"]) in answer_no_commas

    if check["type"] == "contains":
        return any(v.lower() in answer_lower for v in check["values"])

    if check["type"] == "min_rows":
        # Can't verify row count from free text - treat any non-refusal
        # answer as a pass for this comparison (best-effort).
        refusal_phrases = ["don't have", "no matching", "cannot answer", "not contain"]
        return not any(p in answer_lower for p in refusal_phrases)

    return False


def run():

    graph_agent = GraphRAGAgent()
    hybrid_agent = HybridRAGAgent()
    vector_agent = VectorOnlyAgent()

    calls_before = observability.get_stats()["call_count"]

    items = [b for b in BENCHMARK if b["id"] in COMPARE_IDS]
    results = []

    for item in items:
        question = item["question"]
        check = item["check"]

        row = {"id": item["id"], "question": question}

        # Graph-only
        try:
            _, _, rows, _ = graph_agent.generate_and_run(question)
            preview = json.dumps(rows[:25], default=str)
            row["graph_pass"] = check["type"] == "scalar_equals" and str(check["value"]) in preview
            if check["type"] == "contains":
                row["graph_pass"] = any(v.lower() in preview.lower() for v in check["values"])
            if check["type"] == "min_rows":
                row["graph_pass"] = len(rows) >= check["value"]
        except Exception:
            row["graph_pass"] = False

        # Vector-only
        try:
            v_result = vector_agent.ask(question)
            row["vector_pass"] = _answer_contains_expected(v_result["answer"], check)
        except Exception:
            row["vector_pass"] = False

        # Hybrid
        try:
            h_result = hybrid_agent.ask(question)
            row["hybrid_pass"] = _answer_contains_expected(h_result["answer"], check)
        except Exception:
            row["hybrid_pass"] = False

        results.append(row)

        print(
            f"{item['id']:32s} graph={'PASS' if row['graph_pass'] else 'FAIL':4s} "
            f"vector={'PASS' if row['vector_pass'] else 'FAIL':4s} "
            f"hybrid={'PASS' if row['hybrid_pass'] else 'FAIL':4s}"
        )

    total = len(results)

    stats_after = observability.get_stats()
    calls_during_run = [
        c for c in stats_after["recent_calls"]
    ][-(stats_after["call_count"] - calls_before):] if stats_after["call_count"] > calls_before else []
    fallback_calls = sum(1 for c in calls_during_run if c["fallback_used"])
    fallback_rate = round(fallback_calls / len(calls_during_run), 2) if calls_during_run else 0.0

    print("\n" + "=" * 60)
    for method in ["graph_pass", "vector_pass", "hybrid_pass"]:
        passed = sum(1 for r in results if r[method])
        print(f"{method}: {passed}/{total} ({round(100 * passed / total, 1)}%)")
    print(
        f"\nfallback model used for {fallback_calls}/{len(calls_during_run)} "
        f"LLM calls this run ({round(fallback_rate * 100, 1)}%)"
    )
    if fallback_rate > 0.3:
        print(
            "WARNING: high fallback rate - the primary model's quota was "
            "likely exhausted mid-run, so these results reflect degraded "
            "model quality, not just retrieval-strategy differences. "
            "Re-run once quota resets for a clean comparison."
        )
    print("=" * 60)

    with open("app/eval/comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {"results": results, "fallback_rate": fallback_rate},
            f, indent=2, default=str
        )

    print("\nFull results written to app/eval/comparison_results.json")

    return results


if __name__ == "__main__":
    run()
