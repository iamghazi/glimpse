# RAG Production App - Technical Reference

## Overview
A Retrieval-Augmented Generation (RAG) application for question-answering over PDF documents. Users upload PDFs which are chunked, embedded, and stored in a vector database. Questions retrieve relevant chunks and generate AI-powered answers with source attribution.

## Architecture

```
Streamlit UI (8501) → Inngest Events → FastAPI (8000)
                          ↓
                    Inngest Dev Server (8288)
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    Qdrant (6333)    Gemini API      Local Files
```

## Technology Stack
- **Backend**: FastAPI 0.115.6, Python 3.10+, Inngest 0.6.1
- **Frontend**: Streamlit 1.41.1
- **Vector DB**: Qdrant (Docker)
- **AI**: Google Gemini (gemini-embedding-001, gemini-2.0-flash-exp)
- **Processing**: LlamaIndex (PDFReader, SentenceSplitter)
- **Package Manager**: uv

## Components

### 1. FastAPI Backend (`main.py`)

#### Inngest Function: `rag_ingest_pdf`
```python
Event: rag/ingest_pdf
Input: {"file_path": str}
Steps:
  1. Load PDF and chunk (1000 chars, 200 overlap) via SentenceSplitter
  2. Generate 3072-dim embeddings via Gemini
  3. Store in Qdrant with deterministic UUID from content hash
Output: {"chunks_count": int}
```

#### Inngest Function: `rag_query_pdf_ai`
```python
Event: rag/query_pdf_ai
Input: {"query": str, "top_k": int}
Steps:
  1. Embed query via Gemini
  2. COSINE similarity search in Qdrant
  3. Generate answer via Gemini with top-k context
Output: {"answer": str, "sources": list[str], "contexts_count": int}
```

### 2. Streamlit UI (`streamlit_app.py`)
- **PDF Upload**: Saves to `uploads/{timestamp}_{filename}.pdf`, triggers `rag/ingest_pdf`, polls 60s
- **Q&A Interface**: Text input + top_k slider (1-10, default 3), triggers `rag/query_pdf_ai`, polls 30s
- **Polling**: HTTP GET to Inngest API every 1s until completion or timeout

### 3. Data Loader (`data_loader.py`)
```python
load_and_chunk_pdfs(pdf_paths: list[str]) -> list[RAGChunkAndSrc]
  - LlamaIndex PDFReader
  - SentenceSplitter(chunk_size=1000, chunk_overlap=200)

embed_texts(texts: list[str]) -> list[list[float]]
  - Google Gemini gemini-embedding-001
  - Returns 3072-dimensional vectors
```

### 4. Vector DB (`vector_db.py`)
```python
class QdrantStorage:
  __init__(host="localhost", port=6333)
    - Creates "docs" collection (3072-dim, COSINE)

  upsert(chunks_with_embeddings, batch_size=100)
    - Deterministic UUID from content hash
    - Payload: {text: str, source: str}

  search(query_embedding, top_k=3) -> RAGSearchResult
    - Returns contexts and sources
```

## Data Models (`custom_types.py`)
```python
class RAGChunkAndSrc(BaseModel):
    text: str
    source: str

class RAGUpsertResult(BaseModel):
    chunks_count: int

class RAGSearchResult(BaseModel):
    contexts: list[str]
    sources: list[str]

class RAGQueryResult(BaseModel):
    answer: str
    sources: list[str]
    contexts_count: int
```

## Data Flow

### Ingestion
```
PDF upload → uploads/{timestamp}_{name}.pdf
  → Inngest: rag/ingest_pdf
  → PDFReader → SentenceSplitter (1000/200)
  → Gemini embed (3072-dim)
  → Qdrant upsert (UUID, vector, {text, source})
```

### Query
```
User question → Inngest: rag/query_pdf_ai
  → Gemini embed query
  → Qdrant COSINE search (top-k)
  → Gemini generate with context
  → Return answer + sources
```

## Qdrant Schema
```python
Collection: "docs"
Point: {
    "id": "uuid-v5-from-content-hash",
    "vector": [float; 3072],
    "payload": {
        "text": "chunk content",
        "source": "uploads/file.pdf"
    }
}
Config: COSINE distance, HNSW index
Storage: ./qdrant_storage/ (Docker volume)
```

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=required
INNGEST_API_BASE=http://localhost:8288  # optional, defaults to local
```

### Chunking Parameters (`data_loader.py`)
- chunk_size: 1000 characters
- chunk_overlap: 200 characters
- Splitter: SentenceSplitter (respects sentence boundaries)

### Vector DB Settings (`vector_db.py`)
- Host: localhost:6333
- Collection: docs
- Distance: COSINE
- Dimension: 3072

## Error Handling
- Inngest: 3 automatic retries with exponential backoff
- Streamlit: Timeout errors (30s/60s) shown to user
- Qdrant: Auto-creates collection if missing
- Gemini: Rate limiting handled by SDK

## Performance
- Ingestion: ~3-5s per 10-page PDF (sequential embedding)
- Query: ~3-5s (0.5s embed + 0.01-0.1s search + 2-4s generation)
- Limitations: Sequential processing, single Qdrant instance, polling-based updates

## Security
- API keys in `.env` (gitignored)
- No authentication/authorization
- No file size limits
- No rate limiting
- Shared upload directory
- Local development only

## File Structure
```
ragproductionapp/
├── main.py              # FastAPI + Inngest functions
├── streamlit_app.py     # Streamlit UI
├── data_loader.py       # PDF processing & embedding
├── vector_db.py         # Qdrant wrapper
├── custom_types.py      # Pydantic models
├── pyproject.toml       # Dependencies
├── .env                 # API keys (GEMINI_API_KEY)
├── qdrant_storage/      # Qdrant data (persisted)
└── uploads/             # Uploaded PDFs (runtime)
```

## Key Dependencies
```
fastapi ^0.115.6
google-genai >=1.55.0
inngest ^0.6.1
llama-index-core ^0.12.18
llama-index-readers-file ^0.4.2
qdrant-client ^1.13.1
streamlit ^1.41.1
```

## Running the Application
1. Qdrant: `docker run -d --name qdrant -p 6333:6333 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant`
2. Inngest: `npx inngest-cli@latest dev`
3. FastAPI: `uv run fastapi dev ./main.py`
4. Streamlit: `uv run streamlit run ./streamlit_app.py`

Access: UI (8501), API (8000), Inngest Dashboard (8288), Qdrant (6333)
