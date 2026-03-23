# API Integration Testing Guide

## Overview

This guide covers the integration test suite for the AI Translation & Summary API. Integration tests run against a **real, live API container** — they do not mock any dependencies. This validates the full stack: HTTP routing, authentication, service logic, and LLM integration.

---

## Unit Tests vs. Integration Tests

| Aspect             | Unit Tests        | Integration Tests                |
| ------------------ | ----------------- | -------------------------------- |
| Location           | `API/tests/*.py`  | `API/tests/integration/`         |
| Requires Docker    | No                | Yes                              |
| Mocks LLM calls    | Yes (monkeypatch) | No — real Ollama                 |
| Speed              | Fast (~seconds)   | Slow (~5–15 min in CI)           |
| pytest marker      | _(none)_          | `@pytest.mark.integration`       |
| What they validate | Function logic    | HTTP stack, response shape, auth |

> **Unit tests are never modified or removed.** Integration tests are additive.

---

## Directory Structure

```
API/tests/
├── conftest.py                          # Unit test fixtures (ASGI transport, DEV_MODE)
├── test_sanitize_html.py                # Unit test
├── test_sanitize_text.py                # Unit test
├── test_create_prompt_translation.py    # Unit test
├── test_translate_router.py             # Unit test
├── test_resume_router.py                # Unit test
├── test_translation_service.py          # Unit test
├── test_summary_service.py              # Unit test
├── test_full_flow.py                    # Unit test (in-process HTTP)
└── integration/
    ├── __init__.py
    └── test_api_integration.py          # ← Integration tests (real HTTP)
```

---

## Running Locally

### Step 1 — Start the API and dependencies

```bash
# From the repo root
chmod +x run-api-only.sh
./run-api-only.sh
```

This starts `fastapi`, `ollama`, and `chroma` containers (excluding Editor, Proxy, CMS).

### Step 2 — Run integration tests

```bash
pip install httpx pytest pytest-asyncio
pytest API/tests/integration/ -m integration -v
```

### Step 3 — Run unit tests (unchanged, no Docker needed)

```bash
pytest API/tests/ -m "not integration"
```

### Step 4 — Tear down containers

```bash
docker compose down
```

---

## CI/CD: GitHub Actions

The workflow is defined at [`.github/workflows/api-tests.yml`](../../.github/workflows/api-tests.yml).

### Trigger

Runs automatically on every **Pull Request targeting `main`**.

### Jobs

#### 1. `unit-tests` (fast, ~1–2 min)

- Installs Python dependencies
- Runs `pytest API/tests/ -m "not integration"`
- No Docker required
- Passes `DEV_MODE=true` and `ALLOWED_ORIGINS` as env vars inline

#### 2. `integration-tests` (slow, ~10–20 min) — runs after unit tests pass

- Builds and starts containers via `docker-compose.ci.yml`
- Polls `GET /health` every 10 seconds, up to 10 minutes
- Installs `httpx`, `pytest`, `pytest-asyncio`
- Runs `pytest API/tests/integration/ -m integration -v`
- On failure: dumps logs from `fastapi`, `ollama`, and `chroma` containers
- Always tears down containers (including volumes) at the end

### Architecture of `docker-compose.ci.yml`

| Service   | Purpose                                                  |
| --------- | -------------------------------------------------------- |
| `fastapi` | The API under test                                       |
| `ollama`  | LLM inference — uses `tinyllama` (lightweight, ~637MB)   |
| `chroma`  | ChromaDB for RAG — starts empty, API degrades gracefully |

**No Editor, Proxy, or CMS services are started in CI.**

---

## What Integration Tests Validate

Tests are in [API/tests/integration/test_api_integration.py](../tests/integration/test_api_integration.py).

