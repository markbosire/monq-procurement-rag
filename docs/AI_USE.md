# AI Assistance & Tool Usage Disclosure

This document outlines how Artificial Intelligence (AI) tools and autonomous agents were utilized throughout the research, design, prototyping, testing, and documentation phases of the **MONQ Procurement RAG** system.

---

## Key Areas of AI Utilization

### 1. Web Search & Architecture Alternatives Research
- Utilized AI search sub-agents to perform deep web research on architectural alternatives for local RAG systems.
- Researched optimal hybrid search scoring algorithms (Okapi BM25 + Dense Cosine Vector Similarity + Named Entity Recognition boosting).
- Evaluated lightweight embedding models (`all-MiniLM-L6-v2`) and cross-encoder re-ranking models (`ms-marco-MiniLM-L-6-v2`) suitable for local execution.

### 2. Prototype Creation & Experiments
- Leveraged AI agents to rapidly create, run, and evaluate technical proof-of-concept (PoC) prototypes.
- Experimented with PyMuPDF text extraction heuristics, multi-column span re-ordering, and heading-aware chunk boundary padding ($\pm 150$ characters).
- Tested SQLite vector storage strategies via custom SQLAlchemy `VectorType` JSON serialization.

### 3. Boilerplate Generation
- Accelerated initial codebase setup by auto-generating boilerplate Pydantic schemas (`backend/app/schemas.py`), FastAPI router controllers, and standard repository patterns.
- Automated repetition in database entity definitions, dependency injections, and environment variable configuration files.

### 4. Frontend Prototyping & Layout Testing
- Used AI tools to explore and prototype Vue 3 Composition API components, Pinia stores, and Tailwind CSS design layouts.
- Tested interactive PDF.js canvas overlay integration for dynamic bounding-box visual highlighting.

### 5. Automated Test Suite Generation
- Used AI to rapidly generate comprehensive backend unit and integration test suites (`pytest`).
- Built and expanded frontend unit and integration tests using `Vitest` and `@vue/test-utils` (`UploadNavigateChat.test.ts`, `SourceHighlightPdfSync.test.ts`, `App.test.ts`) to achieve high statement and line test coverage.

### 6. System Documentation & Diagrams
- Generated technical documentation, including `architecture.md` and `API.md`.
- Formatted structured Markdown documentation, API contracts, entity-relationship models, and system flow breakdowns.
