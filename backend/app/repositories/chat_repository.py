"""Repository for chat-related database operations.

Encapsulates queries for documents, chat sessions, and chat messages
using SQLAlchemy sessions.
"""

from sqlalchemy.orm import Session

from app.db.models import Document, ChatSession, ChatMessage


class ChatRepository:
    """Data-access layer for chat sessions and messages."""

    def __init__(self, db: Session):
        """Initialise the repository with a database session.

        Args:
            db: SQLAlchemy session.
        """
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        """Look up a document by its id.

        Args:
            document_id: The document UUID.

        Returns:
            The Document if found, else None.
        """
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def get_or_create_session(self, document_id: str) -> ChatSession:
        """Return the most recent session for a document, or create a new one.

        Args:
            document_id: The document UUID.

        Returns:
            An existing or newly created ChatSession.
        """
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.document_id == document_id)
            .order_by(ChatSession.created_at.desc())
            .first()
        )
        if not session:
            session = ChatSession(document_id=document_id)
            self.db.add(session)
            self.db.flush()
            self.db.refresh(session)
        return session

    def get_latest_session(self, document_id: str) -> ChatSession | None:
        """Return the most recent chat session for a document.

        Args:
            document_id: The document UUID.

        Returns:
            The latest ChatSession or None.
        """
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.document_id == document_id)
            .order_by(ChatSession.created_at.desc())
            .first()
        )

    def get_history(self, document_id: str) -> list[ChatMessage]:
        """Return all messages for a document, oldest first.

        Args:
            document_id: The document UUID.

        Returns:
            Chronologically ordered list of ChatMessage.
        """
        session = self.get_latest_session(document_id)
        if not session:
            return []
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def get_recent_messages(self, session_id: int, limit: int = 10) -> list[ChatMessage]:
        """Return the most recent messages for a session.

        Args:
            session_id: The chat session id.
            limit: Maximum number of messages to return.

        Returns:
            List of ChatMessage, newest first.
        """
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    def add_message(
        self, session_id: int, role: str, content: str, source_chunks: list | None = None
    ) -> ChatMessage:
        """Persist a new chat message.

        Args:
            session_id: The chat session id.
            role: Message role ('user' or 'assistant').
            content: Message body text.
            source_chunks: Optional list of source chunk references.

        Returns:
            The newly created ChatMessage.
        """
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            source_chunks=source_chunks or [],
        )
        self.db.add(msg)
        return msg