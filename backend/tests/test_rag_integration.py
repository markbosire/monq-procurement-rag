"""Integration tests for the RAG question-answering pipeline.

Tests the full retrieval-prompt-generation-LLM-response cycle using an
in-memory SQLite database and mocked external dependencies (embedding model,
cross-encoder reranker, spaCy NER, and Groq LLM client) to keep the suite
fast and deterministic.
"""

import sys
from unittest.mock import MagicMock

# Temporarily stub heavy ML/NLP/LLM modules in sys.modules so the app imports
# below do not fail when those packages are absent.  The originals are restored
# immediately after the imports so that other test files in the same session
# still see the real packages.
_ORIG_MODULES: dict[str, object] = {}
for _mod in ("sentence_transformers", "spacy", "groq"):
    _ORIG_MODULES[_mod] = sys.modules.get(_mod)
    sys.modules[_mod] = MagicMock()

import json
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Document, Chunk
from app.services.retrieval import retrieve_chunks
from app.services.rag import answer_question, _format_known_fields

# Restore originals so other test files are not affected.
for _mod, _orig in _ORIG_MODULES.items():
    if _orig is not None:
        sys.modules[_mod] = _orig
    else:
        sys.modules.pop(_mod, None)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database, create all tables, and yield a Session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def document_with_chunks(db_session):
    """Create a Document with three Chunks including embeddings, entities, and page metadata."""
    doc = Document(
        id="test-doc-001",
        filename="test_doc.pdf",
        status="processed",
        category="Contract",
        title="Test Procurement Document",
        extractions={"Vendor": {"value": "Acme Corp"}, "Amount": {"value": "$1M"}},
    )
    db_session.add(doc)

    chunks_data = [
        (
            "The quick brown fox jumps over the lazy dog.",
            [0.1, 0.2, 0.3],
            [{"label": "ANIMAL", "value": "fox"}],
        ),
        (
            "Procurement policy requires competitive bidding.",
            [0.4, 0.5, 0.6],
            [{"label": "LAW", "value": "Policy"}],
        ),
        (
            "Payment terms are net 30 days from invoice.",
            [0.7, 0.8, 0.9],
            [{"label": "MONEY", "value": "net 30"}],
        ),
    ]

    chunks = []
    for i, (text, embedding, entities) in enumerate(chunks_data):
        chunk = Chunk(
            document_id=doc.id,
            chunk_index=i,
            text=text,
            embedding=embedding,
            entities=entities,
            page_numbers=[i + 1],
            bbox=[[0, 0, 100, 100]],
        )
        db_session.add(chunk)
        chunks.append(chunk)

    db_session.commit()
    return doc, chunks


# ---------------------------------------------------------------------------
# retrieve_chunks tests
# ---------------------------------------------------------------------------

def test_retrieve_empty_chunks(db_session):
    """Verify that a document with no chunks returns empty lists."""
    doc = Document(id="empty-doc", filename="empty.pdf", status="processed")
    db_session.add(doc)
    db_session.commit()

    texts, ids = retrieve_chunks(db_session, doc.id, "any question")
    assert texts == []
    assert ids == []


def test_retrieve_single_chunk(db_session):
    """Verify that a document with one chunk returns that single chunk."""
    doc = Document(id="single-doc", filename="single.pdf", status="processed")
    db_session.add(doc)
    chunk = Chunk(
        document_id=doc.id,
        chunk_index=0,
        text="Only chunk in the document.",
        embedding=[0.5, 0.5, 0.5],
        entities=[],
    )
    db_session.add(chunk)
    db_session.commit()

    with (
        patch("app.services.retrieval._load_reranker") as mock_reranker,
        patch("app.services.retrieval.encode_single") as mock_encode,
        patch("app.services.retrieval.cosine_similarity") as mock_cos,
        patch("app.services.retrieval._load_nlp") as mock_nlp,
    ):
        mock_model = MagicMock()
        mock_model.predict.return_value = [1.0]
        mock_reranker.return_value = mock_model

        mock_encode.return_value = [1.0, 0.0, 0.0]
        mock_cos.return_value = 1.0

        mock_nlp_model = MagicMock()
        mock_nlp_model.return_value.ents = []
        mock_nlp.return_value = mock_nlp_model

        texts, ids = retrieve_chunks(db_session, doc.id, "test query")

    assert len(texts) == 1
    assert texts[0] == "Only chunk in the document."
    assert ids[0] == chunk.id


