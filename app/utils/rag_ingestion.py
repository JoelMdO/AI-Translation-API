"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
import hashlib
import httpx
from typing import Any, Dict, List

from config import CMS_RAG_URL, CMS_RAG_TOKEN, CHROMA_HOST, CHROMA_PORT
from utils import rag_service

_CHROMA_BASE = f"http://{CHROMA_HOST}:{CHROMA_PORT}"

_CHUNK_SIZE = 400
_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _OVERLAP) -> List[str]:
    """Sliding-window text chunker."""
    words = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
        start += chunk_size - overlap
    return chunks


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


async def _upsert_chunks(col_id: str, chunks: List[str], article_id: str, language: str) -> int:
    """Embed and upsert a list of text chunks into ChromaDB. Returns count upserted."""
    upserted = 0
    for i, chunk in enumerate(chunks):
        doc_id = hashlib.md5(f"{article_id}_{i}".encode()).hexdigest()
        embedding = await rag_service.embed(chunk)
        if not embedding:
            continue
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{_CHROMA_BASE}/api/v1/collections/{col_id}/upsert",
                    json={  # type: ignore[arg-type]
                        "ids": [doc_id],
                        "embeddings": [embedding],
                        "documents": [chunk],
                        "metadatas": [{"article_id": article_id, "language": language, "chunk": i}],
                    },
                )
                if resp.status_code in (200, 201):
                    upserted += 1
        except Exception as e:
            print(f"⚠️  upsert chunk {doc_id} failed: {e}")
    return upserted


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


async def ingest_all() -> Dict[str, Any]:
    """Ingest both EN and ES. Returns combined stats."""
    results: Dict[str, Any] = {}
    for lang in ("en", "es"):
        results[lang] = await ingest_language(lang)
    total_ingested = sum(v["ingested"] for v in results.values())
    total_errors = sum(v["errors"] for v in results.values())
    print(f"✅ ingest_all complete: {total_ingested} chunks ingested, {total_errors} errors")
    return {"total_ingested": total_ingested, "total_errors": total_errors, "details": results}


async def is_populated(language: str) -> bool:
    """Return True if the ChromaDB collection for the language already has documents."""
    count = await rag_service.collection_count(language)
    return count > 0
