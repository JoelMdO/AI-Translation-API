# RAG Implementation — Blog Editor

## Overview

This document describes the Retrieval-Augmented Generation (RAG) system added to the Blog Editor's FastAPI translation and summarization pipeline.

The RAG system enriches every translation and summary request with:

- **Semantic passages** retrieved from published CMS articles (grammar/style reference via ChromaDB + Ollama embeddings)
- **Bilingual vocabulary** (EN/ES glossary always injected)
- **Style rules** per language (tone, punctuation, sentence structure)

The intent is to make the LLM produce output that is consistent with the existing blog's voice and terminology.

---

## Architecture

```
Editor (Next.js)
       │  POST /api/translate | /api/resume
       ▼
FastAPI (/API/app)
   ├── services/translation.py
   │       │ 1. query ChromaDB for style passages
   │       │ 2. load vocabulary.json
   │       │ 3. format context block
   │       │ 4. call Ollama (aya) with enriched prompt
   │       └──► Ollama (aya 8B / llama3.2 fallback)
   └── utils/rag_service.py ──► ChromaDB (port 8001)
                                   ▲ ingested by
                            utils/rag_ingestion.py
                                   │ fetches
Content-Manager-Editor-Backend (Django)
   └── /articles/rag-corpus/?lang=en|es
```

### Services (Docker)

| Service | Image / Build                      | Internal Port | External Port   |
| ------- | ---------------------------------- | ------------- | --------------- |
| editor  | `./Editor`                         | 8000          | 8000            |
| fastapi | `./API/app`                        | 443           | 443             |
| ollama  | `ollama/ollama:latest`             | 11434         | 11434           |
| chroma  | `chromadb/chroma:latest`           | 8000          | 8001            |
| cms     | `./Content-Manager-Editor-Backend` | 8000          | 127.0.0.1:8002  |
| cms-db  | `postgres:16-alpine`               | 5432          | (internal only) |
| proxy   | `./Proxy`                          | 80            | 80              |

---

## LLM Model Change

| Before                   | After                          |
| ------------------------ | ------------------------------ |
| `llama3.2` (3B, EN only) | `aya` (8B, multilingual EN/ES) |

- **Primary**: `aya` — Cohere's 8B multilingual model, tuned for EN↔ES
- **Fallback**: `llama3.2` — kept available for lightweight tasks
- **Embeddings**: `nomic-embed-text` — used by ChromaDB for passage retrieval

All three are pulled automatically by `ollama-init.sh` on first container start.

---

## New Files Created

### `/API/app/data/vocabulary.json`

Static bilingual glossary (50+ terms) + per-language style rules.
Always injected into every enriched prompt regardless of ChromaDB results.

```json
{
  "style_rules": {
    "en": ["Write in a clear, active voice.", ...],
    "es": ["Usa voz activa y oraciones concisas.", ...]
  },
  "vocabulary": {
    "en": {
      "aircraft": "aircraft",
      "runway": "runway",
     },
    "es": {
      "aircraft": "aeronave",
      "runway": "pista",
    },
  }
}
```

### `/API/app/data/aviation_vocabulary.json`

Static bilingual acronym glossary + per-language style rules.
Always injected into every enriched prompt regardless of ChromaDB results.

```json
[
  {
    "term": "A/A",
    "english": "Air/air",
    "spanish": "Aire a aire"
  },...
]
```

### `/API/app/utils/rag_service.py`

ChromaDB client singleton with graceful fallback.

Key functions:

- `embed(text)` — calls Ollama `/api/embeddings` with `nomic-embed-text`
- `query(text, language, n_results)` — returns top-N passages from `rag_en` or `rag_es`
- `format_context(passages, vocabulary, language)` — builds a "Style Reference" block string
- `check_health()` — returns `True` if ChromaDB is reachable
- `collection_count(lang)` — returns number of documents in the collection

If ChromaDB is unreachable on startup, all methods return empty/safe values — the pipeline degrades gracefully to non-RAG mode.

### `/API/app/utils/rag_ingestion.py`

Fetches published articles from the Django CMS, chunks them, and upserts into ChromaDB.

Key functions:

- `fetch_articles(language)` — `GET CMS_RAG_URL?lang=<lang>` with `X-RAG-Token` header
- `chunk_text(text, chunk_size=400, overlap=50)` — sliding window chunker
- `ingest_all()` — ingests both EN and ES, returns `{total_ingested, total_errors}`
- `is_populated(language)` — returns `True` if collection already has documents

### `/API/app/utils/load_vocabulary.py`

Loads `vocabulary.json` once at import time (cached in module-level `_cache` dict).

### `/API/app/routers/rag_router.py`

Admin RAG management endpoints:

