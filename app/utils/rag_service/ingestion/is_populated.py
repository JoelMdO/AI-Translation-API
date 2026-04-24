"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
from utils.rag_service import rag_service

async def is_populated(language: str) -> bool:
    """Return True if the ChromaDB collection for the language already has documents."""
    count = await rag_service.collection_count(language)
    return count > 0
