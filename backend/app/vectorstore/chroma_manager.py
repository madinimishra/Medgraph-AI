import chromadb

from app.core.config import settings
from app.rag.embeddings import Embeddings

_client = None
_collection = None


def get_collection():
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION
        )

    return _collection


class ChromaManager:

    @staticmethod
    def add_chunks(ids: list[str], texts: list[str], metadatas: list[dict]):

        if not texts:
            return

        collection = get_collection()
        embeddings = Embeddings.embed_texts(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    @staticmethod
    def list_documents() -> list[dict]:
        """One entry per uploaded document (its first chunk), not one
        per chunk - used by the Documents page to show what's already
        been uploaded."""

        collection = get_collection()

        if collection.count() == 0:
            return []

        result = collection.get(
            where={"chunk_index": 0},
            include=["metadatas", "documents"]
        )

        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        entries = [
            {
                **metadatas[i],
                "preview": documents[i][:200] if documents[i] else "",
            }
            for i in range(len(metadatas))
        ]

        entries.sort(key=lambda e: e.get("uploaded_at") or "", reverse=True)

        return entries

    @staticmethod
    def get_document(document_id: str) -> dict:
        """Metadata for a single uploaded document (its first chunk),
        or None if no document with that id exists."""

        collection = get_collection()

        if collection.count() == 0:
            return None

        result = collection.get(
            where={
                "$and": [
                    {"document_id": document_id},
                    {"chunk_index": 0},
                ]
            },
            include=["metadatas"]
        )

        metadatas = result.get("metadatas", [])

        return metadatas[0] if metadatas else None

    @staticmethod
    def search(query: str, n_results: int = 5, where: dict = None):

        collection = get_collection()

        if collection.count() == 0:
            return []

        query_embedding = Embeddings.embed_query(query)

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            where=where
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {
                "text": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i]
            }
            for i in range(len(documents))
        ]
