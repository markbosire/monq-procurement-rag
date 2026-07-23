# MONQ Procurement RAG — API Documentation

## Table of Contents
1. [API Overview](#1-api-overview)
2. [API Endpoints](#2-api-endpoints)
   - [2.1. Documents](#21-documents)
     - [GET /documents](#get-documents)
     - [POST /documents](#post-documents)
     - [GET /documents/{document_id}](#get-documentsdocument_id)
     - [PATCH /documents/{document_id}](#patch-documentsdocument_id)
     - [DELETE /documents/{document_id}](#delete-documentsdocument_id)
     - [GET /documents/{document_id}/pdf](#get-documentsdocument_idpdf)
     - [GET /documents/{document_id}/pages](#get-documentsdocument_idpages)
   - [2.2. Chat](#22-chat)
     - [GET /documents/{document_id}/chat/history](#get-documentsdocument_idchathistory)
     - [POST /documents/{document_id}/chat](#post-documentsdocument_idchat)
   - [2.3. Health](#23-health)
     - [GET /health](#get-health)
3. [Error Responses](#3-error-responses)
4. [Data Models](#4-data-models)
   - [4.1. ClassificationResult](#41-classificationresult)
   - [4.2. DocumentResponse](#42-documentresponse)
   - [4.3. DocumentListItem](#43-documentlistitem)
   - [4.4. RenameDocumentRequest](#44-renamedocumentrequest)
   - [4.5. ChatRequest](#45-chatrequest)
   - [4.6. SourceChunk](#46-sourcechunk)
   - [4.7. ChatResponse](#47-chatresponse)
   - [4.8. ChatHistoryMessage](#48-chathistorymessage)
   - [4.9. ChatHistoryResponse](#49-chathistoryresponse)
   - [4.10. PageChunkOverlap](#410-pagechunkoverlap)
   - [4.11. PageResponse](#411-pageresponse)
   - [4.12. Database ORM Schema Models](#412-database-orm-schema-models-appdbmodelspy)
5. [API Flow Examples](#5-api-flow-examples)
6. [Rate Limiting & Performance](#6-rate-limiting--performance)
7. [Environment Variables](#7-environment-variables)
8. [Testing the API](#8-testing-the-api)
9. [API Versioning](#9-api-versioning)

---

## 1. API Overview

The MONQ Procurement RAG API provides asynchronous endpoints for uploading, ingesting, classifying, querying, and managing procurement PDF documents.

- **Base URL**: `http://localhost:8000/api`
- **Authentication**: None required (assessment-only)
- **Content-Type**: `application/json` (except for `POST /documents` which requires `multipart/form-data`)

---

## 2. API Endpoints

### 2.1. Documents

#### GET /documents
**Description**: List all documents that are in the system along with their metadata and processing status.

**Request**:
```http
GET /api/documents HTTP/1.1
Host: localhost:8000
```

**Response**:
```json
[
  {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "contract.pdf",
    "category": "Contract",
    "chunk_count": 15,
    "title": "Master Service Agreement",
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

**Status Codes**:
- `200 OK`: Success

---

#### POST /documents
**Description**: Upload a PDF document for ingestion, chunking, embedding, and classification. Includes automatic content deduplication.

**Request**:
- Content-Type: `multipart/form-data`
- Body: `file` (PDF binary file)

**Response**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "classification": {
    "category": "Contract",
    "confidence": 0.92,
    "reasoning": "Contains agreement language with parties and signatures."
  },
  "chunk_count": 15,
  "status": "ready",
  "title": "Master Service Agreement",
  "summary": "Agreement between parties for consulting services...",
  "extractions": {
    "parties": {"value": "ACME Corp", "chunk_index": 0, "page_numbers": [1], "bbox": [{"page": 1, "x0": 10, "y0": 20, "x1": 100, "y1": 50}]},
    "effective_date": {"value": "2026-01-01", "chunk_index": 0, "page_numbers": [1], "bbox": [{"page": 1, "x0": 10, "y0": 60, "x1": 100, "y1": 80}]}
  }
}
```

**Status Codes**:
- `200 OK`: Success (includes deduplication handling)
- `400 Bad Request`: Invalid file type or empty PDF

---

#### GET /documents/{document_id}
**Description**: Retrieve full metadata, classification results, and extracted fields for a single document.

**Path Parameters**:
- `document_id`: UUID string of the document

**Response**: Same as POST `/documents` response.

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Document not found

---

#### PATCH /documents/{document_id}
**Description**: Rename a document's filename or title.

**Path Parameters**:
- `document_id`: UUID string of the document

**Request**:
```json
{
  "title": "Updated Master Service Agreement"
}
```

**Response**: Same as GET `/documents/{document_id}` response.

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Empty title
- `404 Not Found`: Document not found

---

#### DELETE /documents/{document_id}
**Description**: Delete a document and all associated chunks, chat sessions, and stored PDF file.

**Path Parameters**:
- `document_id`: UUID string of the document

**Response**:
```json
{
  "status": "deleted"
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Document not found

---

#### GET /documents/{document_id}/pdf
**Description**: Stream the original PDF file for rendering in the client viewer.

**Path Parameters**:
- `document_id`: UUID string of the document

**Response**:
- Content-Type: `application/pdf`
- Content-Disposition: `inline; filename="contract.pdf"`

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Document or PDF file not found

---

#### GET /documents/{document_id}/pages
**Description**: Retrieve per-page extracted text with line-level bounding box annotations.

**Path Parameters**:
- `document_id`: UUID string of the document

**Query Parameters**:
- `chunk_id` (optional): Highlight overlapping chunks on pages

**Response**:
```json
[
  {
    "page_number": 1,
    "text": "This is page one text...",
    "chunk_overlaps": [
      {
        "chunk_id": 1,
        "char_start": 0,
        "char_end": 100,
        "bbox": {"page": 1, "x0": 10.0, "y0": 20.0, "x1": 100.0, "y1": 50.0}
      }
    ]
  }
]
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Document not found

---

### 2.2. Chat

#### GET /documents/{document_id}/chat/history
**Description**: Retrieve the full chat history for a document.

**Path Parameters**:
- `document_id`: UUID string of the document

**Response**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the contract value?",
      "source_chunks": [],
      "created_at": "2026-01-15T10:35:00Z"
    },
    {
      "role": "assistant",
      "content": "The contract value is $500,000.",
      "source_chunks": [
        {"id": 1, "text": "The total contract value is $500,000...", "page_numbers": [1], "bbox": [{"page": 1, "x0": 10, "y0": 20, "x1": 100, "y1": 50}]}
      ],
      "created_at": "2026-01-15T10:35:05Z"
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Document not found

---

#### POST /documents/{document_id}/chat
**Description**: Ask a question about a document. Uses three-branch hybrid RAG (Retrieval-Augmented Generation) and cross-encoder reranking to ground the answer.

**Path Parameters**:
- `document_id`: UUID string of the document

**Request**:
```json
{
  "question": "What is the total contract value?"
}
```

**Response**:
```json
{
  "answer": "The total contract value is $500,000.",
  "source_chunks": [
    {
      "id": 1,
      "text": "The total contract value is $500,000...",
      "page_numbers": [1],
      "bbox": [{"page": 1, "x0": 10.0, "y0": 20.0, "x1": 100.0, "y1": 50.0}]
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Document not ready for chat
- `404 Not Found`: Document not found

---

### 2.3. Health

#### GET /health
**Description**: Health-check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

**Status Codes**:
- `200 OK`: Service healthy

---

## 3. Error Responses

All error responses follow the standard FastAPI detail structure:

```json
{
  "detail": "Human-readable error message"
}
```

Common status codes:
- `400 Bad Request`: Validation error or invalid file input
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Request payload validation failed
- `500 Internal Server Error`: Unexpected server exception

---

## 4. Data Models

### 4.1. ClassificationResult
| Field | Type | Description |
|---|---|---|
| `category` | string | Procurement category (e.g. Contract, RFP/RFQ, Quote/Proposal, Invoice, SLA, Amendment, NDA, Purchase Order, Other) |
| `confidence` | float | Classification confidence score (0.0–1.0) |
| `reasoning` | string | Explanation of classification decision |

### 4.2. DocumentResponse
| Field | Type | Description |
|---|---|---|
| `document_id` | string | UUID string of the document |
| `classification` | ClassificationResult | Classification details |
| `chunk_count` | integer | Total text chunks created |
| `status` | string | Status: `processing`, `ready`, or `failed` |
| `duplicate_of` | string / null | Original document UUID if content is duplicate |
| `title` | string / null | Extracted document title |
| `summary` | string / null | Auto-extracted document summary |
| `extractions` | object / null | Category-specific extracted fields with bboxes |

### 4.3. DocumentListItem
| Field | Type | Description |
|---|---|---|
| `document_id` | string | UUID string of the document |
| `filename` | string | Original PDF filename |
| `category` | string / null | Classified procurement category |
| `chunk_count` | integer | Total chunks created |
| `title` | string / null | Extracted document title |
| `created_at` | datetime / null | ISO timestamp of document creation |

### 4.4. RenameDocumentRequest
| Field | Type | Description |
|---|---|---|
| `filename` | string | New filename or title for the document |

### 4.5. ChatRequest
| Field | Type | Description |
|---|---|---|
| `question` | string | User's query about the procurement document |

### 4.6. SourceChunk
| Field | Type | Description |
|---|---|---|
| `id` | integer | Chunk database ID |
| `text` | string | Chunk text content with prepended section context |
| `page_numbers` | array[integer] | List of page numbers spanned |
| `bbox` | array[object] | List of bounding boxes for visual highlighting |

### 4.7. ChatResponse
| Field | Type | Description |
|---|---|---|
| `answer` | string | Grounded LLM response answer text |
| `source_chunks` | array[SourceChunk] | List of cited source chunks used to formulate answer |

### 4.8. ChatHistoryMessage
| Field | Type | Description |
|---|---|---|
| `role` | string | Message role (`user` or `assistant`) |
| `content` | string | Message text content |
| `source_chunks` | array[object] | List of cited source chunks for assistant turns |
| `created_at` | datetime / null | ISO timestamp of message creation |

### 4.9. ChatHistoryResponse
| Field | Type | Description |
|---|---|---|
| `messages` | array[ChatHistoryMessage] | Complete list of chat turns in the session |

### 4.10. PageChunkOverlap
| Field | Type | Description |
|---|---|---|
| `chunk_id` | integer | ID of overlapping chunk |
| `char_start` | integer | Start character index on page |
| `char_end` | integer | End character index on page |
| `bbox` | object / null | Bounding box coordinates `{page, x0, y0, x1, y1}` |

### 4.11. PageResponse
| Field | Type | Description |
|---|---|---|
| `page_number` | integer | 1-indexed page number |
| `text` | string | Extracted page text content |
| `chunk_overlaps` | array[PageChunkOverlap] | Annotations for chunk overlays on page |

---

### 4.12. Database ORM Schema Models (`app/db/models.py`)

#### `documents` Table
- `id`: `String(36)`, Primary Key (UUID)
- `filename`: `String(255)`, Not Null
- `status`: `String(50)`, Default `"processing"`
- `category`: `String(100)`, Nullable
- `confidence`: `Float`, Nullable
- `reasoning`: `Text`, Nullable
- `content_hash`: `String(64)`, Indexed (SHA-256 for deduplication)
- `chunk_count`: `Integer`, Default `0`
- `file_data`: `LargeBinary`, Nullable (Optional DB-level binary BLOB)
- `page_texts`: `VectorType` (JSON-serialized per-page text list)
- `title`: `Text`, Nullable
- `summary`: `Text`, Nullable
- `extractions`: `VectorType` (JSON-serialized key-value field extractions)
- `created_at`: `DateTime(timezone=True)`, Server Default `NOW()`

#### `chunks` Table
- `id`: `Integer`, Primary Key
- `document_id`: `String(36)`, Foreign Key $\rightarrow$ `documents.id` (Indexed, ON DELETE CASCADE)
- `chunk_index`: `Integer`, Not Null
- `text`: `Text`, Not Null (Heading-enriched text)
- `embedding`: `VectorType` (JSON-serialized 384-dim float array)
- `entities`: `VectorType` (JSON-serialized spaCy NER dicts)
- `page_numbers`: `VectorType` (JSON-serialized page list)
- `char_start`: `Integer`, Nullable
- `char_end`: `Integer`, Nullable
- `bbox`: `VectorType` (JSON-serialized bounding box list)

#### `chat_sessions` Table
- `id`: `Integer`, Primary Key
- `document_id`: `String(36)`, Foreign Key $\rightarrow$ `documents.id` (ON DELETE CASCADE)
- `created_at`: `DateTime(timezone=True)`, Server Default `NOW()`

#### `chat_messages` Table
- `id`: `Integer`, Primary Key
- `session_id`: `Integer`, Foreign Key $\rightarrow$ `chat_sessions.id` (ON DELETE CASCADE)
- `role`: `String(50)`, Not Null (`user` / `assistant`)
- `content`: `Text`, Not Null
- `source_chunks`: `VectorType` (JSON-serialized cited source chunks)
- `created_at`: `DateTime(timezone=True)`, Server Default `NOW()`

---

## 5. API Flow Examples

### Upload Flow
1. `POST /api/documents` with PDF file payload.
2. Backend processes synchronously: PDF text extraction $\rightarrow$ heading detection $\rightarrow$ chunking $\rightarrow$ embedding $\rightarrow$ classification $\rightarrow$ SQLite persistence.
3. Response returns metadata, classification, summary, and extracted key-value fields.

### Chat Flow
1. `GET /api/documents/{id}/chat/history` (optional, loads previous messages).
2. `POST /api/documents/{id}/chat` with user query.
3. Backend runs three-branch hybrid retrieval (BM25 + Semantic + spaCy NER) $\rightarrow$ score fusion $\rightarrow$ cross-encoder reranking $\rightarrow$ LLM generation.
4. Response returns answer text and source chunk bounding boxes.

---

## 6. Rate Limiting & Performance

- **Rate Limiting**: None implemented (assessment-only)
- **Chunk Size**: 1000 characters (overlap: 150 characters)
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **LLM Provider**: `llama-3.3-70b-versatile` (Groq API)
- **Reranker Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Top K**: 5 final context chunks

---

## 7. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | API key for Groq LLM service | Required |
| `EMBEDDING_MODEL_NAME` | Sentence-transformer model name | `all-MiniLM-L6-v2` |
| `GROQ_MODEL_NAME` | Groq model identifier | `llama-3.3-70b-versatile` |
| `TOP_K_CHUNKS` | Final context chunks for LLM | `5` |
| `HYBRID_ALPHA` | Weight between BM25 and semantic (0–1) | `0.3` |
| `RERANK_CANDIDATES` | Candidate pool before reranking | `20` |
| `PDF_STORAGE_BACKEND` | Storage backend type | `local` |
| `PDF_STORAGE_PATH` | Storage directory for PDF files | `./storage/pdfs` |

---

## 8. Testing the API

### Using cURL

**Upload a document:**
```bash
curl -X POST http://localhost:8000/api/documents \
  -F "file=@contract.pdf"
```

**Ask a question:**
```bash
curl -X POST http://localhost:8000/api/documents/{document_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the contract value?"}'
```

### Using the Frontend
- Navigate to `http://localhost:5173`.
- Upload a PDF via drag-and-drop or file picker.
- Select a document to view metadata extractions and open the chat view.
- Submit questions in the chat panel and observe source highlights in the PDF viewer.

---

## 9. API Versioning

- **Current Version**: v1 (implicit via `/api` prefix)
- **Future Versions**: `/api/v2` if breaking API contract changes are introduced
