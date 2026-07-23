import pytest
from app.services.rag import build_prompt, _format_known_fields, _pad_with_boundary_context, BOUNDARY_PAD_CHARS


class TestBuildPrompt:
    def test_context_includes_chunk_texts(self):
        chunks = ["chunk one content", "chunk two content", "chunk three content"]
        messages = build_prompt("test question", chunks)
        system_msg = messages[0]["content"]
        for chunk_text in chunks:
            assert chunk_text in system_msg

    def test_grounding_instruction_present(self):
        messages = build_prompt("test question", ["some context"])
        system_msg = messages[0]["content"]
        assert "based solely on the provided document context" in system_msg
        assert "Do not use any outside knowledge" in system_msg

    def test_user_question_in_messages(self):
        messages = build_prompt("What is this about?", ["context"])
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What is this about?"

    def test_history_included(self):
        history = [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ]
        messages = build_prompt("follow up", ["context"], history)
        assert len(messages) == 4
        assert messages[1] == history[0]
        assert messages[2] == history[1]

    def test_empty_chunks(self):
        messages = build_prompt("question", [])
        system_msg = messages[0]["content"]
        assert "Document context:" in system_msg

    def test_preamble_includes_category(self):
        messages = build_prompt("question", ["ctx"], doc_category="Invoice", doc_title="INV-123")
        system_msg = messages[0]["content"]
        assert "Invoice" in system_msg
        assert "INV-123" in system_msg

    def test_preamble_omitted_when_no_info(self):
        messages = build_prompt("question", ["ctx"])
        system_msg = messages[0]["content"]
        assert system_msg.startswith("You are a procurement document assistant")

    def test_known_fields_included_in_system_prompt(self):
        extractions = {
            "submission_deadline": {"value": "2024-12-31", "chunk_id": 5},
            "total_value": {"value": None, "chunk_id": None},
        }
        known = _format_known_fields(extractions)
        messages = build_prompt("question", ["ctx"], known_fields=known)
        system_msg = messages[0]["content"]
        assert "Known extracted fields" in system_msg
        assert "submission_deadline: 2024-12-31" in system_msg
        assert "total_value" not in system_msg

    def test_known_fields_empty_when_none(self):
        assert _format_known_fields(None) == ""
        assert _format_known_fields({}) == ""
        assert _format_known_fields({"foo": {"value": None}}) == ""

    def test_known_fields_says_may_not_be_relevant(self):
        extractions = {"submission_deadline": {"value": "2024-12-31"}}
        known = _format_known_fields(extractions)
        assert "may or may not be relevant" in known


class TestBoundaryPadding:
    def test_both_neighbors_padded(self):
        prev = "This is the end of the previous chunk with some extra text."
        chunk = "5. The vendor shall deliver all goods within 30 days."
        nxt = "6. Late delivery shall incur a penalty of 1% per day."
        result = _pad_with_boundary_context(chunk, prev, nxt, pad_chars=30)
        assert prev[-30:].split(" ", 1)[-1] in result
        assert chunk in result
        assert nxt[:30].rsplit(" ", 1)[0] in result
        assert result.startswith("...")
        assert result.endswith("...")

    def test_first_chunk_no_prev(self):
        chunk = "1. Introduction to the agreement."
        nxt = "2. The parties agree to the following terms."
        result = _pad_with_boundary_context(chunk, None, nxt, pad_chars=30)
        assert chunk in result
        assert "2." in result
        assert not result.startswith("...")
        # Both None returns chunk unchanged
        result2 = _pad_with_boundary_context(chunk, None, None)
        assert result2 == chunk

    def test_last_chunk_no_next(self):
        prev = "This is the tail of the prior chunk with enough text."
        chunk = "10. This is the final clause of the contract."
        result = _pad_with_boundary_context(chunk, prev, None, pad_chars=30)
        assert chunk in result
        assert "..." in result  # prev leads with ellipsis
        assert not result.endswith("...")

    def test_word_boundary_trimming(self):
        prev = "ends abruptly with some"  # pad_chars=10 → " with some" → split → "with some"
        chunk = "The middle chunk text."
        nxt = "Continues with more text here at the start"
        result = _pad_with_boundary_context(chunk, prev, nxt, pad_chars=10)
        tail = prev[-10:]
        expected_prev_tail = tail.split(" ", 1)[-1] if " " in tail else tail
        assert expected_prev_tail in result
        head = nxt[:10]
        expected_nxt_head = head.rsplit(" ", 1)[0] if " " in head else head
        assert expected_nxt_head in result

    def test_constant_defined(self):
        assert isinstance(BOUNDARY_PAD_CHARS, int)
        assert BOUNDARY_PAD_CHARS > 0


# ─── Chat API Endpoint Tests ───────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_engine
from app.db.models import Base, Document
from sqlalchemy.orm import Session

chat_client = TestClient(app)
integration = pytest.mark.integration
chat_pytest = pytest


def _setup_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def _teardown_db():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def test_chat_history_document_not_found():
    """GET /api/documents/{id}/chat/history returns 404 when document does not exist."""
    _setup_db()
    try:
        response = chat_client.get("/api/documents/nonexistent-id/chat/history")
        assert response.status_code == 404
    finally:
        _teardown_db()


