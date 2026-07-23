"""Tests for the document ingestion pipeline.

Verifies that ``ingest_document`` correctly orchestrates text extraction,
chunking, embedding, entity extraction, and classification while persisting
the results via SQLAlchemy.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Document, Chunk
from app.services.ingestion import ingest_document


@pytest.fixture
def db_session():
    """Yield a SQLAlchemy Session backed by an in-memory SQLite database.

    Creates all tables before yielding the session and drops them after
    the test completes.
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_extraction():
    """Return a standard extraction dictionary for use in test mocks.

    The returned dict mirrors the shape produced by
    ``app.services.pdf_extraction.extract_text_with_spans``.
    """
    return {
        "full_text": "Test document content for procurement RAG system.",
        "page_texts": ["Test document content for procurement RAG system."],
        "raw_page_texts": ["Test document content for procurement RAG system."],
        "page_spans": [(0, 50)],
        "line_records": [],
        "offset_index": {},
    }


def test_ingest_creates_document(mocker, db_session, mock_extraction):
    """Verify that ingest_document creates a Document record with the expected attributes.

    Mocks the extraction, chunking, embedding, entity extraction, and
    classification steps so that only the orchestration logic is tested.
    """
    chunk_texts = [
        ("First chunk.", [1], 0, 12, [0, 0, 100, 50]),
        ("Second chunk.", [1], 13, 26, [0, 50, 100, 100]),
    ]
    embeddings = [[0.1] * 384, [0.2] * 384]

    mocker.patch(
        "app.services.ingestion.extract_text_with_spans",
        return_value=mock_extraction,
    )
    mocker.patch(
        "app.services.ingestion.chunk_text",
        return_value=chunk_texts,
    )
    mocker.patch(
        "app.services.ingestion.encode",
        return_value=embeddings,
    )
    mocker.patch(
        "app.services.ingestion.extract_chunk_entities",
        return_value=[[], []],
    )
    mocker.patch(
        "app.services.ingestion.classify",
        return_value={
            "category": "RFP",
            "confidence": 0.95,
            "reasoning": "Test reasoning.",
            "title": "Test Document",
            "summary": "A test document summary.",
            "fields": {},
            "selected_indices": [],
        },
    )

    doc = ingest_document(
        db=db_session,
        filename="test.pdf",
        pdf_bytes=b"%PDF-1.4...",
        content_hash="abc123",
    )

    assert doc.filename == "test.pdf"
    assert doc.content_hash == "abc123"
    assert doc.status == "ready"
    assert doc.chunk_count == 2
    assert doc.id is not None


def test_ingest_creates_chunks(mocker, db_session, mock_extraction):
    """Verify that ingest_document creates Chunk records with the expected text, index, and embedding."""
    chunk_texts = [
        ("First chunk.", [1], 0, 12, [0, 0, 100, 50]),
        ("Second chunk.", [1], 13, 26, [0, 50, 100, 100]),
    ]
    embeddings = [[0.1] * 384, [0.2] * 384]

    mocker.patch(
        "app.services.ingestion.extract_text_with_spans",
        return_value=mock_extraction,
    )
    mocker.patch(
        "app.services.ingestion.chunk_text",
        return_value=chunk_texts,
    )
    mocker.patch(
        "app.services.ingestion.encode",
        return_value=embeddings,
    )
    mocker.patch(
        "app.services.ingestion.extract_chunk_entities",
        return_value=[[], []],
    )
    mocker.patch(
        "app.services.ingestion.classify",
        return_value={
            "category": "RFP",
            "confidence": 0.95,
            "reasoning": "Test reasoning.",
            "title": "Test Document",
            "summary": "A test document summary.",
            "fields": {},
            "selected_indices": [],
        },
    )

    ingest_document(
        db=db_session,
        filename="test.pdf",
        pdf_bytes=b"%PDF-1.4...",
        content_hash="abc123",
    )

    chunks = db_session.query(Chunk).order_by(Chunk.chunk_index).all()
    assert len(chunks) == 2

    assert chunks[0].text == "First chunk."
    assert chunks[0].chunk_index == 0
    assert chunks[0].embedding == [0.1] * 384

    assert chunks[1].text == "Second chunk."
    assert chunks[1].chunk_index == 1
    assert chunks[1].embedding == [0.2] * 384


