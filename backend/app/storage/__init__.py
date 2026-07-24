"""Storage abstraction for PDF binaries.

Provides a factory function that instantiates the appropriate PDF storage
backend based on application settings. Currently supports 'local' filesystem
storage; the architecture is designed to allow adding an 's3' backend by
implementing the PDFStorage interface and registering it in the _BACKENDS
mapping.
"""

from app.storage.interfaces import PDFStorage
from app.storage.local_storage import LocalFileStorage
from app.config import settings

_BACKENDS: dict[str, type[PDFStorage]] = {
    "local": LocalFileStorage,
}


def get_pdf_storage() -> PDFStorage:
    """Factory: return a PDFStorage instance based on settings.pdf_storage_backend.

    Looks up the backend name in the _BACKENDS registry and instantiates
    the corresponding class. New backends can be added by implementing
    PDFStorage and registering the class here.

    Returns:
        PDFStorage: Concrete storage backend instance.

    Raises:
        ValueError: If pdf_storage_backend is set to an unsupported value.
    """
    backend = settings.pdf_storage_backend
    cls = _BACKENDS.get(backend)
    if cls is None:
        msg = (
            f"Unknown pdf_storage_backend: '{backend}'. "
            f"Supported: {', '.join(sorted(_BACKENDS))}."
        )
        raise ValueError(msg)
    return cls(base_path=settings.pdf_storage_path)


__all__ = ["PDFStorage", "LocalFileStorage", "get_pdf_storage"]
