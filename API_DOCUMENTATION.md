# Ollama Translation API

A clean, simple translation API that connects NextJS applications to Ollama through Google OAuth authentication.

## 🏗️ Architecture Overview

The API follows a clean architecture pattern with organized modules:

```
app/
├── main.py              # FastAPI application entry point
├── schemas/             # Pydantic models for request/response validation
│   ├── translation.py   # Translation-specific schemas
│   └── user.py         # Google user authentication models
├── services/            # Business logic layer
│   ├── ollama.py        # Ollama communication service
│   └── translation.py   # Translation orchestration service
└── utils/               # Utility functions
    ├── auth.py          # Google OAuth authentication utilities
    └── text_processing.py # Text sanitization utilities
```

## 🔧 Code Structure Explanation

### 1. Main Application (`app/main.py`)

**Purpose**: FastAPI application setup and route definitions

- **Lifespan Management**: Checks Ollama connectivity on startup
- **Route Definitions**: Simple, focused endpoints
- **Error Handling**: Consistent HTTP error responses
- **Security**: Google OAuth token validation

```python
# Key features:
- Google ID token validation on /translate endpoint
- Health check for monitoring
- Clean error handling
- Automatic API documentation
- HTTPS support via nginx proxy
```

### 2. Schemas (`app/schemas/`)

**Purpose**: Data validation and API documentation

- **TranslationRequest**: Validates incoming translation requests
- **TranslationResponse**: Structures API responses
- **HealthResponse**: Health check response format
- **GoogleUser**: Google user information from ID token

```python
# Example Google user model:
class GoogleUser(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    verified: bool
```

### 3. Authentication (`app/utils/auth.py`)

**Purpose**: Google OAuth token validation and user management

- **Google ID Token Verification**: Validates tokens from NextJS Google Sign-In
- **User Permission Checks**: Ensures verified email addresses
- **Security Middleware**: Protects translation endpoints

```python
# Key features:
- Google ID token signature verification
- Token issuer validation
- Email verification requirement
- Structured user information extraction
```

class TranslationRequest(BaseModel):
title: str = Field(..., description="Title text to translate")
body: str = Field(..., description="Body text to translate")
section: str = Field(..., description="Section text to translate")

````

### 3. Authentication (`app/utils/auth.py`)

**Purpose**: JWT token creation and validation

- **Token Creation**: Generates JWT tokens for valid users
- **Token Validation**: Middleware for protecting endpoints
- **User Authentication**: Simple demo user validation

```python
# Security features:
- JWT token expiration (30 minutes)
- Bearer token authentication
- Automatic token validation
- Demo user credentials (replace in production)
````

### 4. Ollama Service (`app/services/ollama.py`)

**Purpose**: Communication with Ollama container

- **Health Checking**: Verifies Ollama accessibility
- **Translation Requests**: Sends prompts to Ollama
- **Error Handling**: Manages Ollama communication errors
- **Configuration**: Placeholder URL for Docker container

```python
# Ollama integration:
OLLAMA_BASE_URL = "https://docker/ollama/url"  # Replace with actual URL
- Async HTTP client for non-blocking requests
- Configurable model selection
- Timeout handling
```

### 5. Translation Service (`app/services/translation.py`)

**Purpose**: Business logic orchestration

- **Request Processing**: Coordinates the translation workflow
- **Text Sanitization**: Cleans responses before sending
- **Error Management**: Handles service-level errors

```python
# Translation workflow:
1. Create structured prompt
2. Send to Ollama service
3. Sanitize response
4. Return formatted result
```

### 6. Text Processing (`app/utils/text_processing.py`)

**Purpose**: Text sanitization and prompt creation

- **Sanitization**: Removes potentially harmful content
- **Prompt Formatting**: Creates consistent translation prompts
- **Content Cleaning**: Handles whitespace and HTML removal

```python
# Security measures:
- HTML tag removal
- Script injection prevention
- Whitespace normalization
- Content validation
```

## 📡 API Endpoints

### GET `/health`

**Purpose**: Check API and Ollama service status

```bash
curl http://127.0.0.1:8000/health
```

**Response**:

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

### POST `/translate`

**Purpose**: Translate text using Ollama
**Authentication**: Required (JWT Bearer token)

```bash
curl -X POST http://127.0.0.1:8000/translate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello World",
    "body": "This is a test message",
    "section": "Welcome section",
    "target_language": "Spanish",
    "model": "llama3.2"
  }'
```

**Response**:

```json
{
  "translated_text": "Hola Mundo\nEste es un mensaje de prueba\nSección de bienvenida",
  "success": true,
  "model_used": "llama3.2"
}
```

## 🔐 Security Features

1. **JWT Authentication**: Protects translation endpoint
2. **Localhost Only**: API only accessible from 127.0.0.1
3. **Text Sanitization**: Prevents injection attacks
4. **Input Validation**: Pydantic schema validation
5. **Error Isolation**: Doesn't expose internal details

## 🚀 Setup and Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# .env file
OLLAMA_BASE_URL=http://your-ollama-container:11434
JWT_SECRET_KEY=your-secret-key-change-in-production
API_HOST=127.0.0.1
API_PORT=8000
```

### 3. Start the API

```bash
python -m app.main
```

### 4. Generate JWT Token (for testing)

```python
from app.utils.auth import create_access_token
token = create_access_token("translator")
print(f"Token: {token}")
```

## 🌐 NextJS Integration Example

```javascript
// NextJS API call example
const translateText = async (textData) => {
  const response = await fetch("http://127.0.0.1:8000/translate", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${your_jwt_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: textData.title,
      body: textData.body,
      section: textData.section,
      target_language: "Spanish",
      model: "llama3.2",
    }),
  });

  const result = await response.json();
  return result.translated_text;
};
```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_BASE_URL`: URL to Ollama container (default: "https://docker/ollama/url")
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `API_HOST`: Host to bind API (default: "127.0.0.1")
- `API_PORT`: Port for API (default: "8000")

### Demo Credentials

- Username: `translator`
- Password: `translate123`

**⚠️ Important**: Replace demo credentials with proper authentication in production!

## 📋 Request/Response Examples

### Example Request Body

```json
{
  "title": "Product Launch",
  "body": "We are excited to announce our new product features",
  "section": "Marketing announcement",
  "target_language": "French",
  "model": "llama3.2"
}
```

### Example Response

```json
{
  "translated_text": "Lancement de produit\nNous sommes ravis d'annoncer nos nouvelles fonctionnalités de produit\nAnnonce marketing",
  "success": true,
  "model_used": "llama3.2"
}
```

## 🚨 Error Handling

### Authentication Errors

```json
{
  "detail": "Invalid token",
  "status_code": 401
}
```

### Translation Errors

```json
{
  "detail": "Translation failed: Ollama service unavailable",
  "status_code": 500
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

This API is designed to be simple, secure, and focused specifically on translation tasks for NextJS applications.
