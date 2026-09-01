# AGENTS.md — Python AI API

## Overview

FastAPI Python application that provides AI-powered translation and article
summarisation for the Blog Editor CMS. It validates Google OAuth Access Tokens,
sanitises HTML input, and proxies requests to a locally-running Ollama LLM
container to perform HTML-structure-preserving translation and content
summarisation.

---

## Tech Stack

| Concern              | Library / Tool                            |
| -------------------- | ----------------------------------------- |
| Framework            | FastAPI 0.115                             |
| Language             | Python 3.11+                              |
| ASGI server          | uvicorn (with standard extras)            |
| Schema validation    | Pydantic v2                               |
| Async HTTP client    | httpx                                     |
| HTML parsing         | beautifulsoup4                            |
| Auth                 | Google OAuth Access Tokens (via httpx)    |
| Environment config   | python-dotenv                             |
| LLM backend          | Ollama (llama3.2 default model)           |
| Package manager      | pip / requirements.txt                    |
| Container runtime    | Docker + docker-compose                   |

---

## Directory Layout

```
app/
├── main.py                  # FastAPI app factory, lifespan, CORS, router registration
├── config.py                # Env variable loading (ALLOWED_ORIGINS, OLLAMA_BASE_URL …)
├── requirements.txt         # Python dependencies
├── models/
│   └── models.py            # Internal Pydantic models (GenerateRequest/Response …)
├── routers/
│   ├── translate_router.py  # POST /api/translate
│   └── resume_router.py     # POST /api/resume
├── schemas/
│   ├── translation.py       # TranslationRequest/Response, ResumeRequest/Response, HealthResponse
│   └── testUser.py          # GoogleUser schema returned by auth dependency
├── services/
│   ├── translation.py       # TranslationService — HTML/text translation via Ollama
│   └── resume.py            # ResumeService — article summarisation via Ollama
└── utils/
    ├── auth.py                      # verify_google_access_token FastAPI dependency
    ├── ollama_services.py           # OllamaService — all Ollama HTTP communication
    ├── sanitize_html.py             # Strip dangerous tags/attributes (regex-based)
    ├── sanitize_text.py             # Strip unwanted characters from plain text output
    └── create_prompt_translation.py # Prompt builder for translation requests
```

---

## API Endpoints

| Method | Path             | Auth required | Description                                       |
| ------ | ---------------- | ------------- | ------------------------------------------------- |
| GET    | `/health`        | No            | Returns API + Ollama health status                |
| POST   | `/api/translate` | Yes (Google)  | Translate title/body/section HTML to target lang  |
| POST   | `/api/resume`    | Yes (Google)  | Summarise article title + body via Ollama         |

### Request / Response Examples

**POST `/api/translate`**
```json
{
  "title": "My Article",
  "body": "<p>Hello <strong>world</strong></p>",
  "section": "Technology",
  "target_language": "Spanish",
  "model": "llama3.2"
}
```
Response:
```json
{
  "translated_text": {
    "title": "Mi Artículo",
    "body": "<p>Hola <strong>mundo</strong></p>",
    "section": "Tecnología"
  },
  "success": true,
  "model_used": "llama3.2"
}
```

**POST `/api/resume`**
```json
{ "title": "My Article", "body": "<p>...</p>", "language": "en" }
```
Response:
```json
{ "resume": "A concise one-paragraph summary.", "success": true }
```

---

## Auth Flow

1. The Next.js editor retrieves a Google OAuth Access Token from the active `next-auth` session.
2. It passes it as `Authorization: Bearer <token>` on every request to this API.
3. `utils/auth.py` — `verify_google_access_token` dependency validates the token by calling
   `GET https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=<token>`.
4. It checks that `email_verified` is `true` and returns a `GoogleUser` injected into the route handler.
5. `DEV_MODE=true` bypasses token validation (returns a static dev user — **never use in production**).
6. `TESTING_MODE=true` accepts fake signed JWTs in place of real Google tokens (tests only).

---

## Configuration (Environment Variables)

| Variable               | Required | Description                                                  |
| ---------------------- | -------- | ------------------------------------------------------------ |
| `ALLOWED_ORIGINS`      | Yes      | CORS origins string (e.g. `http://localhost:8000`)           |
| `CORS_METHODS`         | No       | JSON array of allowed HTTP methods                           |
| `CORS_ALLOW_HEADERS`   | No       | JSON array of allowed headers                                |
| `GOOGLE_CLIENT_ID`     | Yes      | Google OAuth client ID for token introspection               |
| `OLLAMA_BASE_URL`      | Yes      | Ollama server URL (e.g. `http://ollama:11434`)               |
| `OLLAMA_DEFAULT_MODEL` | No       | Default LLM model name (default: `llama3.2`)                 |
| `DEV_MODE`             | No       | `true` bypasses Google token validation — never use in prod  |
| `TESTING_MODE`         | No       | `true` accepts fake JWTs — tests only                        |

All variables are loaded via `python-dotenv` in `config.py`. Never commit `.env` files.

---

## Adding a New Endpoint

1. Define request and response `BaseModel` schemas with `Field(...)` in `schemas/translation.py`.
2. Add service logic in `services/` (new file or existing class).
3. Create (or extend) a router in `routers/`:

```python
from fastapi import APIRouter, Depends
from schemas.translation import MyRequest, MyResponse
from services.my_service import my_service
from utils.auth import verify_user_access
from schemas.testUser import GoogleUser

router = APIRouter()

@router.post("/my-route", response_model=MyResponse)
async def my_handler(
    request: MyRequest,
    current_user: GoogleUser = Depends(verify_user_access),
) -> MyResponse:
    return await my_service.process(request)
```

4. Register in `main.py`: `app.include_router(my_router.router, prefix="/api")`
5. Add tests under `tests/` (see `.github/skills/test.md`).

---

## Development

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run locally (from app/ directory)
uvicorn main:app --reload --port 8001
```

Or via Docker (from the project root):

```bash
docker compose -f docker-compose.dev.yml up --build
```

The API runs on port **8001** inside Docker (proxied via Nginx on 443).

---

## Testing

Use `pytest` + `pytest-asyncio` + `httpx.AsyncClient` for full async coverage.
External services (Ollama, Google OAuth) must always be mocked.

```bash
pip install pytest pytest-asyncio httpx pytest-mock

pytest -v --cov=app --cov-report=term-missing
```

See `.github/skills/test.md` for the full testing skill and fixture conventions.

---

## Security Notes

- All HTML input is sanitised by `utils/sanitize_html.py` before being forwarded to Ollama.
- Google Access Tokens are validated server-side — never trusted client-side.
- `ALLOWED_ORIGINS` must be set or the app refuses to start.
- All secrets must come from environment variables. Never hardcode or commit them.
- Pydantic v2 validates and coerces all request data at the API boundary.
- Never log full token values; truncate to the first 50 characters.

---

## Code Editing Rules

- Follow `.github/skills/codeEdit.md` and `.github/skills/test.md`.
- Use Python type hints on all function signatures and return types.
- Prefer `async def` for all route handlers and service methods.
- Use `logging` (not `print`) for production logging.
- PEP 8: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
