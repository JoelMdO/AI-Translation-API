"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
import httpx
from typing import Any, Dict, List
from config import CMS_RAG_URL, CMS_RAG_TOKEN


async def fetch_articles(language: str) -> List[Dict[str, Any]]:
    """GET CMS_RAG_URL?lang=<language> authenticated with X-RAG-Token header."""
    if not CMS_RAG_URL or not CMS_RAG_TOKEN:
        print("⚠️  CMS_RAG_URL or CMS_RAG_TOKEN not configured — skipping fetch")
        return []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                CMS_RAG_URL,
                params={"lang": language},
                headers={"X-RAG-Token": CMS_RAG_TOKEN},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"⚠️  fetch_articles({language}) failed: {e}")
        return []
