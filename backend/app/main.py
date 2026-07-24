"""FastAPI application entry point for the MONQ Procurement RAG service.

Sets up the ASGI application with CORS middleware, registers API routers
for documents and chat endpoints, and initialises the database on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db
from app.routers import documents, chat


def _init_models():
    """Pre-download all ML models at startup so the first upload is fast."""
    import spacy
    from spacy.cli import download as spacy_download
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        spacy_download("en_core_web_sm")

    from app.services.embeddings import load_embedding_model
    load_embedding_model()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle.

    Initialises the database schema, runs pending migrations, and
    pre-downloads ML models before serving requests.
    """
    init_db()
    _init_models()
    yield


app = FastAPI(title="MONQ Procurement RAG", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health():
    """Health-check endpoint.

    Returns:
        dict: A simple status indicator.
    """
    return {"status": "ok"}