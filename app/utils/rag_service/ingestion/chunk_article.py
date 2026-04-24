"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
def chunk_article(title: str, body: str, chunk_tokens=400, overlap_tokens=60) -> list[str]:
    text = f"{title}. {body}" if title else body
    sentences = sent_tokenize(text)
    chunks, current, current_tokens = [], [], 0

    for sent in sentences:
        t = len(enc.encode(sent))
        if current_tokens + t > chunk_tokens and current:
            chunks.append(" ".join(current))
            # overlap: keep last N tokens worth of sentences
            overlap, overlap_t = [], 0
            for s in reversed(current):
                st = len(enc.encode(s))
                if overlap_t + st > overlap_tokens:
                    break
                overlap.insert(0, s)
                overlap_t += st
            current, current_tokens = overlap[:], overlap_t
        current.append(sent)
        current_tokens += t

    if current:
        chunks.append(" ".join(current))
    return chunks