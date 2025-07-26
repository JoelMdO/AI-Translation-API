# Ollama Translation API

A simple and secure translation API powered by Ollama with JWT authentication. This API is designed to translate text content with title, body, and section fields.

## Features

- 🔐 JWT Authentication for secure access
- 🌍 Text translation powered by Ollama models
- 🔒 Local-only access (127.0.0.1) for security
- 📝 Structured translation with title, body, and section
- 🚀 FastAPI-based with automatic documentation
- 🐳 Docker support for easy deployment

## Prerequisites

1. **Install Ollama**: Download and install from [https://ollama.ai/](https://ollama.ai/)
2. **Start Ollama**: Run `ollama serve` in your terminal
3. **Pull a model**: Run `ollama pull llama3.2` (or your preferred model)

## Quick Start

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   Edit `.env` file to customize settings:

   ```
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_DEFAULT_MODEL=llama3.2
   API_HOST=127.0.0.1
   API_PORT=8000
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
   ```

3. **Start the API server**:

   ```bash
   python start.py
   ```

4. **Access the API**:
   - API: http://127.0.0.1:8000
   - Documentation: http://127.0.0.1:8000/docs
   - Health check: http://127.0.0.1:8000/health

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

- **Username**: `translator`
- **Password**: `translate123`

## API Endpoints

### Authentication

- `POST /token` - Get JWT authentication token

### Translation

- `POST /translate` - Translate text content (requires JWT token)

### Utility

- `GET /` - API information
- `GET /health` - Health check

## Usage Examples

### 1. Get Authentication Token

```bash
curl -X POST "http://127.0.0.1:8000/token?username=translator&password=translate123"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Translate Text

```bash
curl -X POST "http://127.0.0.1:8000/translate" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Welcome to our platform",
    "body": "This is a comprehensive guide on how to use our new features. Please follow the instructions carefully.",
    "section": "Getting Started",
    "target_language": "Spanish"
  }'
```

Response:

```json
{
  "translated_text": "Bienvenido a nuestra plataforma\n\nEsta es una guía completa sobre cómo usar nuestras nuevas funciones. Por favor, siga las instrucciones cuidadosamente.\n\nComenzando",
  "original_prompt": "Translate the following text to Spanish: Title{ Welcome to our platform } Body{ This is a comprehensive guide... } Section{ Getting Started }",
  "model_used": "llama3.2",
  "success": true
}
```

### 3. Python Client Example

```python
import asyncio
import httpx

class TranslationAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None

    async def get_token(self, username: str = "translator", password: str = "translate123"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/token",
                params={"username": username, "password": password}
            )
            data = response.json()
            self.token = data["access_token"]
            return self.token

    async def translate(self, title: str, body: str, section: str, target_language: str = "Spanish"):
        if not self.token:
            await self.get_token()

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/translate",
                headers=headers,
                json={
                    "title": title,
                    "body": body,
                    "section": section,
                    "target_language": target_language
                }
            )
            return response.json()

# Usage
async def main():
    client = TranslationAPIClient()
    result = await client.translate(
        title="Hello World",
        body="This is a test message",
        section="Introduction",
        target_language="French"
    )
    print(result["translated_text"])

asyncio.run(main())
```

## Request/Response Format

### Translation Request

```json
{
  "title": "string",
  "body": "string",
  "section": "string",
  "target_language": "Spanish", // optional, defaults to "Spanish"
  "model": "llama3.2" // optional, defaults to "llama3.2"
}
```

### Translation Response

```json
{
  "translated_text": "string",
  "original_prompt": "string",
  "model_used": "string",
  "success": true
}
```

## Testing

Run the test script to verify everything is working:

```bash
python test_api.py
```

Or use the example client:

```bash
python example_client.py
```

## Docker Deployment

### Using Docker Compose

```bash
docker-compose up
```

This will start both Ollama and the Translation API, accessible only on localhost.

### Using Docker

```bash
# Build the image
docker build -t ollama-translation-api .

# Run the container
docker run -p 127.0.0.1:8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ollama-translation-api
```

## Security Features

- **Local Access Only**: API binds to 127.0.0.1 (localhost) by default
- **JWT Authentication**: All translation requests require valid JWT tokens
- **Token Expiration**: Tokens expire after 30 minutes
- **No External Dependencies**: Self-contained with Ollama

## Configuration

Environment variables:

| Variable               | Default                  | Description                               |
| ---------------------- | ------------------------ | ----------------------------------------- |
| `OLLAMA_BASE_URL`      | `http://localhost:11434` | Ollama server URL                         |
| `OLLAMA_DEFAULT_MODEL` | `llama3.2`               | Default model for translations            |
| `API_HOST`             | `127.0.0.1`              | API server host (localhost only)          |
| `API_PORT`             | `8000`                   | API server port                           |
| `JWT_SECRET_KEY`       | `your-secret-key...`     | JWT signing secret (change in production) |

## Supported Languages

The API can translate to any language supported by your Ollama model. Popular options:

- Spanish
- French
- German
- Italian
- Portuguese
- Chinese
- Japanese
- And many more...

## Error Handling

The API includes comprehensive error handling for:

- Authentication failures
- Invalid JWT tokens
- Ollama connection issues
- Translation errors
- Invalid request formats

## Troubleshooting

1. **Ollama not accessible**: Make sure Ollama is running (`ollama serve`)
2. **Model not found**: Pull the required model (`ollama pull llama3.2`)
3. **Authentication failed**: Check username/password or token validity
4. **Connection refused**: Ensure API is running on 127.0.0.1:8000

## License

This project is open source and available under the MIT License.
