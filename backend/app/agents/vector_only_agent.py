from app.core.llm_client import generate_content
from app.vectorstore.chroma_manager import ChromaManager


class VectorOnlyAgent:
    """Baseline for comparison: answers using ONLY semantic search over
    uploaded documents, no graph access at all. Used to demonstrate what
    a "plain RAG" system (the common alternative to GraphRAG) can and
    cannot answer on this dataset."""

    def ask(self, question: str, n_results: int = 5) -> dict:

        matches = ChromaManager.search(question, n_results=n_results)

        doc_context = (
            "\n---\n".join(
                f"[{item['metadata'].get('filename', 'document')}] {item['text']}"
                for item in matches
            )
            if matches
            else "(no matching documents found)"
        )

        prompt = f"""
You are a document search assistant. Answer the question using ONLY the
document excerpts below - you have no access to any database or
structured records. If the excerpts don't contain the answer, say so
plainly rather than guessing.

Question: {question}

Document excerpts: {doc_context}

Answer:
"""

        answer = generate_content(prompt, purpose="vector_only_synthesis")

        return {
            "question": question,
            "document_matches": matches,
            "answer": answer,
        }
