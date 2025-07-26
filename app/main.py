"""
Main FastAPI application
Simple translation API that validates JWT tokens and calls Ollama for translation
"""
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Callable, Awaitable
from fastapi import Response
from app.schemas.translation import HealthResponse
from app.utils.generate_translation import ollama_service
from app.config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS, URL_AUTH, GOOGLE_CLIENT_ID
# from app.config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS, URL_AUTH, GOOGLE_CLIENT_ID, TESTING_MODE
from app.routers import ask_router

load_dotenv()

if not ALLOWED_ORIGINS:
    raise ValueError("ALLOWED_ORIGINS environment variable is not set. Please define it in your .env file.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    Manages startup and shutdown events
    """
    # Startup: Check Ollama connection
    if not await ollama_service.check_health():
        print("⚠️  Warning: Ollama service is not accessible")
    else:
        print("✅ Connected to Ollama successfully!")
    
    yield
    
    # Shutdown: Cleanup if needed
    print("🔄 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Ollama Translation API",
    description="Simple translation API for NextJS apps with Google authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración del middleware de CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[ALLOWED_ORIGINS] if ALLOWED_ORIGINS else ["*"],  ##TODO change on production
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Permitir credenciales
    allow_methods=CORS_METHODS,  # Métodos configurados en .env
    allow_headers=CORS_ALLOW_HEADERS,  # Headers específicos requeridos
)



@app.middleware("http")
async def google_auth_check(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    # Public endpoints that don't require authentication
    public_paths = ["/health"]
    
    if request.url.path in public_paths:
        return await call_next(request)
    
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Missing ID token")

    # TESTING MODE: Skip real Google validation for fake tokens
    # if TESTING_MODE:
        # In testing mode, just check if token exists and has Bearer format
        # if not token.startswith("Bearer "):
        #     raise HTTPException(status_code=401, detail="Invalid token format")
        # Let the route dependency handle fake token validation
        # return await call_next(request)
    
    # PRODUCTION MODE: Real Google token validation
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{URL_AUTH}{token.split()[-1]}")
        if response.status_code != 200 or response.json().get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=403, detail="Invalid token")

    return await call_next(request)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies API is running and Ollama service is accessible
    """
    ollama_healthy = await ollama_service.check_health()
    
    return HealthResponse(
        status="healthy" if ollama_healthy else "unhealthy",
        ollama_connected=ollama_healthy,
        api_version="1.0.0"
    )

app.include_router(ask_router.router, prefix="/ask")


