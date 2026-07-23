"""Document management API routes.

Provides endpoints for listing, uploading, retrieving, renaming, deleting,
and viewing PDF documents along with their per-page text data.
"""

import hashlib

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response

from app.db.session import get_db, transaction
from app.db.models import Document
from app.schemas import DocumentResponse, DocumentListItem, ClassificationResult, PageResponse, PageChunkOverlap, RenameDocumentRequest
from app.services.pdf_extraction import extract_text, extract_text_with_spans
from app.services.ingestion import ingest_document
from app.repositories.document_repository import DocumentRepository
from app.storage import get_pdf_storage
from app.storage.interfaces import PDFStorage

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    """Dependency provider for DocumentRepository.

    Args:
        db: Database session.

    Returns:
        A DocumentRepository bound to the given session.
    """
    return DocumentRepository(db)


def get_storage() -> PDFStorage:
    """Dependency provider for the configured PDF storage backend.

    Returns:
        A PDFStorage instance.
    """
    return get_pdf_storage()


@router.get("", response_model=list[DocumentListItem])
def list_documents(repo: DocumentRepository = Depends(get_document_repository)):
    """List all documents that are in the 'ready' state.

    Args:
        repo: Document repository dependency.

    Returns:
        A list of DocumentListItem summaries.
    """
    docs = repo.list_ready()
    return [
        DocumentListItem(
            document_id=d.id,
            filename=d.filename,
            category=d.category,
            chunk_count=d.chunk_count,
            title=d.title,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    repo: DocumentRepository = Depends(get_document_repository),
    storage: PDFStorage = Depends(get_storage),
):
    """Upload a PDF document for ingestion and classification.

    Detects duplicate uploads via SHA-256 hash. On duplicate, returns the
    existing document's metadata with a duplicate_of reference.

    Args:
        file: The uploaded PDF file.
        db: Database session.
        repo: Document repository dependency.
        storage: PDF storage backend dependency.

    Returns:
        DocumentResponse with classification, chunk count, and extracted fields.

    Raises:
        HTTPException 400: If the file is not a PDF or ingestion fails.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    content_hash = hashlib.sha256(pdf_bytes).hexdigest()

    existing = repo.get_by_hash(content_hash)
    if existing:
        return DocumentResponse(
            document_id=existing.id,
            classification=ClassificationResult(
                category=existing.category,
                confidence=existing.confidence,
                reasoning=existing.reasoning,
            ),
            chunk_count=existing.chunk_count,
            status=existing.status,
            duplicate_of=existing.id,
        )

    try:
        with transaction(db):
            doc = ingest_document(db, file.filename, pdf_bytes, content_hash)
            storage.save(doc.id, pdf_bytes)
            db.refresh(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return DocumentResponse(
        document_id=doc.id,
        classification=ClassificationResult(
            category=doc.category,
            confidence=doc.confidence,
            reasoning=doc.reasoning,
        ),
        chunk_count=doc.chunk_count,
        status=doc.status,
        title=doc.title,
        summary=doc.summary,
        extractions=doc.extractions,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, repo: DocumentRepository = Depends(get_document_repository)):
    """Retrieve metadata for a single document.

    Args:
        document_id: The document's unique identifier.
        repo: Document repository dependency.

    Returns:
        DocumentResponse with the document's classification and metadata.

    Raises:
        HTTPException 404: If the document is not found.
    """
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        document_id=doc.id,
        classification=ClassificationResult(
            category=doc.category,
            confidence=doc.confidence,
            reasoning=doc.reasoning,
        ),
        chunk_count=doc.chunk_count,
        status=doc.status,
        title=doc.title,
        summary=doc.summary,
        extractions=doc.extractions,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
def rename_document(
    document_id: str,
    body: RenameDocumentRequest,
    db: Session = Depends(get_db),
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Rename a document's filename.

    Args:
        document_id: The document's unique identifier.
        body: Request body containing the new filename.
        db: Database session.
        repo: Document repository dependency.

    Returns:
        Updated DocumentResponse.

    Raises:
        HTTPException 404: If the document is not found.
        HTTPException 400: If the new filename is empty.
    """
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    name = body.filename.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Filename must not be empty")
    doc.filename = name
    db.commit()
    db.refresh(doc)
    return DocumentResponse(
        document_id=doc.id,
        classification=ClassificationResult(
            category=doc.category,
            confidence=doc.confidence,
            reasoning=doc.reasoning,
        ),
        chunk_count=doc.chunk_count,
        status=doc.status,
        title=doc.title,
        summary=doc.summary,
        extractions=doc.extractions,
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    repo: DocumentRepository = Depends(get_document_repository),
    storage: PDFStorage = Depends(get_storage),
):
    """Delete a document and its associated storage.

    Args:
        document_id: The document's unique identifier.
        db: Database session.
        repo: Document repository dependency.
        storage: PDF storage backend dependency.

    Raises:
        HTTPException 404: If the document is not found.
    """
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    storage.delete(document_id)
    return None


@router.get("/{document_id}/pdf")
def get_document_pdf(
    document_id: str,
    repo: DocumentRepository = Depends(get_document_repository),
    storage: PDFStorage = Depends(get_storage),
):
    """Stream the original PDF file for a document.

    Falls back to in-database file_data if the PDF is not found in storage.

    Args:
        document_id: The document's unique identifier.
        repo: Document repository dependency.
        storage: PDF storage backend dependency.

    Returns:
        A Response with the PDF bytes and inline content disposition.

    Raises:
        HTTPException 404: If the document or its PDF data is not found.
    """
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_bytes = storage.get(document_id)
    if pdf_bytes is None:
        if doc.file_data:
            pdf_bytes = doc.file_data
        else:
            raise HTTPException(status_code=404, detail="PDF not available")

    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=\"{doc.filename}\"",
    })


@router.get("/{document_id}/pages", response_model=list[PageResponse])
def get_document_pages(
    document_id: str,
    chunk_id: int | None = None,
    repo: DocumentRepository = Depends(get_document_repository),
):
    """Retrieve per-page text data with optional chunk overlap annotations.

    Args:
        document_id: The document's unique identifier.
        chunk_id: Optional chunk ID to highlight bounding box overlaps.
        repo: Document repository dependency.

    Returns:
        A list of PageResponse objects, one per page.

    Raises:
        HTTPException 404: If the document or page data is not found.
    """
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    page_texts = doc.page_texts
    if not page_texts:
        raise HTTPException(status_code=404, detail="No page data available for this document")

    chunk_bboxes_map: dict[int, list[dict]] = {}
    chunk_text_map: dict[int, str] = {}

    if chunk_id is not None:
        chunk = repo.get_chunk_by_id(chunk_id, document_id)
        if chunk:
            if chunk.bbox:
                for b in chunk.bbox:
                    page_num = b["page"]
                    chunk_bboxes_map.setdefault(page_num, []).append(b)
            chunk_text_map[chunk.id] = chunk.text

    result: list[PageResponse] = []
    for p_idx, pt in enumerate(page_texts):
        page_num = p_idx + 1
        overlaps = [
            PageChunkOverlap(
                chunk_id=chunk_id,
                char_start=0,
                char_end=0,
                bbox=bbox,
            )
            for bbox in chunk_bboxes_map.get(page_num, [])
        ] if chunk_id else []

        result.append(PageResponse(
            page_number=page_num,
            text=pt,
            chunk_overlaps=overlaps,
        ))

    return result