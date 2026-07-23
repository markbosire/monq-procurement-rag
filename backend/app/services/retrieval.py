"""Hybrid retrieval pipeline combining BM25, semantic similarity, entity boost, and cross-encoder reranking.

Implements a multi-stage retrieval strategy:
1. BM25 (keyword) and cosine similarity (semantic) scores for all chunks.
2. Fusion with configurable alpha weight and entity-type boost.
3. Top-N candidate selection.
4. Cross-encoder reranking for final results.
"""

import math
import re
from functools import lru_cache
from collections import Counter

from app.config import settings
from app.services.embeddings import encode_single, cosine_similarity

ENTITY_BOOST_FACTOR = 0.15


class BM25:
    """Pure-Python Okapi BM25 implementation for keyword-based scoring."""

    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        """Initialise BM25 with a corpus and tuning parameters.

        Args:
            corpus: List of document texts.
            k1: Term-frequency saturation parameter.
            b: Length normalisation parameter.
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def _build_index(self):
        self.doc_lens: list[int] = []
        self.doc_freqs: list[Counter] = []
        self.df: Counter = Counter()
        self.total_terms = 0

        for doc in self.corpus:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            self.total_terms += len(tokens)
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            self.df.update(freq.keys())

        self.avgdl = self.total_terms / max(len(self.corpus), 1)
        self.N = len(self.corpus)

    def _idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        return math.log((self.N - n + 0.5) / (n + 0.5) + 1.0)

    def score(self, query: str, doc_idx: int) -> float:
        """Compute the BM25 score for a single query-document pair.

        Args:
            query: The query string.
            doc_idx: Index of the document in the corpus.

        Returns:
            BM25 score.
        """
        query_tokens = self._tokenize(query)
        doc_freq = self.doc_freqs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        score = 0.0
        for qt in set(query_tokens):
            tf = doc_freq.get(qt, 0)
            if tf == 0:
                continue
            idf = self._idf(qt)
            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
        return score

    def get_scores(self, query: str) -> list[float]:
        """Compute BM25 scores for all documents against a query.

        Args:
            query: The query string.

        Returns:
            List of BM25 scores, one per document.
        """
        return [self.score(query, i) for i in range(len(self.corpus))]


@lru_cache(maxsize=1)
def _load_reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)


def rerank(query: str, candidates: list[tuple[str, int]], top_k: int = 5) -> list[tuple[str, int]]:
    """Rerank candidate (text, id) pairs using a cross-encoder.

    Args:
        query: The query string.
        candidates: List of (chunk_text, chunk_id) pairs to rerank.
        top_k: Number of top results to return.

    Returns:
        Reranked list of (text, id) pairs, best first.
    """
    if not candidates:
        return []

    model = _load_reranker()
    pairs = [(query, text) for text, _ in candidates]
    scores = model.predict(pairs)

    scored = list(zip(scores, candidates))
    scored.sort(key=lambda x: x[0], reverse=True)

    return [c[1] for c in scored[:top_k]]


def _minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return values
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


@lru_cache(maxsize=1)
def _load_nlp():
    import spacy
    return spacy.load("en_core_web_sm")


def _compute_entity_boosts(question: str, chunks_entities: list[list[dict] | None]) -> list[float]:
    """Compute entity-type overlap boosts for each chunk.

    Args:
        question: The query string.
        chunks_entities: List of entity lists per chunk (or None).

    Returns:
        Boost values per chunk based on entity-type overlap with the question.
    """
    q_doc = _load_nlp()(question[:2000])
    q_types = set(ent.label_ for ent in q_doc.ents)
    if not q_types:
        return [0.0] * len(chunks_entities)

    boosts: list[float] = []
    for chunk_ents in chunks_entities:
        if not chunk_ents:
            boosts.append(0.0)
            continue
        chunk_types = set(e["label"] for e in chunk_ents)
        overlap = q_types & chunk_types
        boosts.append(len(overlap) * ENTITY_BOOST_FACTOR)
    return boosts


def retrieve_chunks(
    db_session,
    document_id: int,
    question: str,
    top_k: int | None = None,
    alpha: float | None = None,
    rerank_top_k: int | None = None,
) -> tuple[list[str], list[int]]:
    """Hybrid retrieval: BM25 + semantic similarity fused, then reranked.

    Steps:
    1. Score all document chunks with BM25 (keyword) and cosine similarity (semantic).
    2. Fuse scores: score = alpha * bm25_norm + (1 - alpha) * semantic_norm + entity_boost.
    3. Take top ``rerank_top_k`` candidates (default 20).
    4. Rerank with a cross-encoder and return final top ``top_k``.

    Args:
        db_session: SQLAlchemy database session.
        document_id: Document UUID.
        question: The user's question.
        top_k: Number of final chunks to return.
        alpha: Blend weight between BM25 and semantic (0 = pure semantic, 1 = pure BM25).
        rerank_top_k: Number of candidates to consider before reranking.

    Returns:
        Tuple of (chunk_texts, chunk_ids).
    """
    k = top_k or settings.top_k_chunks
    alpha_val = alpha if alpha is not None else settings.hybrid_alpha
    candidate_k = rerank_top_k if rerank_top_k is not None else settings.rerank_candidates

    from app.db.models import Chunk

    chunks: list[Chunk] = (
        db_session.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
        .all()
    )

    if not chunks:
        return [], []

    chunk_texts = [c.text for c in chunks]
    question_vector = encode_single(question)

    semantic_scores = [cosine_similarity(question_vector, c.embedding) for c in chunks]

    bm25 = BM25(chunk_texts)
    bm25_scores = bm25.get_scores(question)

    chunks_entities = [c.entities for c in chunks]
    entity_boosts = _compute_entity_boosts(question, chunks_entities)

    sem_norm = _minmax_norm(semantic_scores)
    bm25_norm = _minmax_norm(bm25_scores)
    fused = [
        alpha_val * b + (1 - alpha_val) * s + e
        for b, s, e in zip(bm25_norm, sem_norm, entity_boosts)
    ]

    indexed = list(enumerate(fused))
    indexed.sort(key=lambda x: x[1], reverse=True)
    candidate_indices = [i for i, _ in indexed[:candidate_k]]
    candidates = [(chunks[i].text, chunks[i].id) for i in candidate_indices]

    reranked = rerank(question, candidates, top_k=k)

    texts = [t for t, _ in reranked]
    ids = [cid for _, cid in reranked]
    return texts, ids