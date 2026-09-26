from app.agents.hybrid_agent import HybridRAGAgent
from app.agents.multi_step_agent import MultiStepAgent
from app.agents.graph_agent import GraphRAGAgent
from app.agents.vector_only_agent import VectorOnlyAgent

_hybrid_agent = HybridRAGAgent()
_multi_step_agent = MultiStepAgent()
_graph_agent = GraphRAGAgent()
_vector_agent = VectorOnlyAgent()


class ChatService:

    @staticmethod
    def ask(question: str, scope: dict = None, advanced: bool = False) -> dict:
        if advanced:
            return _multi_step_agent.ask(question, scope=scope)
        return _hybrid_agent.ask(question, scope=scope)

    @staticmethod
    def compare(question: str, scope: dict = None) -> dict:
        """Runs the same question through the graph-only agent and the
        vector-only agent, for the chat UI's "why graph" side-by-side
        toggle - the same argument the eval harness's
        compare_retrieval.py makes offline, made interactive."""

        try:
            cypher, _, rows, attempts = _graph_agent.generate_and_run(question, scope=scope)
            graph_answer = _graph_agent.synthesize_answer(question, rows)
        except Exception as e:
            cypher, rows = None, []
            graph_answer = f"The graph agent could not answer this: {e}"

        vector_result = _vector_agent.ask(question)

        return {
            "question": question,
            "graph_answer": graph_answer,
            "graph_cypher": cypher,
            "graph_results": rows,
            "vector_answer": vector_result["answer"],
            "vector_document_matches": vector_result["document_matches"],
        }