def test_retrieve_alpha_0_pure_semantic(db_session, document_with_chunks):
    """Verify that alpha=0 ignores BM25 and ranks purely by semantic similarity."""
    doc, chunks = document_with_chunks

    with (
        patch("app.services.retrieval._load_reranker") as mock_reranker,
        patch("app.services.retrieval.encode_single") as mock_encode,
        patch("app.services.retrieval.cosine_similarity") as mock_cos,
        patch("app.services.retrieval._load_nlp") as mock_nlp,
    ):
        mock_model = MagicMock()
        mock_model.predict.return_value = [1.0, 0.5, 0.0]
        mock_reranker.return_value = mock_model

        mock_encode.return_value = [1.0, 0.0, 0.0]
        mock_cos.side_effect = [0.9, 0.5, 0.1]

        mock_nlp_model = MagicMock()
        mock_nlp_model.return_value.ents = []
        mock_nlp.return_value = mock_nlp_model

        texts, ids = retrieve_chunks(db_session, doc.id, "fox quick", alpha=0)

    assert len(texts) == 3
    assert texts[0] == chunks[0].text
    assert ids[0] == chunks[0].id


def test_retrieve_alpha_1_pure_bm25(db_session, document_with_chunks):
    """Verify that alpha=1 ignores semantic similarity and ranks purely by BM25."""
    doc, chunks = document_with_chunks

    with (
        patch("app.services.retrieval._load_reranker") as mock_reranker,
        patch("app.services.retrieval.encode_single") as mock_encode,
        patch("app.services.retrieval.cosine_similarity") as mock_cos,
        patch("app.services.retrieval._load_nlp") as mock_nlp,
    ):
        mock_model = MagicMock()
        mock_model.predict.return_value = [1.0, 0.5, 0.0]
        mock_reranker.return_value = mock_model

        mock_encode.return_value = [1.0, 0.0, 0.0]
        mock_cos.return_value = 0.0

        mock_nlp_model = MagicMock()
        mock_nlp_model.return_value.ents = []
        mock_nlp.return_value = mock_nlp_model

        texts, ids = retrieve_chunks(db_session, doc.id, "procurement bidding", alpha=1)

    assert len(texts) == 3
    assert texts[0] == chunks[1].text
    assert ids[0] == chunks[1].id


# ---------------------------------------------------------------------------
# answer_question tests
# ---------------------------------------------------------------------------

def test_answer_question_success(db_session, document_with_chunks):
    """Verify a successful RAG round-trip returns the parsed answer and resolved source chunks."""
    doc, chunks = document_with_chunks

    with (
        patch("app.services.rag.Groq") as mock_groq_cls,
        patch("app.services.rag.retrieve_chunks") as mock_retrieve,
    ):
        mock_retrieve.return_value = (
            [chunks[0].text, chunks[1].text],
            [chunks[0].id, chunks[1].id],
        )

        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value.choices[0].message.content = json.dumps(
            {"answer": "The fox jumps over the lazy dog.", "sources": [1]}
        )
        mock_groq_cls.return_value = mock_groq

        result = answer_question(
            db_session, doc.id, "What does the fox do?",
            doc_title=doc.title, doc_category=doc.category,
        )

    assert result["answer"] == "The fox jumps over the lazy dog."
    assert len(result["source_chunks"]) == 1
    assert result["source_chunks"][0]["id"] == chunks[0].id
    assert result["source_chunks"][0]["text"] == chunks[0].text


