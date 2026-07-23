"""Tests for DocumentRepository and ChatRepository.

Uses an in-memory SQLite database to verify all repository methods
against a freshly created schema.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.db.models import Base, Document, Chunk, ChatSession, ChatMessage
from app.db.session import get_engine
from app.repositories.document_repository import DocumentRepository
from app.repositories.chat_repository import ChatRepository


@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite session with all tables.

    Yields:
        Session: A SQLAlchemy session connected to an in-memory database.
    """
    Base.metadata.create_all(bind=get_engine())
    session = Session(bind=get_engine())
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=get_engine())


@pytest.fixture
def sample_document(db_session):
    """Create and return a sample Document with status 'ready'.

    Args:
        db_session: The database session fixture.

    Returns:
        Document: A persisted Document instance.
    """
    doc = Document(
        filename="test_doc.pdf",
        status="ready",
        category="RFQ",
        content_hash="abc123",
    )
    db_session.add(doc)
    db_session.commit()
    return doc


class TestDocumentRepository:
    """Tests for DocumentRepository methods."""

    def test_list_ready(self, db_session, sample_document):
        """Test that list_ready returns only documents with status 'ready'.

        Creates two ready documents and one processing document, then
        verifies only the two ready documents are returned.
        """
        repo = DocumentRepository(db_session)
        ready2 = Document(filename="ready2.pdf", status="ready", category="RFP")
        processing = Document(filename="proc.pdf", status="processing", category="RFQ")
        db_session.add_all([ready2, processing])
        db_session.commit()
        results = repo.list_ready()
        assert len(results) == 2
        assert sample_document in results
        assert ready2 in results

    def test_list_ready_empty(self, db_session):
        """Test that list_ready returns an empty list when no documents exist."""
        repo = DocumentRepository(db_session)
        assert repo.list_ready() == []

    def test_list_ready_ordered_by_created_at_desc(self, db_session):
        """Test that list_ready returns ready documents ordered by created_at descending."""
        repo = DocumentRepository(db_session)
        now = datetime.now(timezone.utc)
        older = Document(
            filename="older.pdf", status="ready", category="RFQ",
            created_at=now - timedelta(hours=2),
        )
        newer = Document(
            filename="newer.pdf", status="ready", category="RFP",
            created_at=now - timedelta(hours=1),
        )
        db_session.add_all([older, newer])
        db_session.commit()
        results = repo.list_ready()
        assert results == [newer, older]

    def test_get_by_id_found(self, db_session, sample_document):
        """Test that get_by_id returns the correct document when it exists."""
        repo = DocumentRepository(db_session)
        result = repo.get_by_id(sample_document.id)
        assert result is not None
        assert result.id == sample_document.id

    def test_get_by_id_not_found(self, db_session):
        """Test that get_by_id returns None when no document matches."""
        repo = DocumentRepository(db_session)
        assert repo.get_by_id("nonexistent-id") is None

    def test_get_by_hash_found(self, db_session, sample_document):
        """Test that get_by_hash returns a ready document matching the content hash."""
        repo = DocumentRepository(db_session)
        result = repo.get_by_hash(sample_document.content_hash)
        assert result is not None
        assert result.id == sample_document.id

    def test_get_by_hash_not_found(self, db_session):
        """Test that get_by_hash returns None for a non-ready document's hash."""
        repo = DocumentRepository(db_session)
        doc = Document(
            filename="proc.pdf", status="processing", content_hash="proc_hash",
        )
        db_session.add(doc)
        db_session.commit()
        assert repo.get_by_hash("proc_hash") is None

    def test_create(self, db_session):
        """Test that create instantiates a Document with given kwargs and sets an id."""
        repo = DocumentRepository(db_session)
        doc = repo.create(
            filename="new_doc.pdf", status="ready", category="ITB",
            content_hash="new_hash",
        )
        db_session.flush()
        assert doc.id is not None
        assert doc.filename == "new_doc.pdf"
        assert doc.status == "ready"
        assert doc.category == "ITB"

    def test_delete_found(self, db_session):
        """Test that delete removes an existing document and returns True."""
        repo = DocumentRepository(db_session)
        doc = Document(filename="delete_me.pdf", status="ready")
        db_session.add(doc)
        db_session.commit()
        assert repo.delete(doc.id) is True
        assert repo.get_by_id(doc.id) is None

    def test_delete_not_found(self, db_session):
        """Test that delete returns False when the document does not exist."""
        repo = DocumentRepository(db_session)
        assert repo.delete("nonexistent-id") is False

    def test_get_chunks_for_document(self, db_session, sample_document):
        """Test that get_chunks_for_document returns all chunks for the given document."""
        repo = DocumentRepository(db_session)
        chunks = [
            Chunk(document_id=sample_document.id, chunk_index=i, text=f"chunk {i}")
            for i in range(3)
        ]
        db_session.add_all(chunks)
        db_session.commit()
        results = repo.get_chunks_for_document(sample_document.id)
        assert len(results) == 3
        assert all(c.document_id == sample_document.id for c in results)

    def test_get_chunk_by_id_found(self, db_session, sample_document):
        """Test that get_chunk_by_id returns the chunk when it exists for the document."""
        repo = DocumentRepository(db_session)
        chunk = Chunk(document_id=sample_document.id, chunk_index=0, text="chunk 0")
        db_session.add(chunk)
        db_session.commit()
        result = repo.get_chunk_by_id(chunk.id, sample_document.id)
        assert result is not None
        assert result.id == chunk.id

    def test_get_chunk_by_id_not_found(self, db_session, sample_document):
        """Test that get_chunk_by_id returns None when the chunk does not exist."""
        repo = DocumentRepository(db_session)
        assert repo.get_chunk_by_id(9999, sample_document.id) is None

    def test_get_chunks_by_ids(self, db_session, sample_document):
        """Test that get_chunks_by_ids returns only chunks matching the given ids."""
        repo = DocumentRepository(db_session)
        chunks = [
            Chunk(document_id=sample_document.id, chunk_index=i, text=f"chunk {i}")
            for i in range(4)
        ]
        db_session.add_all(chunks)
        db_session.commit()
        target_ids = [chunks[0].id, chunks[2].id]
        results = repo.get_chunks_by_ids(target_ids)
        assert len(results) == 2
        result_ids = {c.id for c in results}
        assert result_ids == set(target_ids)

    def test_get_chunks_by_indices(self, db_session, sample_document):
        """Test that get_chunks_by_indices returns chunks matching the given indices."""
        repo = DocumentRepository(db_session)
        chunks = [
            Chunk(document_id=sample_document.id, chunk_index=i, text=f"chunk {i}")
            for i in range(5)
        ]
        db_session.add_all(chunks)
        db_session.commit()
        results = repo.get_chunks_by_indices(sample_document.id, {0, 2, 4})
        assert len(results) == 3
        assert all(c.chunk_index in {0, 2, 4} for c in results)

    def test_get_chunk_index_to_id_map(self, db_session, sample_document):
        """Test that get_chunk_index_to_id_map returns correct index-to-id mapping."""
        repo = DocumentRepository(db_session)
        chunks = [
            Chunk(document_id=sample_document.id, chunk_index=i, text=f"chunk {i}")
            for i in range(3)
        ]
        db_session.add_all(chunks)
        db_session.commit()
        mapping = repo.get_chunk_index_to_id_map(sample_document.id, [0, 1, 2])
        assert mapping == {0: chunks[0].id, 1: chunks[1].id, 2: chunks[2].id}


