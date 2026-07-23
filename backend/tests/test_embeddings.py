"""Tests for the embeddings service module.

Mocks SentenceTransformer to avoid loading a real model.
"""

import math
from unittest.mock import patch, MagicMock
import numpy as np
from app.services import embeddings


class TestEncode:
    """Tests for the encode function."""

    def test_encode(self):
        """Verify encode calls model.encode with correct texts and returns .tolist()."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        with patch("app.services.embeddings.load_embedding_model", return_value=mock_model):
            result = embeddings.encode(["hello", "world"])
        mock_model.encode.assert_called_once_with(["hello", "world"], show_progress_bar=False)
        assert result == [[0.1, 0.2], [0.3, 0.4]]

    def test_encode_single(self):
        """Verify encode_single wraps text in list and returns first element."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.5, 0.6]])
        with patch("app.services.embeddings.load_embedding_model", return_value=mock_model):
            result = embeddings.encode_single("test")
        mock_model.encode.assert_called_once_with(["test"], show_progress_bar=False)
        assert result == [0.5, 0.6]

    def test_encode_returns_expected_shape(self):
        """Verify encode returns a list of floats matching the mocked array shape."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[1.0, 2.0]])
        with patch("app.services.embeddings.load_embedding_model", return_value=mock_model):
            result = embeddings.encode(["text"])
        assert result == [[1.0, 2.0]]
        assert len(result) == 1
        assert len(result[0]) == 2


class TestCosineSimilarity:
    """Tests for the cosine_similarity function."""

    def test_cosine_similarity_identical(self):
        """Verify identical vectors produce a similarity of 1.0."""
        result = embeddings.cosine_similarity([1, 0, 0], [1, 0, 0])
        assert math.isclose(result, 1.0)

    def test_cosine_similarity_orthogonal(self):
        """Verify orthogonal vectors produce a similarity of 0.0."""
        result = embeddings.cosine_similarity([1, 0, 0], [0, 1, 0])
        assert math.isclose(result, 0.0)

    def test_cosine_similarity_zero_vector(self):
        """Verify a zero vector returns 0.0 similarity."""
        result = embeddings.cosine_similarity([0, 0, 0], [1, 0, 0])
        assert math.isclose(result, 0.0)
