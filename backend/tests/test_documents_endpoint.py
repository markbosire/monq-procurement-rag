import io
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from app.main import app
from app.db.session import get_db, get_engine
from app.db.models import Base

client = TestClient(app)

integration = pytest.mark.integration


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=get_engine())
    yield
    Base.metadata.drop_all(bind=get_engine())


def _make_sample_pdf() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, "INVOICE\n\nVendor: ABC Supplies\nClient: MONQ Corp\nTotal Due: $1,500.00\nTerms: Net 30\n\nThis invoice covers the procurement of office equipment delivered on January 15, 2025. Payment should be remitted to the vendor within 30 days of receipt.")
    raw = pdf.output()
    return raw if isinstance(raw, bytes) else bytes(raw)


def test_upload_non_pdf_returns_400():
    response = client.post(
        "/api/documents",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_get_nonexistent_document_returns_404():
    response = client.get("/api/documents/nonexistent-id")
    assert response.status_code == 404


def test_delete_nonexistent_document_returns_404():
    response = client.delete("/api/documents/nonexistent-id")
    assert response.status_code == 404


def test_rename_nonexistent_document_returns_404():
    response = client.patch("/api/documents/nonexistent-id", json={"filename": "new.pdf"})
    assert response.status_code == 404


def test_list_documents_empty():
    """GET /api/documents returns an empty list when no documents exist."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_response_structure():
    """GET /api/documents returns DocumentListItem objects with required fields."""
    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    from app.db.models import Document
    db = Session(bind=get_engine())
    doc = Document(
        id="00000000-0000-0000-0000-000000000001",
        filename="test.pdf",
        status="ready",
        category="Invoice",
        chunk_count=5,
        title="Test Doc",
    )
    db.add(doc)
    db.commit()
    db.close()

    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["document_id"] == "00000000-0000-0000-0000-000000000001"
    assert item["filename"] == "test.pdf"
    assert item["category"] == "Invoice"
    assert item["chunk_count"] == 5
    assert item["title"] == "Test Doc"


def test_list_documents_ready_only():
    """GET /api/documents must only return documents with status='ready'."""
    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    from app.db.models import Document
    db = Session(bind=get_engine())
    db.add(Document(id="d1", filename="ready.pdf", status="ready"))
    db.add(Document(id="d2", filename="processing.pdf", status="processing"))
    db.add(Document(id="d3", filename="failed.pdf", status="error"))
    db.commit()
    db.close()

    response = client.get("/api/documents")
    assert response.status_code == 200
    ids = [d["document_id"] for d in response.json()]
    assert "d1" in ids
    assert "d2" not in ids
    assert "d3" not in ids


def test_get_document_pdf_not_found():
    """GET /api/documents/{id}/pdf returns 404 for a non-existent document."""
    response = client.get("/api/documents/nonexistent-id/pdf")
    assert response.status_code == 404


def test_get_document_pages_not_found():
    """GET /api/documents/{id}/pages returns 404 for a non-existent document."""
    response = client.get("/api/documents/nonexistent-id/pages")
    assert response.status_code == 404


def test_get_document_pages_no_page_texts():
    """GET /api/documents/{id}/pages returns 404 when page_texts is None."""
    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    from app.db.models import Document
    db = Session(bind=get_engine())
    doc = Document(id="pt-none", filename="no_pages.pdf", status="ready", page_texts=None)
    db.add(doc)
    db.commit()
    db.close()

    response = client.get("/api/documents/pt-none/pages")
    assert response.status_code == 404


def test_delete_idempotent():
    """DELETE /api/documents/{id} returns 404 when the document is already deleted."""
    response = client.delete("/api/documents/already-deleted-id")
    assert response.status_code == 404


@integration
def test_upload_pdf_returns_document_response():
    pdf_bytes = _make_sample_pdf()
    response = client.post(
        "/api/documents",
        files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert isinstance(data["document_id"], str)
    assert len(data["document_id"]) == 36
    assert "classification" in data
    assert data["status"] == "ready"
    assert data["chunk_count"] > 0


@integration
def test_upload_and_retrieve_document():
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post(
        "/api/documents",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["document_id"]

    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["document_id"] == doc_id
    assert "classification" in data
    assert data["classification"]["category"] is not None


@integration
def test_rename_persists():
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("old_name.pdf", pdf_bytes, "application/pdf")})
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["document_id"]

    rename_resp = client.patch(f"/api/documents/{doc_id}", json={"filename": "new_name.pdf"})
    assert rename_resp.status_code == 200
    assert rename_resp.json()["document_id"] == doc_id

    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.json()["document_id"] == doc_id


@integration
def test_delete_cascades_to_chunks_and_sessions():
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("del.pdf", pdf_bytes, "application/pdf")})
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["document_id"]

    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    session = Session(bind=get_engine())
    from app.db.models import Chunk, ChatSession
    assert session.query(Chunk).filter(Chunk.document_id == doc_id).count() > 0

    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404

    assert session.query(Chunk).filter(Chunk.document_id == doc_id).count() == 0
    assert session.query(ChatSession).filter(ChatSession.document_id == doc_id).count() == 0
    session.close()


@integration
def test_rename_requires_non_empty():
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("r.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    resp = client.patch(f"/api/documents/{doc_id}", json={"filename": "  "})
    assert resp.status_code == 400


@integration
def test_uuid_format():
    pdf_bytes = _make_sample_pdf()
    resp = client.post("/api/documents", files={"file": ("a.pdf", pdf_bytes, "application/pdf")})
    doc_id = resp.json()["document_id"]
    assert isinstance(doc_id, str)
    assert len(doc_id) == 36
    assert doc_id.count("-") == 4


@integration
def test_list_documents_ordered_by_created_at():
    """GET /api/documents returns documents in descending created_at order."""
    import time
    ids = []
    for label in ["first", "second", "third"]:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, f"Unique content {label} to avoid duplicate hash.")
        raw = pdf.output()
        pdf_bytes = raw if isinstance(raw, bytes) else bytes(raw)
        resp = client.post("/api/documents", files={"file": (f"{label}.pdf", pdf_bytes, "application/pdf")})
        assert resp.status_code == 200
        ids.append(resp.json()["document_id"])
        time.sleep(1)

    response = client.get("/api/documents")
    data = response.json()
    returned_ids = [d["document_id"] for d in data[:3]]
    assert returned_ids == ids[::-1]


@integration
def test_get_document_pdf_success():
    """GET /api/documents/{id}/pdf returns application/pdf with Content-Disposition."""
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("doc.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    response = client.get(f"/api/documents/{doc_id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Content-Disposition" in response.headers
    assert response.headers["Content-Disposition"].startswith("inline")


@integration
def test_get_document_pages_success():
    """GET /api/documents/{id}/pages returns a list of pages with text and page_number."""
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("pages.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    response = client.get(f"/api/documents/{doc_id}/pages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for page in data:
        assert "page_number" in page
        assert "text" in page
        assert "chunk_overlaps" in page


@integration
def test_rename_very_long_filename():
    """Renaming to a very long filename should succeed."""
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("short.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    long_name = "a" * 200 + ".pdf"
    resp = client.patch(f"/api/documents/{doc_id}", json={"filename": long_name})
    assert resp.status_code == 200


@integration
def test_rename_same_filename():
    """Renaming to the same filename should succeed without conflict."""
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("same.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    resp = client.patch(f"/api/documents/{doc_id}", json={"filename": "same.pdf"})
    assert resp.status_code == 200


@integration
def test_delete_removes_pdf_from_storage():
    """Deleting a document also removes its PDF file from the storage backend."""
    pdf_bytes = _make_sample_pdf()
    create_resp = client.post("/api/documents", files={"file": ("del_storage.pdf", pdf_bytes, "application/pdf")})
    doc_id = create_resp.json()["document_id"]

    from app.storage import get_pdf_storage
    storage = get_pdf_storage()
    assert storage.get(doc_id) is not None

    client.delete(f"/api/documents/{doc_id}")

    assert storage.get(doc_id) is None


def test_get_document_pdf_no_data():
    """GET /api/documents/{id}/pdf returns 404 when no PDF data is available in storage or database."""
    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    from app.db.models import Document
    db = Session(bind=get_engine())
    doc = Document(id="no-pdf-data", filename="missing.pdf", status="ready", file_data=None)
    db.add(doc)
    db.commit()
    db.close()

    response = client.get("/api/documents/no-pdf-data/pdf")
    assert response.status_code == 404


def test_get_document_pages_with_chunk_id():
    """GET /api/documents/{id}/pages?chunk_id=X returns chunk_overlaps with bbox data."""
    from app.db.session import get_engine
    from sqlalchemy.orm import Session
    from app.db.models import Document, Chunk
    db = Session(bind=get_engine())
    doc = Document(
        id="pages-chunk-test",
        filename="chunk_pages.pdf",
        status="ready",
        page_texts=["Page one content.", "Page two content."],
    )
    db.add(doc)
    db.flush()
    chunk = Chunk(
        document_id=doc.id,
        chunk_index=0,
        text="Page one content.",
        bbox=[{"page": 1, "x0": 10, "y0": 20, "x1": 100, "y1": 50}],
        page_numbers=[1],
    )
    db.add(chunk)
    db.commit()
    chunk_id = chunk.id
    db.close()

    response = client.get(f"/api/documents/pages-chunk-test/pages?chunk_id={chunk_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    page_one = data[0]
    assert page_one["page_number"] == 1
    assert len(page_one["chunk_overlaps"]) == 1
    overlap = page_one["chunk_overlaps"][0]
    assert overlap["chunk_id"] == chunk_id
    assert overlap["bbox"]["page"] == 1
    assert overlap["bbox"]["x0"] == 10


@integration
def test_upload_pdf_no_text_returns_400():
    """Uploading a PDF with no extractable text should return a 400 error."""
    from unittest.mock import patch
    pdf_bytes = _make_sample_pdf()
    with patch("app.routers.documents.ingest_document") as mock_ingest:
        mock_ingest.side_effect = ValueError("PDF contains no extractable text")
        response = client.post(
            "/api/documents",
            files={"file": ("empty.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 400
    assert "no extractable text" in response.json()["detail"].lower()
