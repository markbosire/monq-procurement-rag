"""Document classification using embedding similarity and LLM extraction.

Computes category embeddings from exemplar text, selects representative
chunks from a document, scores categories via cosine similarity, and
uses a Groq LLM to determine the final category and extract fields.
"""

import numpy as np
from functools import lru_cache

from app.constants import CATEGORY_EXEMPLARS
from app.services.embeddings import load_embedding_model
from app.services.classification_selection import _select_classification_indices, _keyword_boost_indices
from app.services.classification_prompts import _llm_extract


@lru_cache(maxsize=1)
def get_category_embeddings() -> dict[str, list[list[float]]]:
    """Pre-compute and cache embeddings for all category exemplars.

    Returns:
        Dict mapping category name to a list of exemplar embedding vectors.
    """
    model = load_embedding_model()
    result: dict[str, list[list[float]]] = {}
    for category, exemplars in CATEGORY_EXEMPLARS.items():
        if isinstance(exemplars, str):
            exemplars = [exemplars]
        embeddings = model.encode(exemplars, show_progress_bar=False)
        result[category] = embeddings.tolist()
    return result


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity in range [-1, 1].
    """
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


def classify(
    chunk_embeddings: list[list[float]],
    chunk_texts: list[str],
    chunk_page_numbers: list[list[int]] | None = None,
    chunk_bboxes: list[list[dict]] | None = None,
) -> dict:
    """Classify a document into a procurement category.

    Selects representative chunks, scores categories via embedding similarity,
    and invokes an LLM to produce the final classification and field extractions.

    Args:
        chunk_embeddings: Embedding vectors for all document chunks.
        chunk_texts: Text content of all chunks.
        chunk_page_numbers: Page numbers per chunk (for result annotation).
        chunk_bboxes: Bounding boxes per chunk (for result annotation).

    Returns:
        Dict with keys: category, confidence, reasoning, title, summary,
        fields, selected_indices.
    """
    base_indices = _select_classification_indices(chunk_texts, chunk_embeddings)
    extra_indices = _keyword_boost_indices(chunk_texts, set(base_indices))

    all_indices = base_indices + extra_indices
    selected_texts = [chunk_texts[i] for i in all_indices]

    try:
        doc_centroid = np.mean(chunk_embeddings, axis=0).tolist()
        cat_embs = get_category_embeddings()
        scores: dict[str, float] = {}
        for category, exemplar_embeddings in cat_embs.items():
            best_ex = max(cosine_similarity(doc_centroid, ex_vec) for ex_vec in exemplar_embeddings)
            scores[category] = best_ex
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        emb_hint = "; ".join(f"{c}={s:.3f}" for c, s in ranked[:3])
    except Exception:
        emb_hint = "unavailable"

    try:
        llm_result = _llm_extract(selected_texts, all_indices, chunk_texts)
        if "category" not in llm_result:
            raise ValueError("Missing category in LLM response")
        reasoning = llm_result.get("reasoning", "")
        reasoning += f" | Embedding hint: {emb_hint}"

        raw_fields = llm_result.get("fields", {})

        resolved_fields = {}
        for field_name, field_value in raw_fields.items():
            if isinstance(field_value, dict):
                val = field_value.get("value")
                src_label = field_value.get("source_chunk")
            else:
                val = field_value if field_value not in (None, "", "N/A") else None
                src_label = None

            if val in (None, "", "N/A", "null"):
                resolved_fields[field_name] = {"value": None, "chunk_index": None, "page_numbers": [], "bbox": []}
                continue

            resolved_idx = None
            if src_label is not None:
                label_idx = int(src_label) - 1
                if 0 <= label_idx < len(all_indices):
                    resolved_idx = all_indices[label_idx]

            page_nums = []
            bboxes = []
            if resolved_idx is not None and chunk_page_numbers is not None:
                page_nums = chunk_page_numbers[resolved_idx] if resolved_idx < len(chunk_page_numbers) else []
            if resolved_idx is not None and chunk_bboxes is not None:
                bboxes = chunk_bboxes[resolved_idx] if resolved_idx < len(chunk_bboxes) else []

            resolved_fields[field_name] = {
                "value": val,
                "chunk_index": resolved_idx,
                "page_numbers": page_nums,
                "bbox": bboxes,
            }

        return {
            "category": llm_result.get("category", "Other"),
            "confidence": llm_result.get("confidence", 0.0),
            "reasoning": reasoning,
            "title": llm_result.get("title"),
            "summary": llm_result.get("summary"),
            "fields": resolved_fields,
            "selected_indices": all_indices,
        }
    except Exception:
        return {
            "category": "Other",
            "confidence": 0.0,
            "reasoning": f"LLM classification failed; hybrid context used {len(selected_texts)} chunks. Embedding hint: {emb_hint}",
            "title": None,
            "summary": None,
            "fields": {},
            "selected_indices": all_indices,
        }