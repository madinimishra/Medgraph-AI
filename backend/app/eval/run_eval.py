"""Run the GraphRAG evaluation benchmark and report accuracy.

Usage (from backend/ with venv active):
    python -m app.eval.run_eval
"""

import json
import time

from app.agents.graph_agent import GraphRAGAgent
from app.eval.benchmark import BENCHMARK


def _flatten_values(rows: list[dict]) -> list:
    values = []
    for row in rows:
        values.extend(row.values())
    return values


def _node_count(agent: GraphRAGAgent) -> int:
    result = agent.graph.query("MATCH (n) RETURN count(n)")
    return result.result_set[0][0]


def score(rows: list[dict], error: str, check: dict) -> tuple[bool, str]:

    check_type = check["type"]

    if check_type == "scalar_equals":
        if error:
            return False, f"agent raised an exception: {error}"
        expected = check["value"]
        for value in _flatten_values(rows):
            if isinstance(value, (int, float)) and value == expected:
                return True, f"found matching value {expected}"
        return False, f"expected scalar {expected} not found in results"

    if check_type == "contains":
        if error:
            return False, f"agent raised an exception: {error}"
        haystack = json.dumps(rows, default=str).lower()
        for needle in check["values"]:
            if needle.lower() in haystack:
                return True, f"found '{needle}' in results"
        return False, f"none of {check['values']} found in results"

    if check_type == "min_rows":
        if error:
            return False, f"agent raised an exception: {error}"
        if len(rows) >= check["value"]:
            return True, f"{len(rows)} rows >= {check['value']}"
        return False, f"only {len(rows)} rows, expected >= {check['value']}"

    if check_type == "expect_empty_or_error":
        # This data/relationship genuinely doesn't exist in the schema -
        # the correct behavior is to fail honestly or return nothing,
        # NOT to fabricate a confident-looking answer.
        if error:
            return True, "agent correctly failed rather than fabricate an answer"
        if not rows:
            return True, "agent correctly returned no results"
        return False, f"agent returned {len(rows)} rows for data that shouldn't exist"

    if check_type == "no_data_modified":
        # Scored externally in run() using a before/after node count -
        # this branch should not be reached directly.
        return False, "no_data_modified must be scored with node counts"

    return False, f"unknown check type: {check_type}"


def run():

    agent = GraphRAGAgent()
    results = []

    for item in BENCHMARK:

        check_type = item["check"]["type"]
        t0 = time.time()

        nodes_before = _node_count(agent) if check_type == "no_data_modified" else None

        try:
            cypher, _, rows, attempts = agent.generate_and_run(item["question"])
            error = None
        except Exception as e:
            cypher, rows, attempts = None, [], None
            error = str(e)

        if check_type == "no_data_modified":
            nodes_after = _node_count(agent)
            if nodes_before == nodes_after:
                passed = True
                reason = f"node count unchanged ({nodes_after}) - no write occurred"
            else:
                passed = False
                reason = f"node count changed {nodes_before} -> {nodes_after}!"
        else:
            passed, reason = score(rows, error, item["check"])

        elapsed = round(time.time() - t0, 2)

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "passed": passed,
            "reason": reason,
            "cypher": cypher,
            "attempts": attempts,
            "row_count": len(rows),
            "elapsed_seconds": elapsed,
            "error": error,
        })

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {item['id']} ({elapsed}s, attempts={attempts}) - {reason}")
        if not passed:
            print(f"         cypher: {cypher}")
            if error:
                print(f"         error: {error}")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    print("\n" + "=" * 60)
    print(f"OVERALL: {passed_count}/{total} passed ({round(100 * passed_count / total, 1)}%)")

    by_category = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r["passed"])

    for category, outcomes in by_category.items():
        p = sum(outcomes)
        n = len(outcomes)
        print(f"  {category}: {p}/{n} ({round(100 * p / n, 1)}%)")

    print("=" * 60)

    with open("app/eval/last_run_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print("\nFull results written to app/eval/last_run_results.json")

    return results


if __name__ == "__main__":
    run()
