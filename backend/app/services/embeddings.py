"""Sentence-transformer embedding model loading and encoding utilities.

Provides a cached model loader and convenience functions for encoding
single texts or batches into fixed-size embedding vectors.
"""

import math
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import settings


@lru_cache(maxsize=1)
def load_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence-transformers embedding model.

    Returns:
        A SentenceTransformer instance configured by settings.
    """
    return SentenceTransformer(settings.embedding_model_name)


def encode(texts: list[str]) -> list[list[float]]:
    """Encode a list of texts into embedding vectors.

    Args:
        texts: List of text strings to encode.

    Returns:
        List of embedding vectors as Python lists.
    """
    model = load_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def encode_single(text: str) -> list[float]:
    """Encode a single text string into an embedding vector.

    Args:
        text: The text to encode.

    Returns:
        A single embedding vector.
    """
    model = load_embedding_model()
    return model.encode([text], show_progress_bar=False)[0].tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity in range [0, 1], or 0.0 if either vector is zero.
    """
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)