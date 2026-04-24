"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
async def ingest_article(article: dict, collection: QdrantCollection):
    raw_body = article.get("body", "")
    body     = clean_html(raw_body) if "<" in raw_body else raw_body
    title    = article.get("title", "")
    chunks   = chunk_article(title, body)

    points = []
    for i, chunk in enumerate(chunks):
        payload = {
            "source_type": "article",
            "title": title,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk,
            "term": None,
            "abbreviation": None,
            "spanish_term": None,
        }
        points.append(build_point(chunk, payload))

    collection.upsert(points)


