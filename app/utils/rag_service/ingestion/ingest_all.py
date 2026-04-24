"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""

async def ingest_all() -> Dict[str, Any]:
    """Ingest both EN and ES. Returns combined stats."""
    results: Dict[str, Any] = {}
    for lang in ("en", "es"):
        results[lang] = await ingest_language(lang)
    total_ingested = sum(v["ingested"] for v in results.values())
    total_errors = sum(v["errors"] for v in results.values())
    print(f"✅ ingest_all complete: {total_ingested} chunks ingested, {total_errors} errors")
    return {"total_ingested": total_ingested, "total_errors": total_errors, "details": results}

