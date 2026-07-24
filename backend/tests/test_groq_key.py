"""Tests for GROQ_API_KEY validation at every layer.

Validates that:
- require_groq_key() rejects empty/placeholder keys.
- The upload endpoint returns 503 when the key is missing.
- Groq AuthenticationError is converted to a 400 with a clear message.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from groq import AuthenticationError

from app.main import app
from app.config import require_groq_key, settings

client = TestClient(app)


def _auth_err(mocker):
    """Build a Groq AuthenticationError with the real constructor signature."""
    return AuthenticationError(
        message="Invalid API Key",
        response=mocker.Mock(status_code=401, headers={}),
        body={"error": {"message": "Invalid API Key", "code": "invalid_api_key"}},
    )


class TestRequireGroqKey:
    """Unit tests for the require_groq_key() helper."""

    def test_accepts_valid_key(self):
        with patch("app.config.settings.groq_api_key", "sk-valid-key"):
            require_groq_key()

    def test_rejects_empty_key(self):
        with patch("app.config.settings.groq_api_key", ""):
            with pytest.raises(RuntimeError, match="GROQ_API_KEY is not set"):
                require_groq_key()

    def test_rejects_placeholder_key(self):
        with patch("app.config.settings.groq_api_key", "your_groq_api_key_here"):
            with pytest.raises(RuntimeError, match="GROQ_API_KEY is not set"):
                require_groq_key()


class TestUploadEndpointAuth:
    """Tests that the upload endpoint handles missing/invalid keys properly."""

    def test_upload_returns_503_when_key_missing(self):
        with patch("app.config.settings.groq_api_key", ""):
            response = client.post("/api/documents", files={"file": ("test.pdf", b"fake pdf content", "application/pdf")})
        assert response.status_code == 503
        assert "GROQ_API_KEY" in response.json()["detail"]

    def test_upload_returns_503_when_key_is_placeholder(self):
        with patch("app.config.settings.groq_api_key", "your_groq_api_key_here"):
            response = client.post("/api/documents", files={"file": ("test.pdf", b"fake pdf content", "application/pdf")})
        assert response.status_code == 503
        assert "GROQ_API_KEY" in response.json()["detail"]

    def test_upload_returns_400_on_groq_auth_error(self, mocker):
        mock_groq = mocker.patch("app.services.classification_prompts.Groq")
        mock_groq.return_value.chat.completions.create.side_effect = _auth_err(mocker)
        mocker.patch(
            "app.services.ingestion.extract_text_with_spans",
            return_value={
                "full_text": "test",
                "page_texts": ["test"],
                "raw_page_texts": ["test"],
                "page_spans": [],
            },
        )
        with patch("app.config.settings.groq_api_key", "sk-invalid"):
            response = client.post(
                "/api/documents",
                files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            )
        assert response.status_code == 400
        assert "GROQ_API_KEY" in response.json()["detail"]


class TestChatEndpointAuth:
    """Tests that the chat endpoint handles auth errors properly."""

    def test_chat_returns_503_when_key_missing(self, mocker):
        mocker.patch("app.routers.chat.ChatRepository.get_document", return_value=mocker.Mock(status="ready"))
        with patch("app.config.settings.groq_api_key", ""):
            response = client.post("/api/documents/doc-1/chat", json={"question": "test"})
        assert response.status_code == 503

    def test_chat_returns_400_on_groq_auth_error(self, mocker):
        mock_repo = mocker.patch("app.routers.chat.ChatRepository")
        mock_repo.return_value.get_document.return_value = mocker.Mock(
            status="ready", category="Other", title=None, extractions=None,
        )
        mock_repo.return_value.get_or_create_session.return_value = mocker.Mock(id=1)
        mock_repo.return_value.get_recent_messages.return_value = []

        mock_groq = mocker.patch("app.services.rag.Groq")
        mock_groq.return_value.chat.completions.create.side_effect = _auth_err(mocker)

        with patch("app.config.settings.groq_api_key", "sk-invalid"):
            response = client.post("/api/documents/doc-1/chat", json={"question": "test"})
        assert response.status_code == 400
        assert "GROQ_API_KEY" in response.json()["detail"]
