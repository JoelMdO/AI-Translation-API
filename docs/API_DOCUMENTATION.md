## 📁 Folder & Method Overview

### services/

- **summary.py**
  - `SummaryService.summarize(request)`: Orchestrates summary generation, RAG context, HTML handling.
- **translation.py**
  - `TranslationService.translate(request)`: Orchestrates translation, RAG context, HTML handling.

### utils/summary/

- **summary_article.py**
  - `SummaryUtils.resume_article(title, body, model, language, context_block)`: Generates summary with RAG context.
- **create_prompt_summary.py**
  - Builds summary prompts for LLM.

### utils/translation/

- **translate_html_content.py**
  - `TranslateHTMLContent.translate_html_content(content, target_language)`: HTML-aware translation.
- **generate_translation.py**
  - Sends translation prompts to Ollama.
- **create_prompt_translation.py**
  - Builds translation prompts for LLM.

### utils/rag_file_data_transform/

- **check_lines.py**: Extracts/cleans lines from PDF vocabulary.
- **merge_csv_to_vocab.py**: Merges CSV vocabulary into JSON.
- **pdf_to_json.py**: Converts PDF vocabulary to JSON.

# Ollama Translation API — with RAG Enrichment

A secure, context-enriched translation API for NextJS applications, featuring Retrieval-Augmented Generation (RAG) with ChromaDB, bilingual vocabulary, and style rules. Integrates Google OAuth authentication and supports advanced LLM models (aya, llama3.2).

## 🏗️ Architecture Overview

```
Editor (Next.js)
  │  POST /api/translate | /api/summary
  ▼
FastAPI (/API/app)
  ├── main.py                # App entrypoint, startup checks, router registration
  ├── routers/
  │     ├── translate_router.py  # /api/translate endpoint
  │     ├── summary_router.py    # /api/summary endpoint
  │     └── rag_router.py        # /api/rag/status, /api/rag/ingest endpoints
  ├── services/
  │     ├── translation.py       # Orchestrates translation, RAG, and Ollama (translation)
  │     └── summary.py           # Orchestrates summary, RAG, and Ollama (summary)
  ├── utils/
  │     ├── summary/             # Summary prompt/logic helpers
  │     ├── translation/         # Translation prompt/logic helpers
  │     ├── rag_service/         # ChromaDB client, context formatting
  │     ├── rag_ingestion.py     # CMS fetch, chunking, ingestion
  │     ├── rag_file_data_transform/ # PDF/CSV vocabulary extraction tools
  │     ├── load_vocabulary.py   # Loads vocabulary and style rules
  │     └── auth.py              # Google OAuth/JWT utilities
  ├── data/
  │     ├── vocabulary.json      # Bilingual glossary + style rules
  │     └── abbreviation.json    # Acronym glossary
  └── config.py                  # Environment/config management
```

**Key subfolders:**

- `services/`: Business logic for translation and summary endpoints
- `utils/summary/`: Summary prompt creation and Ollama helpers
- `utils/translation/`: Translation prompt creation and Ollama helpers
- `utils/rag_service/`: ChromaDB client and context formatting
- `utils/rag_file_data_transform/`: Scripts for extracting/merging vocabulary from PDFs/CSVs
- `utils/`: Other helpers (auth, ingestion, vocabulary loading)

## 🔧 Code Structure Explanation

### 1. Main Application (`app/main.py`)

**Purpose**: FastAPI setup, startup checks, and router registration

- **Startup Checks**: Verifies Ollama and ChromaDB connectivity
- **RAG Auto-Ingestion**: If ChromaDB is empty, fetches and ingests CMS articles
- **Route Registration**: `/api/translate`, `/api/summary`, `/api/rag/status`, `/api/rag/ingest`
- **CORS & Security**: Configured via environment variables

### 2. Schemas (`app/schemas/`)

**Purpose**: Pydantic models for request/response validation

- **TranslationRequest**: `{title, body, section, target_language, model}`
- **TranslationResponse**: `{translated_text: {title, body, section}, success, model_used}`
- **HealthResponse**: `{status, ollama_connected, api_version}`
- **GoogleUser**: Google user info from ID token

### 3. Authentication (`app/utils/auth.py`)

**Purpose**: Google OAuth (for admin endpoints) and JWT (for translation)

- **Google ID Token Verification**: For `/api/rag/ingest` (admin)
- **JWT Token**: For `/api/translate` endpoint
- **Security**: Token expiration, Bearer authentication, demo credentials (replace in prod)

### 4. Ollama Service & LLM Models

**Purpose**: Communicate with Ollama container for translation/summarization

- **Primary Model**: `aya` (8B, multilingual EN/ES)
- **Fallback Model**: `llama3.2` (lightweight, EN only)
- **Embeddings**: `nomic-embed-text` (for ChromaDB retrieval)
- **Async HTTP**: Non-blocking requests, timeout handling

