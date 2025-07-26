# 🐳 Ollama Testing & Docker Container Guide

## 📋 **Current Setup Analysis**

You have **two different configurations**:

### 🖥️ **Local Testing Setup**

- **Ollama URL**: `http://localhost:11434` (your current .env)
- **Testing Mode**: `TESTING_MODE=true` (fake Google tokens)
- **Ollama**: Runs directly on your machine

### 🐳 **Docker Container Setup**

- **Ollama URL**: `http://ollama:11434` (commented in .env, used in docker-compose)
- **Production Mode**: `TESTING_MODE=false` (real Google tokens)
- **Ollama**: Runs in Docker container

## 🚀 **Testing Scenarios**

### **Scenario 1: Local Testing (Current)**

#### Does it start Ollama?

**NO** - Your tests assume Ollama is already running locally.

#### How to run:

```bash
# Option A: Use the startup script (RECOMMENDED)
./start_ollama.sh local

# Option B: Manual steps
# 1. Start Ollama locally
ollama serve

# 2. Pull model (if not already done)
ollama pull llama3.2

# 3. Run your API tests
./venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### **Scenario 2: Docker Container Testing**

#### Does it start Ollama?

**YES** - Docker Compose starts everything including Ollama.

#### How to run:

```bash
# Option A: Use the startup script (RECOMMENDED)
./start_ollama.sh docker

# Option B: Manual steps
# 1. Start all containers (including Ollama)
docker-compose up -d

# 2. Wait for Ollama to be ready
# 3. Pull model in container
docker exec ollama ollama pull llama3.2
```

## 🛠️ **Easy Startup Script Usage**

I've created `start_ollama.sh` that handles everything:

```bash
# Local testing with fake Google tokens
./start_ollama.sh local

# Docker containers with real Google tokens
./start_ollama.sh docker

# Stop all services
./start_ollama.sh stop

# Check status
./start_ollama.sh status

# Run tests and generate tokens
./start_ollama.sh test
```

## 📊 **Environment Files**

### `.env.local` (Local Testing)

```properties
OLLAMA_BASE_URL=http://localhost:11434
TESTING_MODE=true  # Fake Google tokens
API_HOST=127.0.0.1
```

### `.env.docker` (Container Mode)

```properties
OLLAMA_BASE_URL=http://ollama:11434  # Container name
TESTING_MODE=false  # Real Google tokens
API_HOST=0.0.0.0
```

## 🔄 **What Happens in Each Mode**

### **Local Mode (`./start_ollama.sh local`)**

1. ✅ **Copies `.env.local` to `.env`**
2. ✅ **Checks if Ollama is running locally**
3. ✅ **Starts Ollama if not running (`ollama serve`)**
4. ✅ **Waits for Ollama to be ready**
5. ✅ **Ensures `llama3.2` model is available**
6. ✅ **Starts FastAPI server on localhost:8000**
7. ✅ **Uses fake Google tokens for testing**

**Result**: Perfect for development and Postman testing

### **Docker Mode (`./start_ollama.sh docker`)**

1. ✅ **Copies `.env.docker` to `.env`**
2. ✅ **Starts Docker containers (`docker-compose up -d`)**
3. ✅ **Ollama container starts automatically**
4. ✅ **Waits for Ollama container to be ready**
5. ✅ **Ensures `llama3.2` model is available in container**
6. ✅ **FastAPI connects to containerized Ollama**
7. ✅ **nginx provides HTTPS on port 443**
8. ✅ **Uses real Google tokens**

**Result**: Production-ready setup with HTTPS

## 🧪 **Testing Workflow**

### **For Local Development:**

```bash
# 1. Start everything
./start_ollama.sh local

# 2. Generate test tokens
./start_ollama.sh test

# 3. Use Postman with generated tokens
# API: http://localhost:8000
# Health: http://localhost:8000/health
```

### **For Docker/Production:**

```bash
# 1. Start containers
./start_ollama.sh docker

# 2. Test with real Google tokens
# API: https://localhost:443
# Health: https://localhost:443/health
```

## 📝 **Key Differences**

| Aspect              | Local Mode              | Docker Mode                |
| ------------------- | ----------------------- | -------------------------- |
| **Ollama Location** | `localhost:11434`       | `ollama:11434`             |
| **Authentication**  | Fake Google tokens      | Real Google tokens         |
| **API URL**         | `http://localhost:8000` | `https://localhost:443`    |
| **HTTPS**           | No                      | Yes (nginx)                |
| **Startup Time**    | Fast                    | Slower (container startup) |
| **Use Case**        | Development/Testing     | Production                 |

## 🔍 **Troubleshooting**

### **Ollama Not Starting Locally**

```bash
# Check if Ollama is installed
ollama --version

# Install if missing
brew install ollama

# Start manually
ollama serve
```

### **Docker Issues**

```bash
# Check container logs
docker-compose logs ollama
docker-compose logs fastapi

# Restart containers
./start_ollama.sh stop
./start_ollama.sh docker
```

### **Model Not Available**

```bash
# Local
ollama pull llama3.2

# Docker
docker exec ollama ollama pull llama3.2
```

## ✨ **Summary**

Your testing setup is now **completely automated**:

- **Local Testing**: `./start_ollama.sh local` - Everything starts automatically
- **Docker Production**: `./start_ollama.sh docker` - Full container stack
- **Testing**: Uses fake Google tokens, no need for real OAuth setup
- **Production**: Uses real Google tokens with HTTPS

The script handles all the complexity for you! 🎉
