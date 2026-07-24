# MONQ Procurement RAG — Testing Documentation

## Table of Contents
1. [Overview](#1-overview)
2. [Backend Testing Strategy (`pytest`)](#2-backend-testing-strategy-pytest)
   - [Running Backend Tests](#running-backend-tests)
   - [Test Suite Structure](#test-suite-structure)
   - [Fixtures & Mocks (`conftest.py`)](#fixtures--mocks-conftestpy)
3. [Frontend Testing Strategy (`Vitest`)](#3-frontend-testing-strategy-vitest)
   - [Running Frontend Tests](#running-frontend-tests)
   - [Frontend Test Suite Structure](#frontend-test-suite-structure)
4. [Coverage Enforcement & Reports](#4-coverage-enforcement--reports)

---

## 1. Overview

The MONQ Procurement RAG system includes an automated testing suite for both backend services (Python/pytest) and frontend reactive UI components (Vue 3/Vitest). The test suites cover unit tests for core algorithms, integration tests for API endpoints and stores, and full user flow simulations.

---

## 2. Backend Testing Strategy (`pytest`)

Backend tests are located in `backend/tests/` and built using `pytest` and `httpx.AsyncClient`.

### Running Backend Tests

1. Navigate to the backend directory and activate your virtual environment:
   ```bash
   cd backend
   source .venv/bin/activate
   ```

2. Run the complete test suite:
   ```bash
   pytest
   ```

3. Run with coverage report:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

4. Run specific test files:
   ```bash
   pytest tests/test_rag_integration.py
   ```

### Test Suite Structure

| Test File | Description / Scope |
|---|---|
| `test_pdf_extraction.py` | Line span extraction, bounding box computation, multi-column reordering, and header/footer stripping heuristics. |
| `test_chunking.py` | Heading detection (ALL-CAPS, SECTION markers), recursive splitting, and heading breadcrumb prepending. |
| `test_embeddings.py` | Local sentence-transformers vector generation and dimension checks (384-dim). |
| `test_classification.py` | Document centroid calculation, cosine similarity exemplar matching, and Groq JSON-mode classification fallback. |
| `test_ner.py` | spaCy entity extraction (`ORG`, `DATE`, `MONEY`, `LAW`) and query entity overlap boosting. |
| `test_retrieval.py` | Three-branch hybrid scoring (Okapi BM25 + Cosine Vector Similarity + spaCy NER boost) and score fusion ($\alpha=0.3$). |
| `test_rag_integration.py` | End-to-end RAG answer pipeline, context boundary padding ($\pm 150$ characters), cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`), and JSON grounding. |
| `test_documents_endpoint.py` | `POST /api/documents` (upload & deduplication), `GET /api/documents`, `PATCH`, `DELETE`, and binary PDF streaming. |
| `test_chat_endpoint.py` | `POST /api/documents/{id}/chat` query processing and `GET /api/documents/{id}/chat/history` retrieval. |
| `test_models.py` | SQLAlchemy ORM model verification, relationships, and custom `VectorType` JSON serialization. |
| `test_repositories.py` | Data access layer methods for `DocumentRepository` and `ChatRepository`. |
| `test_storage.py` | Local filesystem PDF storage (`LocalFileStorage`) saving, reading, and deletion. |

### Fixtures & Mocks (`conftest.py`)
- **In-Memory SQLite**: Configured with an in-memory SQLite database instance (`sqlite:///:memory:`) for isolated, fast execution.
- **Mocked Groq API**: Groq LLM API network calls are mocked to prevent external API calls during testing.

---

## 3. Frontend Testing Strategy (`Vitest`)

Frontend tests are located in `frontend/src/__tests__/` and built using `Vitest`, `@vue/test-utils`, and `happy-dom`.

### Running Frontend Tests

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Run the unit & integration test suite:
   ```bash
   npm run test
   ```

3. Run Vitest in watch mode (interactive):
   ```bash
   npx vitest
   ```

4. Run tests with coverage:
   ```bash
   npm run test:coverage
   ```

### Frontend Test Suite Structure

| Test File | Description / Scope |
|---|---|
| `App.test.ts` | Root `App.vue` component testing, router-view rendering, toast notifications display, auto-dismiss, manual dismiss, and type-based styling. |
| `UploadNavigateChat.test.ts` | Integration flow test simulating PDF upload, automatic navigation to document detail view, and initiating a chat query. |
| `SourceHighlightPdfSync.test.ts` | Integration test verifying active chat source chunk selection and synchronous PDF canvas bounding-box highlight rendering. |
| `router.test.ts` | Vue Router navigation guard, route matching, and fallback handling. |
| `utils.test.ts` | Helper utilities, formatting functions, and coordinate scale calculations. |
| `smoke.test.ts` | Environment sanity check ensuring Vitest test runner setup works correctly. |

---

## 4. Coverage Enforcement & Reports

- **Backend Target**: $>80\%$ statement and line coverage across domain services and API routers.
- **Frontend Target**: $>75\%$ statement and line coverage enforced in `vite.config.ts`.
