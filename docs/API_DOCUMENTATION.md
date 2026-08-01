# AI Translation API

`AI-Translation-API` is a FastAPI service for translating and summarizing editor content with Ollama-hosted language models. It supports HTML-aware translation, vocabulary and style rules, Google OAuth bearer authentication, and an optional ChromaDB retrieval subsystem.

## Architecture

```text
Editor / client
    |  authenticated HTTP requests
    v
FastAPI
    |- routers/                 # translate, summary, and RAG routes
    |- services/                # translation and summary orchestration
    |- schemas/                 # Pydantic request/response models
    |- utils/translation/       # prompts, Ollama calls, HTML translation
    |- utils/summary/           # summary prompts and Ollama helpers
    |- utils/rag_service/       # ChromaDB queries and CMS ingestion
    |- utils/auth.py            # Google OAuth bearer-token validation
    |- data/                    # vocabulary and abbreviation JSON files
    `- config.py                # environment configuration
```

At startup the service checks Ollama and attempts a model warmup. ChromaDB is optional. Startup does not currently perform automatic RAG ingestion, and RAG context is not fully wired into every active translation and summary prompt. Vocabulary and style rules remain part of the active translation prompt.

## Endpoints

| Method | Path              | Authentication | Description                                         |
| ------ | ----------------- | -------------- | --------------------------------------------------- |
| `GET`  | `/health`         | Public         | Reports API and Ollama connectivity                 |
| `POST` | `/api/translate`  | Bearer token   | Translates title, body, and section                 |
| `POST` | `/api/summary`    | Bearer token   | Summarizes article content                          |
| `GET`  | `/api/rag/status` | Public         | Reports ChromaDB availability and collection counts |
| `POST` | `/api/rag/ingest` | Bearer token   | Ingests CMS articles into ChromaDB                  |

### `GET /health`

```bash
curl http://localhost:8444/health
```

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

### `POST /api/translate`

Request fields are `title`, `body`, `section`, `target_language`, and `model`:

```json
{
  "title": "Airport slots",
  "body": "Airport slots help coordinate demand and capacity.",
  "section": "Technology",
  "target_language": "Spanish",
  "model": "aya"
}
```

Response:

```json
{
  "translated_text": {
    "title": "...",
    "body": "...",
    "section": "..."
  },
  "success": true,
  "model_used": "aya"
}
```

The service detects HTML per field. HTML fields are translated while preserving structure and then sanitized. Plain fields are sanitized, translated, parsed into the three response fields, and sanitized again. The model selection order is the configured default model, configured backup model, then the request-level model.

### `POST /api/summary`

Request:

```json
{
  "title": "Article title",
  "body": "Article body",
  "language": "en"
}
```

Response:

```json
{
  "article": "Summary text",
  "success": true
}
```

### `GET /api/rag/status`

This public endpoint reports ChromaDB availability and collection counts:

```json
{
  "chroma_available": true,
  "collections": {
    "en": { "count": 12 },
    "es": { "count": 10 }
  }
}
```

### `POST /api/rag/ingest`

This route manually fetches CMS articles, chunks them, creates Ollama embeddings, and upserts them into the `rag_en` and `rag_es` ChromaDB collections. The CMS request uses `X-RAG-Token: CMS_RAG_TOKEN`.

## Authentication

Protected routes require:

```text
Authorization: Bearer <Google access token>
```

In normal deployments, `app/utils/auth.py` validates the Google OAuth access token through Google's token-info and user-info endpoints and requires a verified email. `GOOGLE_CLIENT_ID`, when configured, is checked against the token audience.

When `DEV_MODE=true`, Google validation is bypassed and a local developer user is returned. This is the mode used by the standalone container test and must not be used as production authentication:

```text
Authorization: Bearer standalone-test-token
```

## Ollama and RAG

Ollama generation uses `POST {OLLAMA_BASE_URL}/api/generate` with a non-streaming request. The default standalone model is `aya`; other models can be configured. Embeddings use `POST {OLLAMA_BASE_URL}/api/embeddings` with `EMBED_MODEL`.

RAG infrastructure includes:

- `rag_en` and `rag_es` ChromaDB collections.
- CMS article fetching and sliding-window chunking.
- Vocabulary, abbreviation, and style-rule data under `app/data/`.
- Manual ingestion through `/api/rag/ingest`.

If ChromaDB is unavailable, the API can continue without retrieved context. RAG startup checks and automatic ingestion are not active in the current application path.

## Configuration

- `ALLOWED_ORIGINS`: CORS origins as a comma-separated or Python/JSON-style list.
- `CORS_METHODS`, `CORS_ALLOW_HEADERS`: CORS settings.
- `GOOGLE_CLIENT_ID`: Google OAuth client ID/audience.
- `DEV_MODE`, `TESTING_MODE`: development and test behavior.
- `OLLAMA_BASE_URL`: Ollama URL, such as `http://ollama:11434` in Docker.
- `OLLAMA_DEFAULT_MODEL`: primary generation model, usually `aya`.
- `OLLAMA_BACKUP_MODEL`: optional fallback model.
- `CHROMA_HOST`, `CHROMA_PORT`: ChromaDB service location.
- `EMBED_MODEL`: embedding model, default `nomic-embed-text`.
- `RAG_N_RESULTS`: number of passages to retrieve.
- `CMS_RAG_URL`, `CMS_RAG_TOKEN`: CMS ingestion endpoint and shared secret.

## Standalone Docker test

From the repository root:

```bash
make api-standalone-up
make api-standalone-test
make api-standalone-down
```

The API is published at `http://localhost:8444`; the container's internal port is `443`, but the application serves plain HTTP and is not configured for TLS. See [`API  TEST Instructions.md`](API%20%20TEST%20Instructions.md) for the full Postman, curl, Jest, cleanup, and troubleshooting workflow.

## Testing and source documentation

Run the Python test suite from `AI-Translation-API/`:

```bash
pytest
```

Relevant source areas include:

- `app/services/translation.py`: translation orchestration.
- `app/services/summary.py`: summary orchestration.
- `app/utils/translation/`: HTML handling, prompts, and Ollama calls.
- `app/utils/summary/`: summary prompts and Ollama calls.
- `app/utils/rag_service/`: ChromaDB queries and ingestion.
- `app/data/`: vocabulary and abbreviation data.
