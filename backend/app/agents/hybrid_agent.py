import json

from app.core.llm_client import generate_content
from app.agents.graph_agent import GraphRAGAgent
from app.vectorstore.chroma_manager import ChromaManager


class HybridRAGAgent:
    """Combines structured graph traversal (FalkorDB knowledge graph)
    with semantic search over unstructured clinical documents (Chroma)
    to answer a question, merging both sources into one answer."""

    def __init__(self):
        self.graph_agent = GraphRAGAgent()

    def _run_graph(self, question: str, scope: dict = None) -> dict:
        try:
            cypher, _, rows, attempts = self.graph_agent.generate_and_run(question, scope=scope)
            return {
                "cypher": cypher,
                "rows": rows,
                "error": None,
                "attempts": attempts
            }

        except Exception as e:
            return {"cypher": None, "rows": [], "error": str(e), "attempts": None}

    def _run_vector(self, question: str, n_results: int = 5) -> list:
        try:
            return ChromaManager.search(question, n_results=n_results)
        except Exception:
            return []

    def _synthesize(
        self,
        question: str,
        graph_result: dict,
        vector_results: list
    ) -> str:

        graph_context = (
            json.dumps(graph_result["rows"][:25], default=str, ensure_ascii=False)
            if graph_result["rows"]
            else "(no structured graph results found)"
        )

        doc_context = (
            "\n---\n".join(
                f"[{item['metadata'].get('filename', 'document')}] {item['text']}"
                for item in vector_results
            )
            if vector_results
            else "(no matching uploaded documents found)"
        )

        prompt = f"""
You are a hospital knowledge assistant with access to two sources of
truth: (1) a structured patient/hospital knowledge graph, and (2)
free-text hospital documents uploaded by staff, retrieved by semantic
search. Answer the question using BOTH sources where relevant. If a
source has nothing useful for this question, ignore it silently -
do not mention that it was empty unless the question cannot be
answered at all. Be concise and factual. Never invent data that is
not present in either source below.

IMPORTANT: a numeric value of 0 (e.g. a count, total, or average of 0)
IS a real, complete answer - state it confidently (e.g. "0 providers
match this"). Do NOT treat a 0 value as if no data was found. Only say
"no data found" / "no matching data" when the graph results list is
completely EMPTY (no rows at all) AND there are no matching documents -
never because a returned value happens to be 0 or false.

Question: {question}

Structured graph results (JSON): {graph_context}

Matching document excerpts: {doc_context}

Answer:
"""

        return generate_content(prompt, purpose="hybrid_answer_synthesis")

    def ask(self, question: str, scope: dict = None) -> dict:

        graph_result = self._run_graph(question, scope=scope)
        vector_results = self._run_vector(question)

        answer = self._synthesize(question, graph_result, vector_results)

        return {
            "question": question,
            "cypher": graph_result["cypher"],
            "graph_results": graph_result["rows"],
            "graph_error": graph_result["error"],
            "graph_attempts": graph_result["attempts"],
            "document_matches": vector_results,
            "answer": answer,
        }