def test_answer_question_boundary_padding(db_session):
    """Verify that neighbour chunks are padded with boundary context when they exist."""
    doc = Document(id="pad-doc", filename="pad.pdf", status="processed")
    db_session.add(doc)
    chunks = []
    for i, text in enumerate(["First chunk content.", "Middle chunk content.", "Last chunk content."]):
        chunk = Chunk(
            document_id=doc.id, chunk_index=i, text=text,
            embedding=[0.1, 0.2, 0.3], entities=[],
        )
        db_session.add(chunk)
        chunks.append(chunk)
    db_session.commit()

    with (
        patch("app.services.rag.Groq") as mock_groq_cls,
        patch("app.services.rag.retrieve_chunks") as mock_retrieve,
    ):
        mock_retrieve.return_value = (
            [chunks[1].text],
            [chunks[1].id],
        )

        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value.choices[0].message.content = json.dumps(
            {"answer": "middle", "sources": [1]}
        )
        mock_groq_cls.return_value = mock_groq

        result = answer_question(db_session, doc.id, "question?")

    assert result["answer"] == "middle"
    call_kwargs = mock_groq.chat.completions.create.call_args[1]
    system_msg = call_kwargs["messages"][0]["content"]
    assert "..." in system_msg


def test_answer_question_malformed_json(db_session, document_with_chunks):
    """Verify that a non-JSON LLM response is used verbatim as the answer text."""
    doc, chunks = document_with_chunks

    with (
        patch("app.services.rag.Groq") as mock_groq_cls,
        patch("app.services.rag.retrieve_chunks") as mock_retrieve,
    ):
        mock_retrieve.return_value = (
            [chunks[0].text],
            [chunks[0].id],
        )

        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value.choices[0].message.content = (
            "I am sorry, I cannot find the answer in the provided context."
        )
        mock_groq_cls.return_value = mock_groq

        result = answer_question(db_session, doc.id, "some question")

    assert result["answer"] == "I am sorry, I cannot find the answer in the provided context."
    assert len(result["source_chunks"]) == 1


def test_answer_question_no_sources(db_session, document_with_chunks):
    """Verify that an empty sources array from the LLM returns all retrieved chunks."""
    doc, chunks = document_with_chunks

    with (
        patch("app.services.rag.Groq") as mock_groq_cls,
        patch("app.services.rag.retrieve_chunks") as mock_retrieve,
    ):
        mock_retrieve.return_value = (
            [chunks[0].text],
            [chunks[0].id],
        )

        mock_groq = MagicMock()
        mock_groq.chat.completions.create.return_value.choices[0].message.content = json.dumps(
            {"answer": "Not found in context.", "sources": []}
        )
        mock_groq_cls.return_value = mock_groq

        result = answer_question(db_session, doc.id, "some question")

    assert result["answer"] == "Not found in context."
    assert len(result["source_chunks"]) == 1
    assert result["source_chunks"][0]["id"] == chunks[0].id


# ---------------------------------------------------------------------------
# _format_known_fields tests
# ---------------------------------------------------------------------------

def test_format_known_fields_with_dict_values():
    """Verify that dict-format extractions are formatted as 'field: value' lines."""
    extractions = {
        "Vendor": {"value": "Acme Corp"},
        "Amount": {"value": "$1,000,000"},
        "Date": {"value": "2024-01-15"},
    }
    result = _format_known_fields(extractions)
    assert result.startswith("Known extracted fields")
    assert "Vendor: Acme Corp" in result
    assert "Amount: $1,000,000" in result
    assert "Date: 2024-01-15" in result


def test_format_known_fields_skips_none_and_na():
    """Verify that fields with None, N/A, or empty-string values are omitted."""
    extractions = {
        "Valid": {"value": "present"},
        "NullField": None,
        "NaStr": "N/A",
        "DictNull": {"value": None},
        "DictNa": {"value": "N/A"},
        "EmptyStr": {"value": ""},
    }
    result = _format_known_fields(extractions)
    assert "Valid: present" in result
    assert "NullField" not in result
    assert "NaStr" not in result
    assert "DictNull" not in result
    assert "DictNa" not in result
    assert "EmptyStr" not in result
