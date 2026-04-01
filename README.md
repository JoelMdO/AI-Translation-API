# AI Translation & Summary API (with RAG)

Production-ready FastAPI service for translation and summarization, featuring Retrieval-Augmented Generation (RAG) with ChromaDB, bilingual vocabulary, and style rules. Integrates Ollama LLMs and Google Authentication.

## Quick Start

1. **Environment Setup**:
1. **Environment Setup**:

   ```bash
   cp .env.production .env
   # Edit .env with your Google Client ID and RAG/ChromaDB settings
   ```

1. **Docker Deployment**:
   ```bash
   docker-compose up -d
   ```

## API Endpoints

### Authentication

- `/api/translate` and `/api/summary` require a JWT Bearer token (obtainable via Google Sign-In)
- `/api/rag/ingest` requires a Google ID token (admin only)

### Endpoints

- **POST `/api/translate`**: Translate text using RAG-enriched prompt
- **POST `/api/summary`**: Summarize article content using RAG-enriched prompt
- **GET `/api/rag/status`**: Check ChromaDB health and collection counts
- **POST `/api/rag/ingest`**: Trigger re-ingestion of CMS articles into ChromaDB (admin)
- **GET `/health`**: Public health check endpoint

## Architecture & Folder Structure

```
API/app/
├── main.py                # App entrypoint, startup checks, router registration
├── routers/               # translate_router.py, summary_router.py, rag_router.py
├── services/              # translation.py, summary.py (business logic)
├── utils/
│     ├── summary/         # Summary prompt/logic helpers
│     ├── translation/     # Translation prompt/logic helpers
│     ├── rag_service/     # ChromaDB client, context formatting
│     ├── rag_ingestion.py # CMS fetch, chunking, ingestion
│     ├── rag_file_data_transform/ # PDF/CSV vocabulary extraction tools
│     ├── load_vocabulary.py # Loads vocabulary and style rules
│     └── auth.py          # Google OAuth/JWT utilities
├── data/
│     ├── vocabulary.json  # Bilingual glossary + style rules
│     └── abbreviation.json # Acronym glossary
└── config.py              # Environment/config management
```

## Environment Variables

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `OLLAMA_BASE_URL`: Ollama service URL
- `OLLAMA_DEFAULT_MODEL`: Primary LLM model (e.g. `aya`)
- `OLLAMA_BACKUP_MODEL`: Fallback LLM model (e.g. `llama3.2`)
- `ALLOWED_ORIGINS`: CORS allowed origins
- `CHROMA_HOST`, `CHROMA_PORT`: ChromaDB service
- `EMBED_MODEL`: Embedding model for ChromaDB (default: `nomic-embed-text`)
- `RAG_N_RESULTS`: Number of passages to retrieve from ChromaDB
- `CMS_RAG_URL`: Django CMS endpoint for RAG corpus
- `CMS_RAG_TOKEN`: Shared secret for CMS authentication

## Deployment

- Uses Docker with nginx for HTTPS termination and FastAPI for the API service
- ChromaDB and CMS run as additional services for RAG enrichment

---

For full API details and request/response examples, see `docs/API_DOCUMENTATION.md`.
