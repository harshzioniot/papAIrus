"""
Local sentence embeddings for semantic RAG over journal entries.

Uses sentence-transformers/all-MiniLM-L6-v2:
  - 384-d vectors, ~80MB model, runs on CPU at ~50ms/text
  - Normalized output → dot product == cosine similarity
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

_model = None
EMBED_DIM = 384


def load_model():
    global _model
    from sentence_transformers import SentenceTransformer
    logger.info("Loading embedding model...")
    _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    logger.info("Embedding model ready.")


def embed(text: str) -> list[float]:
    """Return a normalized 384-d vector for the given text."""
    if not text or not text.strip():
        return [0.0] * EMBED_DIM
    if _model is None:
        raise RuntimeError("Embedding model not loaded — call load_model() first.")
    vec = _model.encode(text.strip(), normalize_embeddings=True, show_progress_bar=False)
    return vec.tolist()


def cosine_rank(query_vec: list[float], candidates: list[tuple[str, list[float]]], top_k: int = 5, threshold: float = 0.25) -> list[tuple[str, float]]:
    """Return [(id, score), ...] sorted by similarity, filtered by threshold."""
    if not candidates:
        return []
    q = np.asarray(query_vec, dtype=np.float32)
    ids = [c[0] for c in candidates]
    M = np.asarray([c[1] for c in candidates], dtype=np.float32)
    # Vectors are already normalized → dot product == cosine
    scores = M @ q
    order = np.argsort(-scores)
    out = []
    for i in order[:top_k]:
        if scores[i] < threshold:
            break
        out.append((ids[i], float(scores[i])))
    return out