| Test                                             | Endpoint              | What is checked                                    |
| ------------------------------------------------ | --------------------- | -------------------------------------------------- |
| `test_health_endpoint_returns_200`               | `GET /health`         | Status 200, required fields present                |
| `test_health_status_is_string`                   | `GET /health`         | `status` is a non-empty string                     |
| `test_rag_status_returns_200`                    | `GET /api/rag/status` | Status 200, `chroma_available` field               |
| `test_translate_403_without_auth`                | `POST /api/translate` | 403 without Authorization header                   |
| `test_translate_422_empty_payload`               | `POST /api/translate` | 422 with empty body                                |
| `test_translate_422_missing_target_language`     | `POST /api/translate` | 422 when `target_language` missing                 |
| `test_translate_422_missing_body`                | `POST /api/translate` | 422 when `body` missing                            |
| `test_translate_plain_text_returns_200`          | `POST /api/translate` | 200 with valid plain-text payload                  |
| `test_translate_plain_text_response_shape`       | `POST /api/translate` | `success`, `model_used`, `translated_text` present |
| `test_translate_plain_text_translated_text_keys` | `POST /api/translate` | `title`, `body`, `section` in `translated_text`    |
| `test_translate_html_body_returns_200`           | `POST /api/translate` | 200 with HTML body                                 |
| `test_translate_html_body_response_shape`        | `POST /api/translate` | Response shape correct for HTML body               |
| `test_summary_403_without_auth`                  | `POST /api/summary`   | 403 without Authorization header                   |
| `test_summary_422_empty_payload`                 | `POST /api/summary`   | 422 with empty body                                |
| `test_summary_422_missing_body`                  | `POST /api/summary`   | 422 when `body` missing                            |
| `test_summary_422_missing_title`                 | `POST /api/summary`   | 422 when `title` missing                           |
| `test_summary_returns_200`                       | `POST /api/summary`   | 200 with valid payload                             |
| `test_summary_response_shape`                    | `POST /api/summary`   | `success` and `article` fields present             |
| `test_summary_article_is_non_empty_on_success`   | `POST /api/summary`   | `article` is non-empty string when success         |
| `test_summary_html_body_returns_200`             | `POST /api/summary`   | 200 with HTML body                                 |
| `test_summary_spanish_language_returns_200`      | `POST /api/summary`   | 200 with `language=es`                             |

> **LLM output quality is NOT asserted.** Tests validate HTTP status codes and response schemas — not the content of translations or summaries. This makes tests stable across model changes and run environments.

---

## Authentication in CI

The API's `DEV_MODE=true` setting (set in `docker-compose.ci.yml`) bypasses Google OAuth validation. Any Bearer token is accepted:

```
Authorization: Bearer devtoken
```

No GitHub Secrets or Google credentials are needed for the integration tests to pass.

---

## GitHub Secrets (Not Required by Default)

With `DEV_MODE=true`, no secrets are needed. If you ever need to test with real Google auth (e.g., token validation), add these secrets to the GitHub repository under **Settings → Secrets and variables → Actions**:

| Secret Name        | Description                          |
| ------------------ | ------------------------------------ |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID               |
| `CMS_RAG_TOKEN`    | Shared secret for CMS authentication |

To use them, replace the hardcoded values in `docker-compose.ci.yml` with `${{ secrets.SECRET_NAME }}` in the workflow environment.

---

## Adding New Integration Tests

1. Open `API/tests/integration/test_api_integration.py`
2. Add a new test function prefixed with `test_`
3. Decorate with `@pytest.mark.integration`
4. Use the `client` fixture (module-scoped `httpx.Client`)
5. Only assert on HTTP status codes and response shape — not LLM content

Example:

```python
@pytest.mark.integration
def test_my_new_endpoint_returns_200(client):
    resp = client.get("/api/some-endpoint")
    assert resp.status_code == 200
    assert "expected_field" in resp.json()
```

---

## Troubleshooting

### API never becomes healthy in CI

- Check Ollama model pull completed: `docker compose -f docker-compose.ci.yml logs ollama`
- Check FastAPI startup errors: `docker compose -f docker-compose.ci.yml logs fastapi`
- Ollama model pull can take 5–15 minutes on a cold runner (no cache)

### Tests time out (LLM calls are slow)

- The `httpx.Client` has a 120-second timeout per test
- `tinyllama` is the fastest available model (~637MB, ~1-3s inference)
- If still timing out, increase the timeout in `test_api_integration.py` or pre-cache the Docker layer

### SSL/certificate errors locally

- The API uses a self-signed certificate on port 443
- Tests use `verify=False` to skip certificate verification — this is expected and safe for local/CI testing

### Running only specific integration tests

```bash
pytest API/tests/integration/ -m integration -k "translate" -v
pytest API/tests/integration/ -m integration -k "summary" -v
```

### Checking what tests are collected without running

```bash
pytest API/tests/integration/ -m integration --collect-only
```
