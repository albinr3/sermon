from __future__ import annotations

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-mpnet-base-v2"
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    embedding = model.encode([text], normalize_embeddings=False)[0]
    return embedding.tolist()
