"""
Main FastAPI application
Simple translation API that validates Google tokens and calls Ollama for translation
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Request
# from schemas.translation import HealthResponse
# from utils.ollama_services import ollama_service
# from config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
# from routers import ask_router, resume_router
##//TODO remove the app. before deploying 
from app.schemas.translation import HealthResponse
from app.utils.ollama_services import ollama_service
from app.config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
from app.routers import resume_router, translate_router

if( not ALLOWED_ORIGINS):
    raise ValueError("ALLOWED_ORIGINS environment variable is not set. Please define it in your .env file."
                     )
@asynccontextmanager
# async def lifespan(app: FastAPI):
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
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    raw = await request.body()
    print("=== REQUEST VALIDATION ERROR ===")
    print("URL:", request.url)
    print("RAW BODY (first 2000 bytes):", raw[:2000])
    print("Pydantic errors:", exc.errors())
    print("================================")
    # Return the default error structure so client still sees details
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
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

app.include_router(translate_router.router, prefix="/api")
app.include_router(resume_router.router, prefix="/api")
