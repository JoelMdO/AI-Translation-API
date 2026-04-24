"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
from utils.rag_service import rag_service

async def ingest_language(language: str) -> Dict[str, int]:
    """Ingest all published articles for a given language. Returns stats dict."""
    col_id = await rag_service.get_or_create_collection(language)
    if not col_id:
        return {"ingested": 0, "errors": 1}

    articles = await fetch_articles(language)
    total_ingested = 0
    total_errors = 0

    for article in articles:
        try:
            text = article.get("plain_text", "").strip()
            title = article.get("title", "")
            combined = f"{title}\n\n{text}" if title else text
            if not combined:
                continue
            chunks = chunk_text(combined)
            upserted = await _upsert_chunks(col_id, chunks, str(article.get("id", "")), language)
            total_ingested += upserted
        except Exception as e:
            print(f"⚠️  Error ingesting article {article.get('id')}: {e}")
            total_errors += 1

    print(f"✅ ingest_language({language}): {total_ingested} chunks, {total_errors} errors")
    return {"ingested": total_ingested, "errors": total_errors}
