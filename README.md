# Agentic RAG Platform

[Live Demo](https://agent-rag-frontend.onrender.com) · [API Documentation](https://agent-rag-asr6.onrender.com/docs)

A full-stack agentic Retrieval-Augmented Generation platform that lets users upload PDF documents, ask grounded questions, retrieve cited passages, access current web information, and continue conversations with persistent memory.

## Features

- Uploads and processes PDF documents
- Extracts text and divides it into retrieval-friendly chunks
- Generates semantic embeddings using FastEmbed
- Stores and searches vectors in Qdrant
- Produces grounded answers using Gemini
- Provides document and page-level citations
- Uses LangGraph to select document, web, or combined retrieval
- Searches current information using DDGS
- Preserves conversation memory in PostgreSQL
- Displays usage and performance analytics with Recharts
- Evaluates retrieval using hit rate, mean reciprocal rank, and similarity
- Supports document deletion across PostgreSQL, file storage, and Qdrant
- Includes FastAPI documentation and health monitoring

## Architecture

```mermaid
flowchart LR
    A[React Frontend] --> B[FastAPI Backend]
    B --> C[PDF Extraction and Chunking]
    C --> D[FastEmbed]
    D --> E[Qdrant Vector Database]

    B --> F[LangGraph Workflow]
    F --> E
    F --> G[Live Web Search]
    F --> H[Gemini]
    F --> I[PostgreSQL Memory]

    B --> J[Analytics and Evaluation]
```

## Agent Workflow

For every question, LangGraph:

1. Embeds the user’s question.
2. Retrieves similar PDF chunks from Qdrant.
3. Decides whether to use documents, live web search, or both.
4. Loads previous messages from PostgreSQL.
5. Sends the selected context to Gemini.
6. Returns an answer with document and web sources.
7. Saves the updated conversation for follow-up questions.

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- LangGraph
- Gemini API
- FastEmbed
- Qdrant
- PyPDF
- DDGS

### Frontend

- React
- Vite
- Tailwind CSS
- Recharts

### Deployment

- Render — FastAPI backend and React frontend
- Neon — PostgreSQL database
- Qdrant Cloud — vector database

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Check API and database health |
| `GET` | `/api/v1/documents` | List documents |
| `POST` | `/api/v1/documents` | Upload and process a PDF |
| `GET` | `/api/v1/documents/{document_id}` | Get one document |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete a document |
| `POST` | `/api/v1/questions/ask` | Run the agentic RAG workflow |
| `GET` | `/api/v1/analytics/summary` | Retrieve dashboard statistics |
| `POST` | `/api/v1/evaluation/run` | Evaluate retrieval quality |

## Retrieval Evaluation

The evaluation system accepts test questions and expected terms, searches the most relevant Qdrant chunks, and reports:

- Hit rate
- Mean reciprocal rank
- Average top similarity
- Found and missing expected terms
- Individual passed or failed cases

## Local Setup

### 1. Start PostgreSQL and Qdrant

```bash
docker compose up -d
```

### 2. Configure the backend

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST/DATABASE
QDRANT_URL=http://localhost:6333
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.1-flash-lite
FRONTEND_URL=http://localhost:5173
```

For Qdrant Cloud, also add:

```env
QDRANT_API_KEY=YOUR_QDRANT_API_KEY
```

### 3. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Backend documentation:

```text
http://127.0.0.1:8000/docs
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

## Security

Secret values are stored in environment variables and are excluded from Git. Uploaded PDFs are also excluded from version control.

## Author

**Thummala Siri Chandana**

- GitHub: [siri-thummala](https://github.com/siri-thummala)