| Method | Path              | Auth         | Description                      |
| ------ | ----------------- | ------------ | -------------------------------- |
| GET    | `/api/rag/status` | None         | Health check + collection counts |
| POST   | `/api/rag/ingest` | Google OAuth | Trigger re-ingestion from CMS    |

---

## Modified Files

### `ollama-init.sh`

Added pulls for `aya` and `nomic-embed-text` in addition to `llama3.2`.

### `docker-compose.yml` + `docker-compose.dev.yml`

- Added `chroma` service (ChromaDB)
- Added `cms-db` service (Postgres for the CMS)
- Added `cms` service (Django CMS, port 8002)
- `fastapi` now depends on `ollama`, `chroma`, and `cms`
- `fastapi` environment overrides `CMS_RAG_URL=http://cms:8000/articles/rag-corpus/`
- Added volumes: `chroma_data`, `cms_postgres_data`, `cms_django_media`, `cms_django_static`

### `/API/app/requirements.txt`

Added `chromadb>=0.5.0`.

### `/API/app/config.py`

Added new settings:

| Variable        | Default            | Description                          |
| --------------- | ------------------ | ------------------------------------ |
| `CHROMA_HOST`   | `chroma`           | ChromaDB service hostname            |
| `CHROMA_PORT`   | `8000`             | ChromaDB internal port               |
| `EMBED_MODEL`   | `nomic-embed-text` | Ollama embedding model name          |
| `RAG_N_RESULTS` | `3`                | Number of passages to retrieve       |
| `CMS_RAG_URL`   | (required)         | Django endpoint for RAG corpus       |
| `CMS_RAG_TOKEN` | (required)         | Shared secret for CMS authentication |

### `/API/app/utils/create_prompt_translation.py`

Added `context_block: str = ""` parameter. When non-empty, it is prepended as a style prefix before the translation instructions.

### `/API/app/utils/ollama_services.py`

`resume_article()` gains `context_block: str = ""` parameter. Injected as style prefix in both EN and ES summary prompts.

### `/API/app/services/translation.py`

Before building the Ollama prompt:

1. Queries ChromaDB for style passages relevant to the article
2. Loads vocabulary
3. Formats a `context_block` string
4. Passes it to `create_prompt_translation()`

### `/API/app/services/resume.py`

Same RAG pipeline as translation. Default model updated from `llama3.2` to `aya`.

### `/API/app/main.py`

- On startup: checks ChromaDB health → if either collection is empty → calls `ingest_all()`
- Registered `rag_router` at `/api` prefix

### `Content-Manager-Editor-Backend/src/articles/views.py`

Added `RagCorpusView(APIView)`:

- `GET /articles/rag-corpus/?lang=en|es`
- Validates `X-RAG-Token` header via constant-time `hmac.compare_digest`
- Extracts plain text from JSONField block body
- Returns `[{id, title, plain_text, language}]`

### `Content-Manager-Editor-Backend/src/articles/urls.py`

Added `path("rag-corpus/", RagCorpusView.as_view(), name="rag-corpus")`.

### `Content-Manager-Editor-Backend/src/config/settings.py`

Added `RAG_INTERNAL_TOKEN = os.getenv("RAG_INTERNAL_TOKEN", "")`.

---

## Environment Variables

### `/API/app/.env`

```env
# --- Existing ---
OLLAMA_HOST=http://ollama:11434
# ...

# --- New (RAG) ---
CHROMA_HOST=chroma
CHROMA_PORT=8000
EMBED_MODEL=nomic-embed-text
RAG_N_RESULTS=3
CMS_RAG_URL=http://cms:8000/articles/rag-corpus/
CMS_RAG_TOKEN=<shared-secret-must-match-RAG_INTERNAL_TOKEN>
```

### `Content-Manager-Editor-Backend/.env`

```env
# --- Existing ---
DJANGO_SECRET_KEY=<your-secret>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (overridden by docker-compose to point at cms-db service)
DB_NAME=blog_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# --- New (RAG) ---
RAG_INTERNAL_TOKEN=<shared-secret-must-match-CMS_RAG_TOKEN>
```

> **Security note:** `CMS_RAG_TOKEN` (FastAPI) and `RAG_INTERNAL_TOKEN` (Django) **must be the same value**. Use a strong random string (e.g. `openssl rand -hex 32`).

---

## Testing Guide

### Prerequisites

All services running via Docker Compose:

```bash
docker compose up --build
# or for dev:
docker compose -f docker-compose.dev.yml up --build
```

---

### Step 1 — Run Django Migrations

The CMS database starts empty. Run migrations inside the `cms` container:

```bash
docker compose exec cms python src/manage.py migrate
```

---

### Step 2 — Create a Django Superuser

