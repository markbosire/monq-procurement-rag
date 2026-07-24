"""Application configuration loaded from environment variables.

Uses pydantic-settings to read a .env file and provide typed configuration
values for database, LLM, embeddings, and storage settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide configuration.

    Reads from a .env file via pydantic-settings. All fields have sensible
    defaults suitable for local development.

    Attributes:
        database_url: SQLAlchemy database connection string.
        groq_api_key: API key for the Groq LLM provider.
        embedding_model_name: Name of the sentence-transformers model.
        groq_model_name: Groq model identifier for chat completions.
        top_k_chunks: Number of final chunks to return after retrieval.
        hybrid_alpha: Blend factor between BM25 and semantic scores (0 = pure semantic, 1 = pure BM25).
        rerank_candidates: Number of candidates to consider before cross-encoder reranking.
        pdf_storage_backend: Storage backend type (e.g. 'local').
        pdf_storage_path: Filesystem path for local PDF storage.
    """

    database_url: str = "sqlite:///./procurement.db"
    groq_api_key: str = ""
    embedding_model_name: str = "all-MiniLM-L6-v2"
    groq_model_name: str = "llama-3.3-70b-versatile"
    top_k_chunks: int = 5
    hybrid_alpha: float = 0.3
    rerank_candidates: int = 20

    pdf_storage_backend: str = "local"
    pdf_storage_path: str = "./storage/pdfs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

_PLACEHOLDER = "your_groq_api_key_here"


def require_groq_key():
    key = settings.groq_api_key
    if not key or key == _PLACEHOLDER:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add your real key to the .env file "
            "(the default placeholder from .env.example won't work), "
            "then restart the server."
        )