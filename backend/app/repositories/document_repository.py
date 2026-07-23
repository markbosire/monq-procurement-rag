"""Repository for document and chunk database operations.

Encapsulates queries for documents and their associated text chunks
using SQLAlchemy sessions.
"""

from sqlalchemy.orm import Session

from app.db.models import Document, Chunk


class DocumentRepository:
    """Data-access layer for documents and chunks."""

    def __init__(self, db: Session):
        """Initialise the repository with a database session.

        Args:
            db: SQLAlchemy session.
        """
        self.db = db

    def list_ready(self) -> list[Document]:
        """Return all documents with status 'ready', newest first.

        Returns:
            List of ready Document objects.
        """
        return (
            self.db.query(Document)
            .filter(Document.status == "ready")
            .order_by(Document.created_at.desc())
            .all()
        )

    def get_by_id(self, document_id: str) -> Document | None:
        """Look up a document by its UUID.

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

    def get_by_hash(self, content_hash: str) -> Document | None:
        """Look up a ready document by its content hash (duplicate detection).

        Args:
            content_hash: SHA-256 hex digest of the PDF content.

        Returns:
            The Document if a ready duplicate exists, else None.
        """
        return (
            self.db.query(Document)
            .filter(Document.content_hash == content_hash, Document.status == "ready")
            .first()
        )

    def create(self, **kwargs) -> Document:
        """Create and add a new Document to the session.

        Args:
            **kwargs: Document column values.

        Returns:
            The newly created Document instance.
        """
        doc = Document(**kwargs)
        self.db.add(doc)
        return doc

    def delete(self, document_id: str) -> bool:
        """Delete a document by its UUID.

        Args:
            document_id: The document UUID.

        Returns:
            True if the document was deleted, False if not found.
        """
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        return True

    def get_chunks_for_document(self, document_id: str) -> list[Chunk]:
        """Return all chunks for a document.

        Args:
            document_id: The document UUID.

        Returns:
            List of Chunk objects.
        """
        return (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .all()
        )

    def get_chunk_by_id(self, chunk_id: int, document_id: str) -> Chunk | None:
        """Look up a single chunk by its id and document.

        Args:
            chunk_id: The chunk's integer primary key.
            document_id: The document UUID.

        Returns:
            The Chunk if found, else None.
        """
        return (
            self.db.query(Chunk)
            .filter(Chunk.id == chunk_id, Chunk.document_id == document_id)
            .first()
        )

    def get_chunks_by_ids(self, ids: list[int]) -> list[Chunk]:
        """Return chunks matching the given primary key ids.

        Args:
            ids: List of chunk primary keys.

        Returns:
            List of matching Chunk objects.
        """
        return (
            self.db.query(Chunk)
            .filter(Chunk.id.in_(ids))
            .all()
        )

    def get_chunks_by_indices(self, document_id: str, indices: set[int]) -> list[Chunk]:
        """Return chunks matching the given chunk_index values for a document.

        Args:
            document_id: The document UUID.
            indices: Set of chunk_index values to fetch.

        Returns:
            List of matching Chunk objects.
        """
        if not indices:
            return []
        return (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id, Chunk.chunk_index.in_(indices))
            .all()
        )

    def get_chunk_index_to_id_map(self, document_id: str, chunk_indices: list[int]) -> dict:
        """Build a mapping from chunk_index to chunk primary key.

        Args:
            document_id: The document UUID.
            chunk_indices: List of chunk_index values.

        Returns:
            Dict mapping chunk_index -> chunk id, with None values filtered out.
        """
        valid_indices = [i for i in chunk_indices if i is not None]
        if not valid_indices:
            return {}
        results = (
            self.db.query(Chunk)
            .filter(
                Chunk.document_id == document_id,
                Chunk.chunk_index.in_(valid_indices),
            )
            .all()
        )
        return {ch.chunk_index: ch.id for ch in results}