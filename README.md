# MONQ Procurement RAG

AI-powered procurement document platform. Upload a PDF → extract & chunk text → embed chunks → classify into a procurement type → chat with the document via grounded RAG.

## Requirements

- Python 3.11+
- Node.js 20+
- Groq API key (free at https://console.groq.com)

## Architecture

For in-depth architectural details, design principles, and data flow specifications, see [docs/architecture.md](docs/architecture.md).

## Testing

For testing strategies, test suite breakdowns, and execution commands, see [docs/testing.md](docs/testing.md).

## API Documentation

For full API documentation, endpoint specifications, and system design overview, see [docs/API.md](docs/API.md).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/markbosire/monq-procurement-rag.git
cd monq-procurement-rag
```

### 2. Frontend Setup

First, install dependencies for the frontend application:

```bash
cd frontend
npm install
```

Start the frontend development server:

```bash
npm run dev
```

The frontend server runs on: **http://localhost:5173**

### 3. Backend Setup

#### Quick start (cross-platform):

```bash
cd backend
python setup.py
```

This creates a virtual environment, installs dependencies, downloads the spaCy model, and copies `.env.example` to `.env`.

#### Manual setup:

##### Linux / macOS:

```bash
cd ../backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
```

##### Windows (Command Prompt / PowerShell):

```cmd
cd ..\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env
```

Edit `.env` and set your `GROQ_API_KEY`. (Default database URL points to local SQLite `sqlite:///./procurement.db`).

Start the backend server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The backend API server runs on: **http://localhost:8000** (Swagger docs available at http://localhost:8000/docs).

## How to Use the System

1. Open your browser and navigate to **http://localhost:5173**.
2. **Upload a PDF**: Drag & drop or select a procurement document (e.g. RFP, Contract, SOW).
3. **View Extraction & Metadata**: See auto-classified procurement category, summaries, and extracted metadata fields.
4. **Chat with Document**: Ask questions about the document and receive grounded AI answers with source highlights.

![System Demo](docs/assets/DEMO.gif)

## AI Usage Disclosure

For details on how AI search agents, prototyping tools, boilerplate generators, testing suites, and documentation tools were utilized, see [docs/AI_USE.md](docs/AI_USE.md).
