"""Abstract storage interface for PDF binary persistence.

Defines the PDFStorage contract that all storage backends must implement.
This allows swapping between local filesystem, S3, or other backends
without changing the rest of the application.
"""

from abc import ABC, abstractmethod


class PDFStorage(ABC):
    """Abstract base class for PDF binary storage backends.

    Implementations handle saving, retrieving, and deleting PDF byte data
    keyed by document id.
    """

    @abstractmethod
    def save(self, document_id: str, pdf_bytes: bytes) -> None:
        """Persist PDF bytes for a given document.

        Args:
            document_id: Unique identifier for the document.
            pdf_bytes: Raw PDF file content.
        """

    @abstractmethod
    def get(self, document_id: str) -> bytes | None:
        """Retrieve PDF bytes for a given document.

        Args:
            document_id: Unique identifier for the document.

        Returns:
            The PDF bytes if found, or None if no stored PDF exists.
        """

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """Remove the stored PDF for a given document.

        Args:
            document_id: Unique identifier for the document.
        """
