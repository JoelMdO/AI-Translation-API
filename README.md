# Ollama Translation API

Production-ready translation API using Ollama and Google Authentication.

## Quick Start

1. **Environment Setup**:

   ```bash
   cp .env.production .env
   # Edit .env with your Google Client ID
   ```

2. **Docker Deployment**:

   ```bash
   docker-compose up -d
   ```

3. **Access API**:
   - HTTPS: `https://joelmdo-lab.dev`
   - Health: `https://joelmdo-lab.dev/health`
   - Translate: `POST https://joelmdo-lab.dev/ask/ask`

## API Usage

### Authentication

Requires Google ID token from NextJS Google Sign-In.

### Endpoints

#### POST /ask/ask

Translates text using Ollama.

**Headers:**

```
Authorization: Bearer <google_id_token>
Content-Type: application/json
X-Request-Type: translation
X-Service: cms-translate
X-Source-DB: db
```

**Request:**

```json
{
  "title": "Article Title",
  "body": "Text to translate",
  "section": "content",
  "target_language": "spanish"
}
```

**Response:**

```json
{
  "translated_text": "Translated content",
  "success": true,
  "model_used": "llama3.2"
}
```

#### GET /health

Public health check endpoint.

## Environment Variables

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `OLLAMA_BASE_URL`: Ollama service URL
- `ALLOWED_ORIGINS`: CORS allowed origins

## Deployment

Uses Docker with nginx for HTTPS termination and FastAPI for the API service.