```bash
docker compose exec cms python src/manage.py createsuperuser
```

Follow the prompts. Then open `http://127.0.0.1:8002/admin/` to access the Django admin.

---

### Step 3 — Add the Test Article to the Database

> **Current state:** There is 1 article in the codebase but it is **not yet in the database**. It must be inserted manually.

**Option A — via Django Admin UI** (`http://127.0.0.1:8002/admin/`):

1. Log in with the superuser credentials
2. Navigate to **Articles → Add Article**
3. Fill in Title, Body (JSON block array), set status to `published`
4. Save

**Option B — via Django shell**:

```bash
docker compose exec cms python src/manage.py shell
```

```python
from articles.models import ArticleModel

ArticleModel.objects.create(
    title="My First Article",
    body=[
        {"type": "paragraph", "content": [{"type": "text", "text": "This is the article body text used as style reference."}]}
    ],
    status="published"
)
```

**Option C — via DRF API** (if authentication is not required for writes):

```bash
curl -X POST http://127.0.0.1:8002/articles/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Article", "body": [{"type": "paragraph", "content": [{"type": "text", "text": "Sample content."}]}], "status": "published"}'
```

---

### Step 4 — Verify the RAG Corpus Endpoint

Confirm the Django endpoint returns the article (replace `<token>` with your `RAG_INTERNAL_TOKEN`):

```bash
curl -H "X-RAG-Token: <token>" \
     "http://127.0.0.1:8002/articles/rag-corpus/?lang=en"
```

Expected response:

```json
[
  {
    "id": "...",
    "title": "My First Article",
    "plain_text": "This is...",
    "language": "en"
  }
]
```

---

### Step 5 — Trigger ChromaDB Ingestion

**Automatic:** FastAPI triggers `ingest_all()` on startup if either ChromaDB collection is empty.

**Manual (re-ingest after adding articles):** Call the RAG ingest endpoint (requires Google OAuth token):

```bash
curl -X POST https://localhost/api/rag/ingest \
  -H "Authorization: Bearer <google-id-token>"
```

---

### Step 6 — Check RAG Status

```bash
curl https://localhost/api/rag/status
```

Expected response when working:

```json
{
  "chroma_available": true,
  "collections": {
    "rag_en": { "count": 5 },
    "rag_es": { "count": 0 }
  }
}
```

`count` reflects the number of text chunks ingested (not articles). 1 article typically produces 2–5 chunks depending on length.

---

### Step 7 — Test Translation

```bash
curl -X POST https://localhost/api/translate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <google-id-token>" \
  -d '{
    "title": "My First Article",
    "body": "<p>This is some content to translate.</p>",
    "target_language": "Spanish"
  }'
```

Check FastAPI logs to confirm the RAG context block was injected:

```bash
docker compose logs fastapi | grep "RAG context"
```

---

### Step 8 — Test Summarization

```bash
curl -X POST https://localhost/api/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <google-id-token>" \
  -d '{
    "title": "My First Article",
    "body": "<p>Long article content here...</p>"
  }'
```

---

### Troubleshooting

| Symptom                        | Likely Cause                           | Fix                                                                     |
| ------------------------------ | -------------------------------------- | ----------------------------------------------------------------------- |
| `chroma_available: false`      | ChromaDB not started or unreachable    | Check `docker compose ps chroma`; verify `CHROMA_HOST=chroma` in `.env` |
| `count: 0` in rag/status       | No articles in CMS or ingestion failed | Complete Steps 1–5 above                                                |
| CMS endpoint returns 403       | Token mismatch                         | Ensure `CMS_RAG_TOKEN` == `RAG_INTERNAL_TOKEN` in both `.env` files     |
| `aya` model slow / timeout     | Model not pulled yet                   | Run `docker compose exec ollama ollama pull aya`                        |
| Translation result lacks style | RAG not enriching (fallback mode)      | Check logs; ensure ChromaDB has chunks and CMS endpoint works           |

---

## Change Log

| Date       | Changed By | Summary                                                       |
| ---------- | ---------- | ------------------------------------------------------------- |
| 2026-03-16 | Copilot    | Added ChromaDB service to docker-compose                      |
| 2026-06-XX | Copilot    | Full RAG implementation: ChromaDB, rag_service, rag_ingestion |
| 2026-06-XX | Copilot    | Switched primary LLM from llama3.2 to aya (multilingual 8B)   |
| 2026-06-XX | Copilot    | Added nomic-embed-text for passage embeddings                 |
| 2026-06-XX | Copilot    | Added vocabulary.json (bilingual glossary + style rules)      |
| 2026-06-XX | Copilot    | Integrated Django CMS RagCorpusView + added cms to compose    |
