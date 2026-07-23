import json
from unittest.mock import patch
import numpy as np
from app.services.classification import (
    cosine_similarity,
    classify,
)
from app.services.classification_selection import (
    _select_classification_indices,
    _medoid_indices,
    _keyword_boost_indices,
)
from app.constants import CLASSIFICATION_CATEGORIES


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0, abs=0.01)

    def test_opposite_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_partial_similarity(self):
        a = [1.0, 2.0, 3.0]
        b = [2.0, 4.0, 6.0]
        assert cosine_similarity(a, b) == pytest.approx(1.0)


class TestMedoidIndices:
    def test_returns_nearest_to_centroid(self):
        embs = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
        indices = _medoid_indices(embs, top_k=1)
        assert indices == [2]


class TestSelectClassificationIndices:
    def test_hybrid_first_plus_medoid(self):
        texts = ["title", "body1", "body2", "body3", "footer"]
        embs = [[1.0, 0.0], [0.9, 0.1], [0.1, 0.9], [0.0, 1.0], [0.5, 0.5]]
        indices = _select_classification_indices(texts, embs, lead_n=2, medoid_k=1)
        assert indices[0] == 0
        assert indices[1] == 1
        assert len(indices) == 3

    def test_deduplicates_across_primary_and_medoid(self):
        texts = ["header", "middle", "footer"]
        embs = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
        indices = _select_classification_indices(texts, embs, lead_n=2, medoid_k=2)
        assert len(indices) == 3
        assert indices[0] == 0
        assert indices[1] == 1

    def test_no_embeddings_falls_back_to_first_only(self):
        texts = ["a", "b", "c"]
        indices = _select_classification_indices(texts, chunk_embeddings=None, lead_n=2)
        assert indices == [0, 1]

    def test_empty_texts(self):
        indices = _select_classification_indices([], [], lead_n=2)
        assert indices == []

    def test_fewer_chunks_than_lead_n(self):
        texts = ["only"]
        indices = _select_classification_indices(texts, None, lead_n=3)
        assert indices == [0]


class TestKeywordBoostIndices:
    def test_adds_signing_chunks(self):
        texts = ["header text", "signed by John Doe", "other content", "Authorized Representative: Jane"]
        existing = {0}
        extra = _keyword_boost_indices(texts, existing)
        assert 1 in extra
        assert 3 in extra

    def test_respects_max_three(self):
        texts = ["signed", "signature", "executed", "witness", "approved by"]
        existing = set()
        extra = _keyword_boost_indices(texts, existing)
        assert len(extra) <= 3


