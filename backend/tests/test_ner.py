"""Tests for the NER service module.

Mocks spaCy to avoid loading the en_core_web_sm model.
"""

from unittest.mock import patch, MagicMock
from app.services import ner


class TestExtractChunkEntities:
    """Tests for the extract_chunk_entities function."""

    def test_extract_chunk_entities(self):
        """Verify entities are extracted and returned in the expected list-of-lists structure."""
        mock_ent1 = MagicMock()
        mock_ent1.text = "Apple"
        mock_ent1.label_ = "ORG"
        mock_ent2 = MagicMock()
        mock_ent2.text = "100"
        mock_ent2.label_ = "MONEY"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent1, mock_ent2]

        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc

        with patch("app.services.ner._load_nlp", return_value=mock_nlp):
            result = ner.extract_chunk_entities(["Apple earned 100 dollars."])

        assert len(result) == 1
        assert result[0] == [
            {"text": "Apple", "label": "ORG"},
            {"text": "100", "label": "MONEY"},
        ]

    def test_extract_chunk_entities_empty(self):
        """Verify a chunk with no entities returns a nested empty list."""
        mock_doc = MagicMock()
        mock_doc.ents = []

        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc

        with patch("app.services.ner._load_nlp", return_value=mock_nlp):
            result = ner.extract_chunk_entities(["No entities here."])

        assert result == [[]]

    def test_extract_chunk_entities_multiple_chunks(self):
        """Verify each chunk text returns its own entity list."""
        mock_doc1 = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "Google"
        mock_ent1.label_ = "ORG"
        mock_doc1.ents = [mock_ent1]

        mock_doc2 = MagicMock()
        mock_ent2 = MagicMock()
        mock_ent2.text = "2024"
        mock_ent2.label_ = "DATE"
        mock_doc2.ents = [mock_ent2]

        mock_nlp = MagicMock()
        mock_nlp.side_effect = [mock_doc1, mock_doc2]

        with patch("app.services.ner._load_nlp", return_value=mock_nlp):
            result = ner.extract_chunk_entities(["Google announced", "due in 2024"])

        assert len(result) == 2
        assert result[0] == [{"text": "Google", "label": "ORG"}]
        assert result[1] == [{"text": "2024", "label": "DATE"}]


class TestExtractEntityTypes:
    """Tests for the extract_entity_types function."""

    def test_extract_entity_types(self):
        """Verify entity types are returned as a set of label strings."""
        mock_ent1 = MagicMock()
        mock_ent1.label_ = "ORG"
        mock_ent2 = MagicMock()
        mock_ent2.label_ = "MONEY"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent1, mock_ent2]

        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc

        with patch("app.services.ner._load_nlp", return_value=mock_nlp):
            result = ner.extract_entity_types("Apple earned 100 dollars.")

        assert result == {"ORG", "MONEY"}

    def test_extract_entity_types_empty(self):
        """Verify text with no entities returns an empty set."""
        mock_doc = MagicMock()
        mock_doc.ents = []

        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc

        with patch("app.services.ner._load_nlp", return_value=mock_nlp):
            result = ner.extract_entity_types("No entities here.")

        assert result == set()
