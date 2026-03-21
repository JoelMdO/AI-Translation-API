# AI Translation API

Production-ready using AI to perform translation through Ollama and Google Authentication.

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

## API Usage

### Authentication

Requires Google ID token from NextJS Google Sign-In.

### Endpoints

#### POST /ask/ask

Translates text using Ollama.

#### POST /api/resume

Summarize an article to create a description not longer than 50 words.

#### GET /health

Public health check endpoint.

## Environment Variables

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `OLLAMA_BASE_URL`: Ollama service URL
- `ALLOWED_ORIGINS`: CORS allowed origins

## Deployment

Uses Docker with nginx for HTTPS termination and FastAPI for the API service.
