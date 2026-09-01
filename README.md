# AI Translation API

FastAPI service for translating and summarizing article content with Ollama. Translation supports plain text and HTML input, preserves supported HTML structure, sanitizes content, and applies the vocabulary and abbreviation rules in `app/data/`.

## Quick start

From the repository root:

```bash
make api-standalone-up
```

The API is available at `http://localhost:8444`. The container publishes port `443`, but Uvicorn serves plain HTTP; TLS is not configured by this service.

```bash
make api-standalone-test  # Jest smoke test
make api-standalone-logs-fastapi
make api-standalone-down
make api-standalone-clean # also removes the temporary image/network
```

For local development, install `app/requirements.txt`, configure the environment variables below, and run from `AI-Translation-API/app`:

```bash
uvicorn main:app --host 0.0.0.0 --port 443
```

## Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | Public | Reports API and Ollama status |
| `POST` | `/api/translate` | Bearer token | Translates title, body, and section |
| `POST` | `/api/summary` | Bearer token | Generates an article summary |
| `GET` | `/api/rag/status` | Public | Reports ChromaDB availability and collection counts |
| `POST` | `/api/rag/ingest` | Bearer token | Re-ingests CMS articles into ChromaDB |

Interactive OpenAPI documentation is available at `/docs`.

### Health

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

### Translation

Required fields are `title`, `body`, and `section`. `target_language` defaults to `Spanish`. The `model` field is accepted for compatibility, but the current service uses `OLLAMA_DEFAULT_MODEL` when configured and otherwise `llama3.2`.

```bash
curl -X POST http://localhost:8444/api/translate \
  -H 'Authorization: Bearer standalone-test-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Airport slots",
    "body": "<p>Airport slots help coordinate demand and capacity.</p>",
    "section": "Technology",
    "target_language": "Spanish"
  }'
```

Response:

```json
{
  "translated_text": {
    "title": "...",
    "body": "<p>...</p>",
    "section": "..."
  },
  "status": 200,
  "model_used": "aya"
}
```

Each translated field is either a string or a list of structured segments. HTML segments can include `id`, `tag`, `text`, `src`, `alt`, and `href`.

### Summary

Required fields are `title` and `body`; `language` defaults to `en`.

```bash
curl -X POST http://localhost:8444/api/summary \
  -H 'Authorization: Bearer standalone-test-token' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Article title","body":"Article body","language":"en"}'
```

```json
{
  "article": "Summary text",
  "success": true
}
```

### RAG

`GET /api/rag/status` returns:

```json
{
  "chroma_available": true,
  "collections": {
    "en": { "count": 12 },
    "es": { "count": 10 }
  }
}
```

`POST /api/rag/ingest` fetches English and Spanish articles from `CMS_RAG_URL`, chunks and embeds them, and upserts them into ChromaDB. The CMS request uses `X-RAG-Token: CMS_RAG_TOKEN`. Ingestion is manual; startup does not automatically populate RAG collections.

## Authentication

Protected endpoints require:

```text
Authorization: Bearer <Google access token>
```

Normal deployments validate the token with Google and require a verified email. With `DEV_MODE=true`, validation is bypassed and any non-empty bearer token is accepted for local development. Do not enable this mode in production.

## Configuration

- `ALLOWED_ORIGINS`: CORS origins; comma-separated or Python/JSON-style list.
- `CORS_METHODS`, `CORS_ALLOW_HEADERS`: CORS settings.
- `GOOGLE_CLIENT_ID`: optional Google OAuth audience.
- `DEV_MODE`, `TESTING_MODE`: development and test behavior.
- `OLLAMA_BASE_URL`: Ollama URL, such as `http://ollama:11434` in Docker.
- `OLLAMA_DEFAULT_MODEL`: primary generation model; standalone setup uses `aya`.
- `OLLAMA_BACKUP_MODEL`: optional model setting used by summary helpers.
- `OLLAMA_REQUEST_TIMEOUT`: timeout in seconds; default `900`.
- `CHROMA_HOST`, `CHROMA_PORT`: ChromaDB location; defaults `chroma:8000`.
- `EMBED_MODEL`: embedding model; default `nomic-embed-text`.
- `RAG_N_RESULTS`: retrieval count; default `3`.
- `CMS_RAG_URL`, `CMS_RAG_TOKEN`: CMS ingestion endpoint and shared secret.

## Tests and documentation

Run the Python tests from this directory:

```bash
pytest
```

- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md): expanded API reference.
- [`docs/RAG_IMPLEMENTATION.md`](docs/RAG_IMPLEMENTATION.md): RAG implementation details.
- [`../RUNNING_INTEGRATED.md`](../RUNNING_INTEGRATED.md): integrated stack instructions.
