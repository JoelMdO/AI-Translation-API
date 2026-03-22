"""
RAG service — ChromaDB client with graceful fallback.

If ChromaDB is unreachable, every public method returns an empty/safe value so
the translation/summarisation pipeline degrades gracefully to non-RAG mode.

Collections:
  rag_en  — English style passages
  rag_es  — Spanish style passages
"""
import httpx
from .query import get_or_create_collection
from config import CHROMA_HOST, CHROMA_PORT



_CHROMA_BASE = f"http://{CHROMA_HOST}:{CHROMA_PORT}"
# Keep private alias for backward compatibility
_get_or_create_collection = get_or_create_collection

async def check_health() -> bool:
    """Return True if ChromaDB is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{_CHROMA_BASE}/api/v1/heartbeat")
            return resp.status_code == 200
    except Exception:
        return False


async def collection_count(lang: str) -> int:
    """Return number of documents in the collection for lang. Returns 0 on error."""
    col_id = await _get_or_create_collection(lang)
    if not col_id:
        return 0
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_CHROMA_BASE}/api/v1/collections/{col_id}/count")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"⚠️  collection_count failed ({lang}): {e}")
    return 0


