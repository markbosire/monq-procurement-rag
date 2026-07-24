"""Local filesystem implementation of the PDFStorage interface.

Saves PDF files to a configurable base directory, using the document id
as the filename with a .pdf extension.
"""

import os

from app.storage.interfaces import PDFStorage


class LocalFileStorage(PDFStorage):
    """Stores PDF binaries on the local filesystem.

    Each document's PDF is saved as ``{document_id}.pdf`` inside the
    configured base_path directory. The directory is created on
    instantiation if it does not exist.

    Attributes:
        base_path: Root directory under which PDF files are stored.
    """

    def __init__(self, base_path: str = "./storage/pdfs") -> None:
        """Initialise the local storage backend.

        Args:
            base_path: Directory path for storing PDF files. Created if
                missing.
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _path(self, document_id: str) -> str:
        """Return the full filesystem path for a document's PDF.

        Args:
            document_id: Unique document identifier.

        Returns:
            Absolute or relative path to the PDF file.
        """
        return os.path.join(self.base_path, f"{document_id}.pdf")

    def save(self, document_id: str, pdf_bytes: bytes) -> None:
        """Write PDF bytes to the local filesystem.

        Args:
            document_id: Unique document identifier.
            pdf_bytes: Raw PDF file content.
        """
        path = self._path(document_id)
        with open(path, "wb") as f:
            f.write(pdf_bytes)

    def get(self, document_id: str) -> bytes | None:
        """Read PDF bytes from the local filesystem.

        Args:
            document_id: Unique document identifier.

        Returns:
            The PDF bytes if the file exists, otherwise None.
        """
        path = self._path(document_id)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete(self, document_id: str) -> None:
        """Remove a document's PDF file from the filesystem.

        Args:
            document_id: Unique document identifier.
        """
        path = self._path(document_id)
        if os.path.exists(path):
            os.remove(path)