def test_chat_history_empty():
    """GET /api/documents/{id}/chat/history returns empty messages array for a new document."""
    _setup_db()
    try:
        engine = get_engine()
        db = Session(bind=engine)
        doc = Document(id="chat-empty-doc", filename="test.pdf", status="ready")
        db.add(doc)
        db.commit()
        db.close()

        response = chat_client.get("/api/documents/chat-empty-doc/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["messages"] == []
    finally:
        _teardown_db()


@integration
def test_chat_ask_question_document_not_found():
    """POST /api/documents/{id}/chat returns 404 when document does not exist."""
    _setup_db()
    try:
        response = chat_client.post(
            "/api/documents/nonexistent-id/chat",
            json={"question": "What is this about?"},
        )
        assert response.status_code == 404
    finally:
        _teardown_db()


@integration
def test_chat_ask_question_not_ready():
    """POST /api/documents/{id}/chat returns 400 when document status is not 'ready'."""
    _setup_db()
    try:
        engine = get_engine()
        db = Session(bind=engine)
        doc = Document(id="not-ready-doc", filename="proc.pdf", status="processing")
        db.add(doc)
        db.commit()
        db.close()

        response = chat_client.post(
            "/api/documents/not-ready-doc/chat",
            json={"question": "Summarize this."},
        )
        assert response.status_code == 400
    finally:
        _teardown_db()


def test_chat_history_success():
    """GET /api/documents/{id}/chat/history returns messages with role, content, and source_chunks."""
    _setup_db()
    try:
        engine = get_engine()
        db = Session(bind=engine)
        doc = Document(id="chat-hist-doc", filename="hist.pdf", status="ready")
        db.add(doc)
        db.flush()
        from app.db.models import ChatSession, ChatMessage
        session = ChatSession(document_id=doc.id)
        db.add(session)
        db.flush()
        db.add(ChatMessage(session_id=session.id, role="user", content="What is this?", source_chunks=[]))
        db.add(ChatMessage(
            session_id=session.id, role="assistant",
            content="This is a procurement document.",
            source_chunks=[{"id": 1, "text": "chunk text"}],
        ))
        db.commit()
        db.close()

        response = chat_client.get("/api/documents/chat-hist-doc/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "What is this?"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "This is a procurement document."
        assert data["messages"][1]["source_chunks"] == [{"id": 1, "text": "chunk text"}]
    finally:
        _teardown_db()


@integration
def test_chat_ask_question_success():
    """POST /api/documents/{id}/chat returns answer and source_chunks for a ready document."""
    from unittest.mock import patch
    _setup_db()
    try:
        engine = get_engine()
        db = Session(bind=engine)
        doc = Document(id="chat-ok-doc", filename="ok.pdf", status="ready", category="Invoice", title="INV-001")
        db.add(doc)
        db.flush()
        from app.db.models import Chunk
        chunk = Chunk(document_id=doc.id, chunk_index=0, text="Invoice total is $500.", embedding=[0.1]*384)
        db.add(chunk)
        db.commit()
        chunk_id = chunk.id
        db.close()

        with patch("app.routers.chat.answer_question") as mock_answer:
            mock_answer.return_value = {
                "answer": "The total is $500.",
                "source_chunks": [{"id": chunk_id, "text": "Invoice total is $500.", "page_numbers": [], "bbox": []}],
            }
            response = chat_client.post(
                "/api/documents/chat-ok-doc/chat",
                json={"question": "What is the total?"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "The total is $500."
        assert len(data["source_chunks"]) == 1
        assert data["source_chunks"][0]["id"] == chunk.id
    finally:
        _teardown_db()


@integration
def test_chat_with_history_context():
    """POST /api/documents/{id}/chat includes previous messages as context."""
    from unittest.mock import patch
    from datetime import datetime, timedelta, timezone
    _setup_db()
    try:
        engine = get_engine()
        db = Session(bind=engine)
        doc = Document(id="chat-ctx-doc", filename="ctx.pdf", status="ready", category="Contract", title="CT-100")
        db.add(doc)
        db.flush()
        from app.db.models import ChatSession, ChatMessage
        session = ChatSession(document_id=doc.id)
        db.add(session)
        db.flush()
        now = datetime.now(timezone.utc)
        db.add(ChatMessage(session_id=session.id, role="user", content="What is the contract about?", created_at=now - timedelta(seconds=4)))
        db.add(ChatMessage(session_id=session.id, role="assistant", content="It covers service terms.", created_at=now - timedelta(seconds=3)))
        db.add(ChatMessage(session_id=session.id, role="user", content="What are the payment terms?", created_at=now - timedelta(seconds=2)))
        db.add(ChatMessage(session_id=session.id, role="assistant", content="Net 30 days.", created_at=now - timedelta(seconds=1)))
        db.commit()
        db.close()

        with patch("app.routers.chat.answer_question") as mock_answer:
            mock_answer.return_value = {
                "answer": "The late fee is 1.5%.",
                "source_chunks": [],
            }
            response = chat_client.post(
                "/api/documents/chat-ctx-doc/chat",
                json={"question": "What is the late fee?"},
            )
        assert response.status_code == 200
        _, call_kwargs = mock_answer.call_args
        assert call_kwargs["doc_title"] == "CT-100"
        assert call_kwargs["doc_category"] == "Contract"
        history = call_kwargs["history"]
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is the contract about?"
        assert history[-1]["content"] == "Net 30 days."
    finally:
        _teardown_db()
