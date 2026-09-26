"""A real multi-step reasoning agent built on LangGraph - as opposed to
the one-shot "question -> one Cypher query -> answer" flow used by
GraphRAGAgent/HybridRAGAgent for simple questions. This is for
genuinely compound questions (comparisons, multi-part asks) that don't
have a single Cypher query answer: it first decides whether the
question needs to be split into independent sub-questions, runs each
sub-question through the existing GraphRAGAgent, then synthesizes one
combined answer.

This is deliberately a separate, opt-in path (see api/v1/chat.py's
"advanced" flag) rather than the default for every question: most
questions in this system genuinely are single-query lookups, and
routing every one of them through a decomposition step would just add
latency and LLM calls for no benefit.
"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.core.llm_client import generate_content
from app.agents.graph_agent import GraphRAGAgent


class MultiStepState(TypedDict):
    question: str
    scope: dict
    subquestions: list[str]
    sub_results: list[dict]
    answer: str


def _decompose(state: MultiStepState) -> MultiStepState:

    prompt = f"""
You are planning how to answer a question about a hospital knowledge
graph. Decide if this question requires comparing or separately
analyzing more than one distinct group, time period, or entity (e.g.
"compare X between patients over 60 and under 40", "how does A differ
from B") - if so, break it into 2-4 independent, self-contained
sub-questions that could each be answered on their own and then
combined. If the question is already a single, simple lookup, return
it unchanged as the only sub-question.

Return ONLY valid JSON: {{"subquestions": ["...", "..."]}}

Question: {state['question']}
"""

    output = generate_content(prompt, purpose="multi_step_decompose")

    if output.startswith("```"):
        output = output.strip("`")
        if output.startswith("json"):
            output = output[4:]
        output = output.strip()

    try:
        parsed = json.loads(output)
        subquestions = parsed.get("subquestions") or [state["question"]]
    except (json.JSONDecodeError, AttributeError):
        subquestions = [state["question"]]

    return {**state, "subquestions": subquestions[:4]}


def _solve_each(state: MultiStepState) -> MultiStepState:

    agent = GraphRAGAgent()
    sub_results = []
    scope = state.get("scope")

    for subquestion in state["subquestions"]:
        try:
            cypher, _, rows, attempts = agent.generate_and_run(subquestion, scope=scope)
            sub_results.append({
                "subquestion": subquestion,
                "cypher": cypher,
                "rows": rows,
                "attempts": attempts,
                "error": None,
            })
        except Exception as e:
            sub_results.append({
                "subquestion": subquestion,
                "cypher": None,
                "rows": [],
                "attempts": None,
                "error": str(e),
            })

    return {**state, "sub_results": sub_results}


def _synthesize(state: MultiStepState) -> MultiStepState:

    context_blocks = []
    for result in state["sub_results"]:
        if result["error"]:
            context_blocks.append(
                f"Sub-question: {result['subquestion']}\n"
                f"Could not be answered ({result['error']})."
            )
        else:
            preview = json.dumps(result["rows"][:25], default=str, ensure_ascii=False)
            context_blocks.append(
                f"Sub-question: {result['subquestion']}\n"
                f"Results: {preview}"
            )

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are a hospital knowledge assistant. The original question was
broken into sub-questions, each answered separately against a graph
database. Combine these into ONE coherent answer to the original
question - if this was a comparison, state the comparison explicitly
rather than just repeating each sub-answer in isolation. Be concise
and factual, and note if a sub-question could not be answered.

Original question: {state['question']}

Sub-question results:
{context}

Answer:
"""

    answer = generate_content(prompt, purpose="multi_step_synthesize")

    return {**state, "answer": answer}


def _build_graph():
    graph = StateGraph(MultiStepState)

    graph.add_node("decompose", _decompose)
    graph.add_node("solve_each", _solve_each)
    graph.add_node("synthesize", _synthesize)

    graph.add_edge(START, "decompose")
    graph.add_edge("decompose", "solve_each")
    graph.add_edge("solve_each", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


class MultiStepAgent:
    """Decomposes a question into sub-questions, solves each against
    the graph, and synthesizes a combined answer."""

    def __init__(self):
        self._graph = _build_graph()

    def ask(self, question: str, scope: dict = None) -> dict:

        result = self._graph.invoke({
            "question": question,
            "scope": scope,
            "subquestions": [],
            "sub_results": [],
            "answer": "",
        })

        return {
            "question": question,
            "subquestions": result["subquestions"],
            "sub_results": result["sub_results"],
            "answer": result["answer"],
        }
