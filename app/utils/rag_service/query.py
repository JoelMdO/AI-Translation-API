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


async def get_or_create_collection(lang: str) -> str | None:
    """Return the ChromaDB collection UUID for lang, creating it if absent."""
    if lang in _collection_ids:
        return _collection_ids[lang]

    name = _COLLECTION_MAP.get(lang, f"rag_{lang}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to get existing collection
            resp = await client.get(f"{_CHROMA_BASE}/api/v1/collections/{name}")
            if resp.status_code == 200:
                col_id = resp.json()["id"]
                _collection_ids[lang] = col_id
                return col_id

            # Create it
            resp = await client.post(
                f"{_CHROMA_BASE}/api/v1/collections",
                json={"name": name, "metadata": {"hnsw:space": "cosine"}},
            )
            if resp.status_code in (200, 201):
                col_id = resp.json()["id"]
                _collection_ids[lang] = col_id
                return col_id
    except Exception as e:
        print(f"⚠️  ChromaDB collection lookup/create failed ({lang}): {e}")
    return None


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
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_CHROMA_BASE}/api/v1/collections/{col_id}/query",
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


