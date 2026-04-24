"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
from bs4 import BeautifulSoup

def clean_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)

