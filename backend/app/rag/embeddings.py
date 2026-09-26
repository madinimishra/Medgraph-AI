from sentence_transformers import SentenceTransformer

from app.core.config import settings

_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)

    return _model


class Embeddings:

    @staticmethod
    def embed_texts(texts: list[str]) -> list[list[float]]:
        model = get_embedding_model()
        return model.encode(texts).tolist()

    @staticmethod
    def embed_query(text: str) -> list[float]:
        model = get_embedding_model()
        return model.encode(text).tolist()
