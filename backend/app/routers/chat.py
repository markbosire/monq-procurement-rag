"""Chat-related API routes.

Provides endpoints for asking questions about a document and retrieving
chat history for a document's conversation session.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse, ChatHistoryResponse, ChatHistoryMessage, SourceChunk
from app.services.rag import answer_question
from app.repositories.chat_repository import ChatRepository
from app.config import require_groq_key

router = APIRouter(prefix="/documents/{document_id}/chat", tags=["chat"])

MAX_HISTORY_MESSAGES = 10


def get_chat_repository(db: Session = Depends(get_db)) -> ChatRepository:
    """Dependency provider for ChatRepository.

    Args:
        db: Database session.

    Returns:
        A ChatRepository bound to the given session.
    """
    return ChatRepository(db)


def _build_history(messages: list) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(
    document_id: str,
    repo: ChatRepository = Depends(get_chat_repository),
):
    """Retrieve the full chat history for a document.

    Args:
        document_id: The document's unique identifier.
        repo: Chat repository dependency.

    Returns:
        ChatHistoryResponse containing all messages for the document.

    Raises:
        HTTPException 404: If the document is not found.
    """
    doc = repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    messages = repo.get_history(document_id)
    return ChatHistoryResponse(
        messages=[
            ChatHistoryMessage(
                role=m.role,
                content=m.content,
                source_chunks=m.source_chunks if m.source_chunks else [],
                created_at=m.created_at,
            )
            for m in messages
        ]
    )


@router.post("", response_model=ChatResponse)
def chat(
    document_id: str,
    body: ChatRequest,
    db: Session = Depends(get_db),
    repo: ChatRepository = Depends(get_chat_repository),
):
    """Ask a question about a document and receive an answer.

    The question is answered via RAG over the document's chunks. Previous
    messages in the session are included for conversational context.

    Args:
        document_id: The document's unique identifier.
        body: The chat request containing the question.
        db: Database session.
        repo: Chat repository dependency.

    Returns:
        ChatResponse with the answer and supporting source chunks.

    Raises:
        HTTPException 404: If the document is not found.
        HTTPException 400: If the document is not yet ready for chat.
    """
    doc = repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document is not ready for chat")

    try:
        require_groq_key()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    session = repo.get_or_create_session(document_id)

    recent_messages = repo.get_recent_messages(session.id, MAX_HISTORY_MESSAGES)
    recent_messages.reverse()
    history = _build_history(recent_messages)

    repo.add_message(session.id, "user", body.question)

    result = answer_question(
        db, document_id, body.question,
        history=history,
        doc_category=doc.category,
        doc_title=doc.title,
        doc_extractions=doc.extractions,
    )

    repo.add_message(
        session.id,
        "assistant",
        result["answer"],
        source_chunks=result.get("source_chunks", []),
    )

    db.commit()

    return ChatResponse(
        answer=result["answer"],
        source_chunks=[
            SourceChunk(
                id=s["id"],
                text=s["text"],
                page_numbers=s["page_numbers"],
                bbox=s.get("bbox", []),
            )
            for s in result["source_chunks"]
        ],
    )