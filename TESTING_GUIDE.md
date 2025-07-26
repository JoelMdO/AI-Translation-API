# 🧪 API Testing Guide

## 📋 Answers to Your Questions

### 1. **Ollama API Endpoints** (`/api/tags` and `/api/generate`)

These are **Ollama's built-in REST API endpoints**, not files in your project:

- **`/api/tags`**: Lists all available models (llama3.2, codellama, etc.)
- **`/api/generate`**: Generates text using a specific model
- **`/api/chat`**: Chat completion endpoint
- **`/api/embeddings`**: Generate embeddings

When you run `ollama serve`, it automatically creates these HTTP endpoints on port 11434.

### 2. **How Ollama Understands `/api/generate`**

Ollama is a **standalone application** that runs its own HTTP server:

1. You install Ollama (`brew install ollama`)
2. You pull models (`ollama pull llama3.2`)
3. You start the server (`ollama serve`)
4. Ollama automatically exposes REST API endpoints

Your code sends this payload to Ollama:

```json
{
  "model": "llama3.2",
  "prompt": "Translate 'Hello' to Spanish",
  "stream": false,
  "temperature": 0.3
}
```

Ollama processes this and returns the generated text.

## 🚀 Testing with Postman

### **Step 1: Copy a Valid Test Token**

Use this token (generated from the script above):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXVkIjoieW91ci1nb29nbGUtY2xpZW50LWlkLWZyb20tY29uc29sZSIsInN1YiI6IjEyMzQ1Njc4OSIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiVGVzdCBVc2VyIiwiaWF0IjoxNzUzNTM4MTg3LCJleHAiOjE3NTM1NDE3ODd9.7xbIZb6OWw9iL9H-RfIHgC7MkQ_KKN5H2v3PaO9KIhs
```

### **Step 2: Create Postman Requests**

#### **Health Check (No Auth Required)**

```
GET https://localhost:443/health
```

#### **Translation Request (Requires Auth)**

```
POST https://localhost:443/translate

Headers:
- Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXVkIjoieW91ci1nb29nbGUtY2xpZW50LWlkLWZyb20tY29uc29sZSIsInN1YiI6IjEyMzQ1Njc4OSIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiVGVzdCBVc2VyIiwiaWF0IjoxNzUzNTM4MTg3LCJleHAiOjE3NTM1NDE3ODd9.7xbIZb6OWw9iL9H-RfIHgC7MkQ_KKN5H2v3PaO9KIhs
- Content-Type: application/json
- X-Request-Type: translation
- X-Service: cms-translate
- X-Source-DB: db

Body (JSON):
{
  "title": "Test Article",
  "body": "Hello world, please translate this text.",
  "section": "content",
  "target_language": "spanish"
}
```

### **Step 3: Testing Different Scenarios**

#### ✅ **Valid Token (Should Work)**

Use the token above - should return translation

#### ❌ **Unverified Email (Should Fail)**

Use this token (unverified email):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXVkIjoieW91ci1nb29nbGUtY2xpZW50LWlkLWZyb20tY29uc29sZSIsInN1YiI6IjEyMzQ1Njc4OSIsImVtYWlsIjoidW52ZXJpZmllZEBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTc1MzUzODE4NywiZXhwIjoxNzUzNTQxNzg3fQ.Mg9921uKNj6eYFPL3y2Bl7QHGmEMTG3fXEhUzNaC0Ys
```

Should return `403 Forbidden` with message about insufficient permissions

## 🔧 **How Fake Google Tokens Work**

Your API is now configured with `TESTING_MODE=true` in `.env`, which means:

1. **Real Google tokens**: Disabled in testing mode
2. **Fake tokens**: Generated with a test secret key
3. **Same validation**: Email verification, expiration, etc.
4. **Easy testing**: No need for real Google OAuth setup

## 🚦 **Expected Responses**

### ✅ **Successful Translation**

```json
{
  "original_title": "Test Article",
  "original_body": "Hello world, please translate this text.",
  "translated_title": "Artículo de Prueba",
  "translated_body": "Hola mundo, por favor traduce este texto.",
  "target_language": "spanish",
  "section": "content"
}
```

### ❌ **Authentication Error**

```json
{
  "detail": "Insufficient permissions for translation service"
}
```

### 📊 **Health Check**

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

## 🔄 **Switching Between Testing and Production**

In `.env` file:

- **Testing**: `TESTING_MODE=true` (uses fake tokens)
- **Production**: `TESTING_MODE=false` (uses real Google tokens)

## 🎯 **Quick Test Commands**

Generate new test tokens anytime:

```bash
cd /Users/joelmontesdeoca/Documents/Bafik/OllamaAPI
/Users/joelmontesdeoca/Documents/Bafik/OllamaAPI/venv/bin/python generate_test_tokens.py
```

Your API structure is now perfect for both development testing and production use!
