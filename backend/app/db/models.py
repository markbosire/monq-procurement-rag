"""SQLAlchemy ORM models for the procurement RAG database.

Defines the schema for documents, text chunks, chat sessions, and messages,
along with a custom VectorType for storing JSON-serialised lists.
"""

import json
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, func, TypeDecorator, LargeBinary
from sqlalchemy.orm import DeclarativeBase, relationship


class VectorType(TypeDecorator):
    """Custom SQLAlchemy type that stores a Python list as a JSON string.

    Automatically serialises on bind and deserialises on result retrieval.
    Uses the ``TEXT`` column type as its implementation.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class Document(Base):
    """A single uploaded procurement document with its classification metadata."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="processing")
    category = Column(String(100))
    confidence = Column(Float)
    reasoning = Column(Text)
    content_hash = Column(String(64), nullable=True, index=True)
    chunk_count = Column(Integer, default=0)
    file_data = Column(LargeBinary, nullable=True)
    page_texts = Column(VectorType, nullable=True)
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    extractions = Column(VectorType, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """A text chunk extracted from a document with embedding and metadata."""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(VectorType(384))
    entities = Column(VectorType, nullable=True)
    page_numbers = Column(VectorType, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    bbox = Column(VectorType, nullable=True)

    document = relationship("Document", back_populates="chunks")


class ChatSession(Base):
    """A chat session tied to a specific document."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """A single message within a chat session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    source_chunks = Column(VectorType, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")