# 🧪 Complete Postman Testing Guide

## ✅ **Your API is Running!**

Your FastAPI server is now running on: **http://localhost:8001**

## 🎯 **Correct API Endpoints**

### **Health Check (Public - No Auth Required)**

```
GET http://localhost:8001/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "api_version": "1.0.0"
}
```

### **Translation (Requires Authentication)**

```
POST http://localhost:8001/ask/ask
```

## 🔑 **Authentication Flow**

Your API structure:

1. **Your NextJS CMS** → calls your API
2. **Your API** → calls Ollama internally
3. **Testing**: Use fake Google tokens (since `TESTING_MODE=true`)

## 🚀 **Postman Setup for Translation Testing**

### **Step 1: Create POST Request**

- **URL**: `http://localhost:8001/ask/ask`
- **Method**: POST

### **Step 2: Add Headers**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXVkIjoieW91ci1nb29nbGUtY2xpZW50LWlkLWZyb20tY29uc29sZSIsInN1YiI6IjEyMzQ1Njc4OSIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiVGVzdCBVc2VyIiwiaWF0IjoxNzUzNTQwNjYzLCJleHAiOjE3NTM1NDQyNjN9.XPVT9CrH7NDjTthy4To5_8b2gdMABozPm1BA5kLcxTk

Content-Type: application/json

X-Request-Type: translation

X-Service: cms-translate

X-Source-DB: db
```

### **Step 3: Add JSON Body**

```json
{
  "title": "Test Article",
  "body": "Hello world, please translate this text to Spanish.",
  "section": "content",
  "target_language": "spanish"
}
```

## 📋 **Testing Scenarios**

### ✅ **Test 1: Valid Authentication**

- **Token**: Use the "Valid User" token from above
- **Expected**: Translation response from Ollama
- **Status**: 200 OK

### ❌ **Test 2: No Authentication**

- **Headers**: Remove Authorization header
- **Expected**: `{"detail": "Missing ID token"}`
- **Status**: 401 Unauthorized

### ❌ **Test 3: Unverified Email**

- **Token**: Use the "Unverified Email" token
- **Expected**: `{"detail": "Insufficient permissions"}`
- **Status**: 403 Forbidden

## 🔄 **API Flow Explanation**

```mermaid
graph LR
    A[Postman] --> B[Your API :8001]
    B --> C[Google Auth Check]
    C --> D[Ollama :11434]
    D --> E[Translation Response]
    E --> B
    B --> A
```

### **What Happens Step by Step:**

1. **Postman** → `POST http://localhost:8001/ask/ask`
2. **Your API** → Validates Google token (fake in testing mode)
3. **Your API** → Calls `http://localhost:11434/api/generate`
4. **Ollama** → Generates translation using llama3.2
5. **Your API** → Returns formatted response to Postman

## 🎯 **Expected Translation Response**

```json
{
  "original_title": "Test Article",
  "original_body": "Hello world, please translate this text to Spanish.",
  "translated_title": "Artículo de Prueba",
  "translated_body": "Hola mundo, por favor traduce este texto al español.",
  "target_language": "spanish",
  "section": "content",
  "model_used": "llama3.2"
}
```

## 🛠️ **Troubleshooting**

### **"Missing ID token"**

- ✅ Add `Authorization: Bearer <token>` header

### **"Invalid token"**

- ✅ Use a fresh token from `generate_test_tokens.py`
- ✅ Ensure `TESTING_MODE=true` in `.env`

### **"Ollama connection failed"**

- ✅ Check: `curl http://localhost:11434/api/tags`
- ✅ Start Ollama: `ollama serve`

### **"Internal Server Error"**

- ✅ Check server logs in terminal
- ✅ Restart API server

## 🔄 **Generate Fresh Tokens**

Run this anytime to get new test tokens:

```bash
/Users/joelmontesdeoca/Documents/Bafik/OllamaAPI/venv/bin/python generate_test_tokens.py
```

## 🎉 **Ready for Production**

When ready for production:

1. Set `TESTING_MODE=false` in `.env`
2. Use real Google Client ID
3. Your NextJS app will send real Google ID tokens
4. Deploy with Docker: `./start_ollama.sh docker`

**Your API is now fully functional and ready for testing!** 🚀