### 5. Translation Service (`app/services/translation.py`)

**Purpose**: Orchestrates translation, RAG enrichment, and Ollama calls

- **RAG Pipeline**:
  1. Query ChromaDB for style passages (via `rag_service`)
  2. Load vocabulary and style rules (from `vocabulary.json`)
  3. Format a `context_block` (style reference)
  4. Inject context into translation prompt
  5. Call Ollama for translation
  6. Sanitize and structure response

### 6. RAG, Vocabulary, and Style Rules

**RAG (Retrieval-Augmented Generation)**:

- **ChromaDB**: Stores style passages from CMS articles (EN/ES)
- **Vocabulary**: Bilingual glossary always injected into context
- **Style Rules**: Per-language rules for tone, grammar, and terminology
- **Fallback**: If ChromaDB is unavailable, pipeline degrades gracefully (no context block)

## 📡 API Endpoints

### GET `/health`

**Purpose**: Check API and Ollama service status

```bash
curl http://127.0.0.1:8000/health
```

**Response:**

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

### POST `/api/summary`

**Purpose**: Summarize article content using RAG-enriched prompt
**Authentication**: Required (JWT Bearer token)

```bash
curl -X POST http://127.0.0.1:8000/api/summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Article",
    "body": "<p>Long article content here...</p>"
  }'
```

**Response:**

```json
{
  "article": "Resumen del artículo...",
  "success": true
}
```

    "title": "Hola Mundo",
    "body": "Este es un mensaje de prueba",
    "section": "Sección de bienvenida"

},
"success": true,
"model_used": "aya"
}

````

### GET `/api/rag/status`
**Purpose**: Check ChromaDB health and collection counts
**Authentication**: None

```bash
curl http://127.0.0.1:8000/api/rag/status
````

**Response:**

```json
{
  "chroma_available": true,
  "collections": {
    "en": { "count": 5 },
    "es": { "count": 3 }
  }
}
```

### POST `/api/rag/ingest`

**Purpose**: Trigger re-ingestion of CMS articles into ChromaDB
**Authentication**: Required (Google OAuth Bearer token)

```bash
curl -X POST http://127.0.0.1:8000/api/rag/ingest \
  -H "Authorization: Bearer GOOGLE_ID_TOKEN"
```

**Response:**

```json
{
  "success": true,
  "total_ingested": 10,
  "total_errors": 0
}
```

## 🔐 Security Features

1. **JWT Authentication**: Protects `/api/translate` endpoint
2. **Google OAuth**: Required for `/api/rag/ingest` (admin)
3. **Text Sanitization**: Prevents injection attacks
4. **Input Validation**: Pydantic schema validation
5. **Error Isolation**: No internal details exposed
6. **CORS**: Configurable allowed origins/methods/headers

## 🚀 Setup and Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with the following (see also RAG_IMPLEMENTATION.md):

```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=aya
OLLAMA_BACKUP_MODEL=llama3.2
JWT_SECRET_KEY=your-secret-key-change-in-production
API_HOST=127.0.0.1
API_PORT=8000
# RAG/ChromaDB
CHROMA_HOST=chroma
CHROMA_PORT=8000
EMBED_MODEL=nomic-embed-text
RAG_N_RESULTS=3
CMS_RAG_URL=http://cms:8000/articles/rag-corpus/
CMS_RAG_TOKEN=<shared-secret>
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
  const response = await fetch("http://127.0.0.1:8000/api/translate", {
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
      model: "aya",
    }),
  });
  const result = await response.json();
  return result.translated_text;
};
```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_BASE_URL`: URL to Ollama container
- `OLLAMA_DEFAULT_MODEL`: Primary LLM model (default: `aya`)
- `OLLAMA_BACKUP_MODEL`: Fallback LLM model (default: `llama3.2`)
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `API_HOST`, `API_PORT`: Host/port for API
- `CHROMA_HOST`, `CHROMA_PORT`: ChromaDB service
- `EMBED_MODEL`: Embedding model for ChromaDB (default: `nomic-embed-text`)
- `RAG_N_RESULTS`: Number of passages to retrieve from ChromaDB
- `CMS_RAG_URL`: Django CMS endpoint for RAG corpus
- `CMS_RAG_TOKEN`: Shared secret for CMS authentication

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
  "model": "aya"
}
```

### Example Response

```json
{
  "translated_text": {
    "title": "Lancement de produit",
    "body": "Nous sommes ravis d'annoncer nos nouvelles fonctionnalités de produit",
    "section": "Annonce marketing"
  },
  "success": true,
  "model_used": "aya"
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

---

This API is designed to be secure, context-aware, and focused on high-quality translation for NextJS applications, with RAG enrichment for consistent style and terminology.
