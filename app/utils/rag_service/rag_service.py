"""
RAG service — ChromaDB client with graceful fallback.

If ChromaDB is unreachable, every public method returns an empty/safe value so
the translation/summarisation pipeline degrades gracefully to non-RAG mode.

Collections:
  rag_en  — English style passages
  rag_es  — Spanish style passages
"""
import httpx
from .query import get_or_create_collection, get_v2_context
from config import CHROMA_HOST, CHROMA_PORT



# Base URL for Chroma (host + port from env)
_CHROMA_BASE = f"http://{CHROMA_HOST}:{CHROMA_PORT}"
# Keep private alias for backward compatibility
_get_or_create_collection = get_or_create_collection

async def check_health() -> bool:
    """Return True if ChromaDB is reachable.

    Be conservative: try multiple known heartbeat endpoints used by
    different Chroma releases and local setups.
    """
    endpoints = [
        "/api/v2/heartbeat",
        "/api/v1/heartbeat",
        "/api/v1/health",
        "/health",
        "/heartbeat",
    ]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for ep in endpoints:
                try:
                    resp = await client.get(f"{_CHROMA_BASE}{ep}")
                    if resp.status_code == 200:
                        return True
                except Exception:
                    # try next endpoint
                    continue
    except Exception:
        pass
    return False


async def collection_count(lang: str) -> int:
    """Return number of documents in the collection for lang. Returns 0 on error."""
    col_id = await _get_or_create_collection(lang)
    if not col_id:
        return 0
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tenant, database = await get_v2_context()
            if not tenant or not database:
                return 0
            resp = await client.get(
                f"{_CHROMA_BASE}/api/v2/tenants/{tenant}/databases/{database}/collections/{col_id}/count"
            )
            if resp.status_code == 200:
                data = resp.json()
                # Chroma may return a raw int or a JSON object like {"count": N}
                if isinstance(data, dict):
                    return int(data.get("count") or 0)  # type: ignore
                try:
                    return int(data)
                except Exception:
                    return 0
    except Exception as e:
        print(f"⚠️  collection_count failed ({lang}): {e}")
    return 0


