"""Chunk selection strategies for classification.

Provides functions to select representative document chunks for LLM-based
classification: leading chunks, centroid-medoid chunks, and keyword-boosted
chunks containing signature/execution language.
"""

import numpy as np


def _medoid_indices(chunk_embeddings: list[list[float]], top_k: int = 3) -> list[int]:
    centroid = np.mean(chunk_embeddings, axis=0)
    distances = [np.linalg.norm(np.array(emb, dtype=np.float32) - centroid) for emb in chunk_embeddings]
    nearest_indices = np.argsort(distances)[:top_k]
    return nearest_indices.tolist()


def _select_classification_indices(
    chunk_texts: list[str],
    chunk_embeddings: list[list[float]] | None = None,
    lead_n: int = 3,
    medoid_k: int = 2,
) -> list[int]:
    """Select representative chunk indices for classification.

    Combines the first N chunks (document opening) with medoid chunks
    (representative of the full embedding space).

    Args:
        chunk_texts: All chunk texts.
        chunk_embeddings: Embedding vectors for all chunks.
        lead_n: Number of leading chunks to include.
        medoid_k: Number of medoid chunks to include.

    Returns:
        Deduplicated list of chunk indices.
    """
    primary_indices = list(range(min(lead_n, len(chunk_texts))))

    secondary_indices: list[int] = []
    if chunk_embeddings is not None and len(chunk_embeddings) >= 1:
        medoid_idxs = _medoid_indices(chunk_embeddings, top_k=medoid_k)
        secondary_indices = [i for i in medoid_idxs]

    combined = list(primary_indices)
    for i in secondary_indices:
        if i not in combined:
            combined.append(i)

    return combined


def _keyword_boost_indices(
    chunk_texts: list[str],
    existing_indices: set[int],
) -> list[int]:
    """Find additional chunks containing signature/execution keywords.

    Args:
        chunk_texts: All chunk texts.
        existing_indices: Already-selected indices to skip.

    Returns:
        Up to 3 extra chunk indices containing relevant keywords.
    """
    keywords = [
        "signature", "signed", "authorized representative", "authorized by",
        "executed", "execution", "witness", "agreed", "approved by",
        "in witness whereof", "dated", "effective date",
    ]
    extra: list[int] = []
    for i, ct in enumerate(chunk_texts):
        if i in existing_indices:
            continue
        lower = ct.lower()
        if any(kw in lower for kw in keywords):
            extra.append(i)
            if len(extra) >= 3:
                break
    return extra