# AI Translation API

Standalone FastAPI service for translating and summarizing editor content with Ollama-hosted language models. It supports HTML-aware translation, vocabulary and style rules, Google OAuth bearer authentication, and an optional ChromaDB RAG subsystem.

## Quick Start

### Standalone API and Ollama

From the repository root:

```bash
make api-standalone-up
```

This builds the API image, starts Ollama, pulls the `aya` model, and waits for the API health check. The standalone API is available at `http://localhost:8444`. The container listens on port `443` internally, but the application itself serves plain HTTP; TLS is not configured in Uvicorn.

The standalone setup uses the real Ollama service and does not start the Editor, Backend-Editor, proxy, Redis, Qdrant, or the root compose stack. The shared `ai-translation-ollama-data` volume preserves downloaded models.

```bash
make api-standalone-test   # real health and translation request
make api-standalone-down   # stop and remove API and Ollama containers
make api-standalone-clean  # also remove the temporary image and network
```

For a complete manual request, see [`API Translation standlone test.md`](../API%20Translation%20standlone%20test.md). For the integrated stack, see [`RUNNING_INTEGRATED.md`](../RUNNING_INTEGRATED.md).

### Local development

Install the dependencies from `app/requirements.txt`, configure the environment variables below, and run Uvicorn from the `app` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 443
```

## API Endpoints

| Method | Endpoint          | Authentication | Purpose                                             |
| ------ | ----------------- | -------------- | --------------------------------------------------- |
| `GET`  | `/health`         | Public         | Reports API and Ollama connectivity                 |
| `POST` | `/api/translate`  | Bearer token   | Translates title, body, and section                 |
| `POST` | `/api/summary`    | Bearer token   | Summarizes article content                          |
| `GET`  | `/api/rag/status` | Public         | Reports ChromaDB availability and collection counts |
| `POST` | `/api/rag/ingest` | Bearer token   | Ingests CMS articles into ChromaDB                  |

### Translation request

```json
{
  "title": "Airport slots",
  "body": "Airport slots help coordinate demand and capacity.",
  "section": "Technology",
  "target_language": "Spanish",
  "model": "aya"
}
```

Successful responses have this shape:

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

The service preserves HTML structure when translating HTML content, sanitizes input and model output, and uses the configured default model before any backup or request-level model.

### Summary request

```json
{
  "title": "Article title",
  "body": "Article body",
  "language": "en"
}
```

The response contains `success` and an `article` summary string.

## Authentication

Protected routes use an `Authorization: Bearer <token>` header. In normal deployments, `app/utils/auth.py` validates Google OAuth access tokens with Google's token and user-info endpoints and requires a verified email.

For local standalone testing, set `DEV_MODE=true`. This bypasses Google validation and accepts any non-empty bearer value, for example:

```text
Authorization: Bearer standalone-test-token
```

This development behavior must not be used as production authentication.

## Configuration

- `ALLOWED_ORIGINS`: CORS origins, supplied as a comma-separated or Python/JSON-style list.
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

## Architecture

```text
app/
├── main.py                 # FastAPI setup, CORS, startup checks, routes
├── routers/                # HTTP endpoints
├── services/               # Translation and summary orchestration
├── schemas/                # Pydantic request and response models
├── utils/translation/      # Prompts, Ollama calls, HTML translation
├── utils/summary/          # Summary prompts and Ollama helpers
├── utils/rag_service/      # ChromaDB queries, context, and ingestion
├── utils/auth.py           # Google OAuth bearer-token validation
├── data/                   # Vocabulary and abbreviation JSON files
└── config.py               # Environment and runtime configuration
```

At startup the API checks Ollama and attempts a model warmup. ChromaDB is optional: its status and ingestion routes are available, but automatic startup ingestion is not enabled. The active translation prompt uses vocabulary/style rules; RAG context injection is not fully wired into every translation and summary prompt yet.

## Tests and Documentation

Run the unit and integration tests from `AI-Translation-API/`:

```bash
pytest
```

- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md): detailed API examples and schemas.
- [`docs/INTEGRATION_TESTING.md`](docs/INTEGRATION_TESTING.md): live-container integration tests.
- [`docs/RAG_IMPLEMENTATION.md`](docs/RAG_IMPLEMENTATION.md): ChromaDB ingestion and retrieval details.
- [`AITranslation-Api Architecture.md`](../AITranslation-Api%20Architecture.md): current architecture and implementation notes.
