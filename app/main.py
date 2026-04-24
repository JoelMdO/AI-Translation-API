"""
Main FastAPI application
Simple translation API that validates Google tokens and calls Ollama for translation
Simple translation API that validates Google tokens and calls Ollama for translation
"""
from fastapi import FastAPI
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from schemas.translation import HealthResponse
from utils.translation.translate_html_utils import translateHTML_utils as ollama_service
from utils.rag_service import rag_service
from API.app.utils.rag_service.ingestion.ingest_vocabulary import ingest_all, is_populated
from utils.translation.generate_translation import generate_translation
from config import OLLAMA_BASE_URL
from config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
from routers import resume_router, translate_router
from routers import rag_router
import logging
import sys

# Configure logging for the application (stream to stdout so Docker captures it)
level = getattr(logging, "INFO", logging.INFO)  # Default to INFO
logging.basicConfig(
    level=level,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
##//TODO remove the app. before deploying 
# from app.schemas.translation import HealthResponse
# from app.utils.translation.translate_html_utils import translateHTML_utils as ollama_service
# from app.utils.rag_service import rag_service
# from app.utils.rag_ingestion import ingest_all, is_populated
# from app.config import ALLOWED_ORIGINS, CORS_METHODS, CORS_ALLOW_HEADERS
# from app.routers import resume_router, translate_router
# from app.routers import rag_router

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
        logger.warning("⚠️  Warning: Ollama service is not accessible")
    else:
        logger.info("✅ Connected to Ollama successfully!")
        # Warm up the model to avoid cold-start latency on first real request
        try:
            warmup_prompt = "Warmup: respond with ready"
            logger.info("🔁 Sending warmup prompt to Ollama to preload model")
            # Use a slightly longer timeout for warmup
            if OLLAMA_BASE_URL is None:
                raise RuntimeError("OLLAMA_BASE_URL is not configured. Set OLLAMA_BASE_URL in config.")
            resp = await generate_translation(warmup_prompt, timeout=30.0, base_url=OLLAMA_BASE_URL)
            logger.info("🔁 Warmup response: %s", (resp or '')[:200])
        except Exception as e:
            logger.warning("Warmup request failed: %s", str(e))

    # Startup: Check ChromaDB and auto-ingest if collections are empty
    if not await rag_service.check_health():
        logger.warning("⚠️  ChromaDB is not accessible — RAG enrichment disabled")
    else:
        logger.info("✅ Connected to ChromaDB successfully!")
        en_populated = await is_populated("en")
        es_populated = await is_populated("es")
        if not en_populated or not es_populated:
            logger.info("🔄 ChromaDB collections empty — starting RAG ingestion from CMS...")
            await ingest_all()
        else:
            logger.info("✅ ChromaDB collections already populated — skipping ingestion")
    
    yield
    
    # Shutdown: Cleanup if needed
    logger.info("🔄 Shutting down...")


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
    chroma_healthy = await rag_service.check_health()
    status: str = "healthy"

    if ollama_healthy and chroma_healthy:
        status = "healthy"
    elif not ollama_healthy and not chroma_healthy:
        status = "unhealthy - Ollama and ChromaDB unreachable"
    elif not ollama_healthy:
        status = "unhealthy - Ollama unreachable"
    else:        
        status = "unhealthy - ChromaDB unreachable"

    return HealthResponse(
        status=status,
        ollama_connected=ollama_healthy,
        chroma_connected=chroma_healthy,
        api_version="1.0.0"
    )


app.include_router(translate_router.router, prefix="/api")
app.include_router(resume_router.router, prefix="/api")
app.include_router(rag_router.router, prefix="/api")
