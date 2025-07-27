"""
Main FastAPI application
Simple translation API that validates Google tokens and calls Ollama for translation
"""
# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware
# from schemas.translation import HealthResponse
# from utils.generate_translation import ollama_service
# from config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
# from routers import ask_router

##//TODO change app before deploying 
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.translation import HealthResponse
from app.utils.generate_translation import ollama_service
from app.config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
from app.routers import ask_router

if( not ALLOWED_ORIGINS):
    raise ValueError("ALLOWED_ORIGINS environment variable is not set. Please define it in your .env file."
                     )
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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)



# Authentication is now handled by dependencies in individual routes
# No middleware needed - this provides better error handling and debugging


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


