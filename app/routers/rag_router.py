"""
RAG management router.

GET  /api/rag/status  — public health check + collection counts
POST /api/rag/ingest  — trigger re-ingestion (requires Google OAuth)
"""
from fastapi import APIRouter, Depends

from schemas.testUser import GoogleUser
from utils.auth import verify_google_access_token
from utils import rag_service
from utils.rag_ingestion import ingest_all

router = APIRouter(tags=["rag"])


@router.get("/rag/status")
async def rag_status():
    """Return ChromaDB health and per-language collection counts."""
    available = await rag_service.check_health()
    counts = {}
    if available:
        for lang in ("en", "es"):
            counts[lang] = {"count": await rag_service.collection_count(lang)}
    return {
        "chroma_available": available,
        "collections": counts,
    }


@router.post("/rag/ingest")
async def rag_ingest(_user: GoogleUser = Depends(verify_google_access_token)):
    """
    Trigger a full re-ingestion of articles from the CMS into ChromaDB.
    Requires a valid Google OAuth bearer token.
    """
    result = await ingest_all()
    return {"success": True, **result}
