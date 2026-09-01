# API Translation Standalone Test

This guide runs only `AI-Translation-API` and its real Ollama dependency. It does not start the Editor, Backend-Editor, proxy, Redis, Qdrant, or the root compose stack. The HTTP checks call the running containers and do not mock FastAPI or Ollama.

## Prerequisites

- Docker Desktop or Docker Engine with Compose support
- Node.js 18+ and `npx` for the Jest check
- Postman for the manual check

The API image listens on port `443` internally, but Uvicorn serves plain HTTP. The standalone Make target publishes it at `http://localhost:8444`.

## Start the standalone containers

Run this command from the repository root, not from `API/`:

```bash
make api-standalone-up
```

The target creates the temporary network, starts Ollama, pulls the `aya` model, builds the API image, starts the API container, and waits for `/health`. It can be run again; the shared `ai-translation-ollama-data` volume preserves downloaded models.

The first translation may be slow while Ollama loads `aya`. Check startup logs with:

```bash
docker logs ai-translation-api-standalone
docker logs ai-translation-ollama
```

If the model pull fails, retry it without rebuilding the API image:

```bash
docker exec ai-translation-ollama ollama pull aya
```

## Health check

```bash
curl http://localhost:8444/health
```

Expected response:

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

## Postman or curl translation check

Create a `POST` request to `http://localhost:8444/api/translate` with:

```text
Authorization: Bearer standalone-test-token
Content-Type: application/json
```

Use this JSON body:

```json
{
  "title": "Airport slots",
  "body": "Airport slots help coordinate demand and capacity.",
  "section": "Technology",
  "target_language": "Spanish",
  "model": "aya"
}
```

Expected result: HTTP `200` with `success: true`, a non-empty `model_used`, and `translated_text` containing `title`, `body`, and `section`.

`DEV_MODE=true` is enabled by the standalone setup, so the bearer value is only a development token and is not production authentication.

Equivalent curl request:

```bash
curl -X POST http://localhost:8444/api/translate \
  -H 'Authorization: Bearer standalone-test-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Airport slots",
    "body": "Airport slots help coordinate demand and capacity.",
    "section": "Technology",
    "target_language": "Spanish",
    "model": "aya"
  }'
```

## Jest integration check

The root test uses Node's real `fetch` for health and translation requests:

```bash
npx --yes jest --runInBand ai-translation-api.standalone.test.js
```

Or:

```bash
make api-standalone-test
```

For a different published port:

```bash
API_BASE_URL=http://localhost:8450 npx --yes jest --runInBand ai-translation-api.standalone.test.js
```

## Logs and cleanup

Follow logs while testing:

```bash
docker logs -f --tail 80 ai-translation-api-standalone
docker logs -f --tail 80 ai-translation-ollama
```

Stop the containers while keeping the image and model volume:

```bash
make api-standalone-down
```

Remove the containers, image, and temporary network while preserving the model volume:

```bash
make api-standalone-clean
```

To remove the shared Ollama model cache as well:

```bash
make api-standalone-purge-ollama
```

## Troubleshooting

- `401` or `403`: confirm the API is running with `DEV_MODE=true` and that the request has a bearer header.
- Ollama is disconnected: confirm `ai-translation-ollama` is running and `OLLAMA_BASE_URL` uses the container name, not `localhost`.
- Translation times out: wait for `aya` to finish downloading/loading, then retry and inspect both container logs.
- Port conflict: change only the host side of the Docker mapping, then use the same address in `API_BASE_URL`.
- `TLS handshake timeout` during `ollama pull`: retry the pull and check Docker Desktop's network, VPN, or proxy settings.