class TestClassify:
    DEFAULT_LLM_RETURN = {
        "category": "Invoice",
        "confidence": 0.85,
        "reasoning": "Document states INVOICE in title.",
        "title": "INVOICE #123",
        "summary": "An invoice for widgets.",
        "fields": {
            "invoice_number": {"value": "123", "source_chunk": 1},
            "due_date": {"value": "2024-01-15", "source_chunk": 1},
            "total_amount": {"value": "$500", "source_chunk": 1},
            "vendor_name": {"value": "Acme Corp", "source_chunk": 1},
            "invoice_date": {"value": "2024-01-01", "source_chunk": 1},
            "purchase_order_reference": {"value": None, "source_chunk": None},
        },
    }

    @patch("app.services.classification._llm_extract")
    def test_llm_is_always_called(self, mock_llm):
        mock_llm.return_value = self.DEFAULT_LLM_RETURN
        chunk_embs = [[0.9, 0.1], [0.8, 0.2], [0.3, 0.7]]
        chunk_texts = ["INVOICE #123", "Item: Widgets", "Total Due: $500"]
        result = classify(chunk_embs, chunk_texts)
        mock_llm.assert_called_once()
        assert result["category"] == "Invoice"

    @patch("app.services.classification._llm_extract")
    def test_llm_returns_other(self, mock_llm):
        mock_llm.return_value = {
            "category": "Other",
            "confidence": 0.5,
            "reasoning": "Unclear document type.",
            "title": None,
            "summary": None,
            "fields": {},
        }
        chunk_embs = [[0.5, 0.5], [0.5, 0.5]]
        chunk_texts = ["memo content", "more notes"]
        result = classify(chunk_embs, chunk_texts)
        assert result["category"] == "Other"

    @patch("app.services.classification._llm_extract")
    def test_llm_failure_returns_other(self, mock_llm):
        """LLM JSONDecodeError should fall back to category Other with confidence 0.0 and failure message."""
        mock_llm.side_effect = json.JSONDecodeError("bad json", "", 0)
        chunk_embs = [[0.5, 0.5]]
        chunk_texts = ["some text"]
        result = classify(chunk_embs, chunk_texts)
        assert result["category"] == "Other"
        assert result["confidence"] == 0.0
        assert "LLM classification failed" in result["reasoning"]

    @patch("app.services.classification._llm_extract")
    def test_llm_malformed_json_response(self, mock_llm):
        """LLM returning a non-dict (e.g. string) should be caught by the except block and return Other."""
        mock_llm.side_effect = TypeError("the JSON object must be str, bytes or bytearray, not 'int'")
        chunk_embs = [[0.5, 0.5]]
        chunk_texts = ["some text"]
        result = classify(chunk_embs, chunk_texts)
        assert result["category"] == "Other"
        assert result["confidence"] == 0.0
        assert "LLM classification failed" in result["reasoning"]

    @patch("app.services.classification._llm_extract")
    def test_llm_empty_response(self, mock_llm):
        """LLM returning a dict without 'category' key triggers fallback to Other with confidence 0.0."""
        mock_llm.return_value = {}
        chunk_embs = [[0.5, 0.5]]
        chunk_texts = ["some text"]
        result = classify(chunk_embs, chunk_texts)
        assert result["category"] == "Other"
        assert result["confidence"] == 0.0
        assert "LLM classification failed" in result["reasoning"]

    @patch("app.services.classification._llm_extract")
    def test_reasoning_includes_embedding_hint(self, mock_llm):
        mock_llm.return_value = {
            "category": "Contract",
            "confidence": 0.9,
            "reasoning": "Contains binding agreement language.",
            "title": None, "summary": None, "fields": {},
        }
        chunk_embs = [[1.0, 0.0], [1.0, 0.0]]
        chunk_texts = ["This Agreement", "IN WITNESS WHEREOF"]
        result = classify(chunk_embs, chunk_texts)
        assert "Embedding hint:" in result["reasoning"]

    def test_single_chunk_does_not_crash(self):
        chunk_embs = [[0.5, 0.5]]
        chunk_texts = ["some text"]
        with patch("app.services.classification._llm_extract") as mock_llm:
            mock_llm.return_value = {
                "category": "Other",
                "confidence": 0.5,
                "reasoning": "Single chunk.",
                "title": None, "summary": None, "fields": {},
            }
            result = classify(chunk_embs, chunk_texts)
            assert result["category"] == "Other"
            assert "selected_indices" in result
            assert len(result["selected_indices"]) > 0

    def test_fields_resolved_to_page_bbox(self):
        chunk_texts = ["INVOICE #123", "Total Due: $500"]
        chunk_embs = [[0.9, 0.1], [0.3, 0.7]]
        chunk_pages = [[1], [2]]
        chunk_bboxes = [[{"page": 1, "x0": 0, "y0": 0, "x1": 100, "y1": 50}], []]
        with patch("app.services.classification._llm_extract") as mock_llm:
            mock_llm.return_value = self.DEFAULT_LLM_RETURN
            result = classify(chunk_embs, chunk_texts, chunk_pages, chunk_bboxes)
            fields = result["fields"]
            assert fields["invoice_number"]["value"] == "123"
            assert fields["invoice_number"]["chunk_index"] == 0
            assert fields["invoice_number"]["page_numbers"] == [1]
            assert len(fields["invoice_number"]["bbox"]) > 0
            assert fields["purchase_order_reference"]["value"] is None

    def test_source_chunk_null_when_field_null(self):
        chunk_texts = ["INVOICE #123"]
        chunk_embs = [[0.9, 0.1]]
        with patch("app.services.classification._llm_extract") as mock_llm:
            mock_llm.return_value = {
                "category": "Invoice",
                "confidence": 0.9,
                "reasoning": "OK",
                "title": None, "summary": None,
                "fields": {
                    "invoice_number": {"value": None, "source_chunk": None},
                },
            }
            result = classify(chunk_embs, chunk_texts, [[]], [[]])
            assert result["fields"]["invoice_number"]["value"] is None
            assert result["fields"]["invoice_number"]["chunk_index"] is None


class TestHybridContextInPrompt:
    @patch("app.services.classification._llm_extract")
    def test_hybrid_chunks_passed_to_llm(self, mock_llm):
        mock_llm.return_value = {
            "category": "RFP/RFQ", "confidence": 0.9, "reasoning": "",
            "title": None, "summary": None, "fields": {},
        }

        chunk_embs = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5], [0.4, 0.6]]
        chunk_texts = [
            "REQUEST FOR PROPOSAL #123",
            "Scope of Work section",
            "Evaluation criteria and pricing",
            "Terms and conditions boilerplate",
        ]

        classify(chunk_embs, chunk_texts)

        args, _ = mock_llm.call_args
        selected_texts = args[0]
        assert "REQUEST FOR PROPOSAL" in selected_texts[0]
        assert len(selected_texts) >= 2


def test_pairwise_exemplar_similarity():
    from app.services.classification import get_category_embeddings, cosine_similarity
    import numpy as np

    cat_embs = get_category_embeddings()
    centroids = {}
    for cat, ex_vecs in cat_embs.items():
        centroids[cat] = np.mean(ex_vecs, axis=0).tolist()

    cats = CLASSIFICATION_CATEGORIES
    print("\n=== Pairwise category-centroid cosine similarity matrix ===")
    header = f"{'':16s}" + "".join(f"{c[:12]:>12s}" for c in cats)
    print(header)
    for c1 in cats:
        row = f"{c1[:16]:16s}"
        for c2 in cats:
            sim = cosine_similarity(centroids[c1], centroids[c2])
            row += f"{sim:>12.4f}"
        print(row)
    print()

    n = len(cats)
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(centroids[cats[i]], centroids[cats[j]])
            cats_i = cats[i][:12]
            cats_j = cats[j][:12]
            warn = " *** HIGH" if sim > 0.85 else ""
            print(f"  {cats_i:>12s} <-> {cats_j:12s}: {sim:.4f}{warn}")
    print()


import pytest
