"""
RAG service — Query.
"""
import httpx
from typing import List, Dict

from config import CHROMA_HOST, CHROMA_PORT, OLLAMA_BASE_URL, EMBED_MODEL, RAG_N_RESULTS

_CHROMA_BASE = f"http://{CHROMA_HOST}:{CHROMA_PORT}"
_COLLECTION_MAP = {"en": "rag_en", "es": "rag_es"}

# ── Collection-ID cache (filled lazily) ─────────────────────────────────────
_collection_ids: Dict[str, str] = {}
_V2_TENANT: str | None = None
_V2_DATABASE: str | None = None


async def get_or_create_collection(lang: str) -> str | None:
    """Return the ChromaDB collection UUID for lang, creating it if absent."""
    if lang in _collection_ids:
        return _collection_ids[lang]

    name = _COLLECTION_MAP.get(lang, f"rag_{lang}")
    try:
        # Use v2 API which requires tenant/database scoping. Discover identity lazily.
        tenant, database = await _get_v2_identity()
        if not tenant or not database:
            print("⚠️  Could not determine Chroma tenant/database")
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to get existing collection by name
            resp = await client.get(f"{_CHROMA_BASE}/api/v2/tenants/{tenant}/databases/{database}/collections/{name}")
            if resp.status_code == 200:
                col_id = resp.json().get("id")
                if col_id:
                    _collection_ids[lang] = col_id
                    return col_id

            # Create collection in v2
            create_payload = {"name": name, "metadata": {"hnsw:space": "cosine"}, "get_or_create": True}
            resp = await client.post(
                f"{_CHROMA_BASE}/api/v2/tenants/{tenant}/databases/{database}/collections",
                json=create_payload,
            )
            if resp.status_code in (200, 201):
                col_id = resp.json().get("id")
                if col_id:
                    _collection_ids[lang] = col_id
                    return col_id
            # Log response for debugging
            try:
                body = resp.text
            except Exception:
                body = "<unreadable>"
            print(f"⚠️  create collection v2 returned {resp.status_code}: {body}")
    except Exception as e:
        print(f"⚠️  ChromaDB collection lookup/create failed ({lang}): {e}")
    return None


async def _get_v2_identity() -> tuple[str | None, str | None]:
    """Return (tenant, database) for the Chroma v2 API (cached)."""
    global _V2_TENANT, _V2_DATABASE
    if _V2_TENANT and _V2_DATABASE:
        return _V2_TENANT, _V2_DATABASE
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{_CHROMA_BASE}/api/v2/auth/identity")
            if resp.status_code == 200:
                data = resp.json()
                tenant = data.get("tenant")
                databases = data.get("databases") or []
                database = databases[0] if len(databases) else None
                _V2_TENANT = tenant
                _V2_DATABASE = database
                return tenant, database
    except Exception as e:
        print(f"⚠️  get_v2_identity failed: {e}")
    return None, None


async def get_v2_context() -> tuple[str | None, str | None]:
    """Public helper to retrieve tenant and database for v2 requests."""
    return await _get_v2_identity()


# Keep private alias for backward compatibility
_get_or_create_collection = get_or_create_collection


async def embed(text: str) -> List[float]:
    """Call Ollama /api/embeddings and return the embedding vector."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json().get("embedding", [])
    except Exception as e:
        print(f"⚠️  Embed failed: {e}")
        return []


async def query(text: str, language: str, n_results: int = RAG_N_RESULTS) -> List[str]:
    """
    Return up to n_results style passage strings from ChromaDB for the
    given language.  Returns [] on any error.
    """
    col_id = await _get_or_create_collection(language)
    if not col_id:
        return []

    embedding = await embed(text)
    if not embedding:
        return []

    try:
        tenant, database = await _get_v2_identity()
        if not tenant or not database:
            return []
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_CHROMA_BASE}/api/v2/tenants/{tenant}/databases/{database}/collections/{col_id}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": n_results,
                    "include": ["documents"],
                },
            )
            if resp.status_code == 200:
                docs = resp.json().get("documents", [[]])
                return docs[0] if docs else []
    except Exception as e:
        print(f"⚠️  ChromaDB query failed: {e}")
    return []


