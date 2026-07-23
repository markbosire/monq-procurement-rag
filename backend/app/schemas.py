"""Pydantic models for request/response serialisation.

Defines the data contracts used by the FastAPI endpoints for documents,
chat, and document page data.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ClassificationResult(BaseModel):
    """Result of document classification."""

    category: str
    confidence: float
    reasoning: str


class DocumentResponse(BaseModel):
    """Full document metadata returned after upload or retrieval."""

    document_id: str
    classification: ClassificationResult
    chunk_count: int
    status: str
    duplicate_of: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    extractions: Optional[dict] = None


class DocumentListItem(BaseModel):
    """Summary of a document for listing endpoints."""

    document_id: str
    filename: str
    category: Optional[str] = None
    chunk_count: int
    title: Optional[str] = None
    created_at: Optional[datetime] = None


class RenameDocumentRequest(BaseModel):
    """Request body for renaming a document."""

    filename: str


class ChatRequest(BaseModel):
    """Request body for asking a question about a document."""

    question: str


class SourceChunk(BaseModel):
    """A chunk that was cited as a source for a chat answer."""

    id: int
    text: str
    page_numbers: list[int] = []
    bbox: list[dict] = []


class ChatResponse(BaseModel):
    """Response containing the answer and supporting source chunks."""

    answer: str
    source_chunks: list[SourceChunk] = []


class ChatHistoryMessage(BaseModel):
    """A single message in a chat session history."""

    role: str
    content: str
    source_chunks: list[dict] = []
    created_at: Optional[datetime] = None


class ChatHistoryResponse(BaseModel):
    """Collection of chat history messages for a session."""

    messages: list[ChatHistoryMessage] = []


class PageChunkOverlap(BaseModel):
    """Metadata for a chunk's bounding box overlap on a given page."""

    chunk_id: int
    char_start: int = 0
    char_end: int = 0
    bbox: Optional[dict] = None


class PageResponse(BaseModel):
    """A single page's text and chunk overlap annotations."""

    page_number: int
    text: str
    chunk_overlaps: list[PageChunkOverlap] = []