def test_ingest_sets_chunk_count(mocker, db_session, mock_extraction):
    """Confirm that chunk_count on the Document matches the number of chunks produced by chunk_text."""
    chunk_texts = [
        ("Single chunk.", [1], 0, 13, [0, 0, 100, 50]),
    ]
    embeddings = [[0.3] * 384]

    mocker.patch(
        "app.services.ingestion.extract_text_with_spans",
        return_value=mock_extraction,
    )
    mocker.patch(
        "app.services.ingestion.chunk_text",
        return_value=chunk_texts,
    )
    mocker.patch(
        "app.services.ingestion.encode",
        return_value=embeddings,
    )
    mocker.patch(
        "app.services.ingestion.extract_chunk_entities",
        return_value=[[]],
    )
    mocker.patch(
        "app.services.ingestion.classify",
        return_value={
            "category": "RFP",
            "confidence": 0.95,
            "reasoning": "Test reasoning.",
            "title": "Test Document",
            "summary": "A test document summary.",
            "fields": {},
            "selected_indices": [],
        },
    )

    doc = ingest_document(
        db=db_session,
        filename="test.pdf",
        pdf_bytes=b"%PDF-1.4...",
        content_hash="abc123",
    )

    assert doc.chunk_count == len(chunk_texts)


def test_ingest_resolves_chunk_id_in_extractions(mocker, db_session, mock_extraction):
    """Ensure that extractions referencing a chunk_index get the resolved chunk_id after flush."""
    chunk_texts = [
        ("Deadline chunk.", [1], 0, 14, [0, 0, 100, 50]),
        ("Budget chunk.", [1], 15, 27, [0, 50, 100, 100]),
    ]
    embeddings = [[0.1] * 384, [0.2] * 384]

    mocker.patch(
        "app.services.ingestion.extract_text_with_spans",
        return_value=mock_extraction,
    )
    mocker.patch(
        "app.services.ingestion.chunk_text",
        return_value=chunk_texts,
    )
    mocker.patch(
        "app.services.ingestion.encode",
        return_value=embeddings,
    )
    mocker.patch(
        "app.services.ingestion.extract_chunk_entities",
        return_value=[[], []],
    )
    mocker.patch(
        "app.services.ingestion.classify",
        return_value={
            "category": "RFP",
            "confidence": 0.95,
            "reasoning": "Test reasoning.",
            "title": "Test Document",
            "summary": "A test document summary.",
            "fields": {
                "deadline": {"chunk_index": 0, "value": "2025-01-01"},
                "budget": {"chunk_index": 1, "value": "100000"},
            },
            "selected_indices": [0, 1],
        },
    )

    doc = ingest_document(
        db=db_session,
        filename="test.pdf",
        pdf_bytes=b"%PDF-1.4...",
        content_hash="abc123",
    )

    chunks = {ch.chunk_index: ch.id for ch in db_session.query(Chunk).all()}

    assert doc.extractions["deadline"]["chunk_id"] == chunks[0]
    assert doc.extractions["deadline"]["chunk_index"] == 0
    assert doc.extractions["budget"]["chunk_id"] == chunks[1]
    assert doc.extractions["budget"]["chunk_index"] == 1


def test_ingest_raises_value_error_for_empty_text(mocker, db_session):
    """Check that a ValueError is raised when the extracted text is empty."""
    empty_extraction = {
        "full_text": "",
        "page_texts": [""],
        "raw_page_texts": [""],
        "page_spans": [(0, 0)],
        "line_records": [],
        "offset_index": {},
    }

    mocker.patch(
        "app.services.ingestion.extract_text_with_spans",
        return_value=empty_extraction,
    )

    with pytest.raises(ValueError, match="PDF contains no extractable text"):
        ingest_document(
            db=db_session,
            filename="empty.pdf",
            pdf_bytes=b"%PDF-1.4...",
            content_hash="empty123",
        )