class TestChatRepository:
    """Tests for ChatRepository methods."""

    def test_get_document_found(self, db_session, sample_document):
        """Test that get_document returns the document when it exists."""
        repo = ChatRepository(db_session)
        result = repo.get_document(sample_document.id)
        assert result is not None
        assert result.id == sample_document.id

    def test_get_document_not_found(self, db_session):
        """Test that get_document returns None when the document does not exist."""
        repo = ChatRepository(db_session)
        assert repo.get_document("nonexistent-id") is None

    def test_get_or_create_session_creates_new(self, db_session, sample_document):
        """Test that get_or_create_session creates a new session when none exist."""
        repo = ChatRepository(db_session)
        session = repo.get_or_create_session(sample_document.id)
        assert session.id is not None
        assert session.document_id == sample_document.id

    def test_get_or_create_session_returns_existing(self, db_session, sample_document):
        """Test that get_or_create_session returns existing session when one exists."""
        repo = ChatRepository(db_session)
        session1 = repo.get_or_create_session(sample_document.id)
        session2 = repo.get_or_create_session(sample_document.id)
        assert session1.id == session2.id

    def test_get_latest_session(self, db_session, sample_document):
        """Test that get_latest_session returns the most recently created session."""
        repo = ChatRepository(db_session)
        now = datetime.now(timezone.utc)
        older = ChatSession(
            document_id=sample_document.id,
            created_at=now - timedelta(hours=2),
        )
        newer = ChatSession(
            document_id=sample_document.id,
            created_at=now - timedelta(hours=1),
        )
        db_session.add_all([older, newer])
        db_session.commit()
        latest = repo.get_latest_session(sample_document.id)
        assert latest is not None
        assert latest.id == newer.id

    def test_get_history_empty(self, db_session, sample_document):
        """Test that get_history returns an empty list when no messages exist."""
        repo = ChatRepository(db_session)
        assert repo.get_history(sample_document.id) == []

    def test_get_history(self, db_session, sample_document):
        """Test that get_history returns all messages in chronological order."""
        repo = ChatRepository(db_session)
        chat_session = repo.get_or_create_session(sample_document.id)
        db_session.commit()
        now = datetime.now(timezone.utc)
        msg1 = ChatMessage(
            session_id=chat_session.id, role="user", content="Hello",
            created_at=now - timedelta(seconds=10),
        )
        msg2 = ChatMessage(
            session_id=chat_session.id, role="assistant", content="Hi",
            created_at=now,
        )
        db_session.add_all([msg1, msg2])
        db_session.commit()
        history = repo.get_history(sample_document.id)
        assert len(history) == 2
        assert history[0].content == "Hello"
        assert history[1].content == "Hi"

    def test_get_recent_messages(self, db_session, sample_document):
        """Test that get_recent_messages returns only the most recent messages up to the limit."""
        repo = ChatRepository(db_session)
        chat_session = repo.get_or_create_session(sample_document.id)
        db_session.commit()
        now = datetime.now(timezone.utc)
        for i in range(12):
            db_session.add(ChatMessage(
                session_id=chat_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                created_at=now + timedelta(seconds=i),
            ))
        db_session.commit()
        recent = repo.get_recent_messages(chat_session.id, limit=10)
        assert len(recent) == 10
        assert recent[0].content == "Message 11"
        assert recent[-1].content == "Message 2"

    def test_add_message(self, db_session, sample_document):
        """Test that add_message persists a chat message with the correct fields."""
        repo = ChatRepository(db_session)
        chat_session = repo.get_or_create_session(sample_document.id)
        db_session.commit()
        msg = repo.add_message(
            session_id=chat_session.id,
            role="user",
            content="What is this?",
            source_chunks=[{"chunk_id": 1, "text": "test"}],
        )
        db_session.commit()
        assert msg.session_id == chat_session.id
        assert msg.role == "user"
        assert msg.content == "What is this?"
        assert msg.source_chunks == [{"chunk_id": 1, "text": "test"}]
        assert msg.id is not None
        fetched = db_session.query(ChatMessage).filter(ChatMessage.id == msg.id).first()
        assert fetched is not None
