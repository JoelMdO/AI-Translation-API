"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""
import re
# knowledge_base/ingestors/vocabulary_ingestor.py

def ingest_vocabulary(vocab: dict[str, str], collection: QdrantCollection):
    """
    vocab = {"FMS": "Flight Management System (FMS)", "ILS": "Instrument Landing System", ...}
    """
    points = []
    for abbrev, full_form in vocab.items():
        # Extract the clean English term (strip redundant abbreviation in parens)
        english_term = re.sub(r'\s*\([^)]+\)\s*$', '', full_form).strip()

        embed_text = f"{abbrev} {english_term}"   # "FMS Flight Management System"

        payload = { # type: ignore
            "source_type": "vocabulary",
            "term": english_term,
            "abbreviation": abbrev,
            "definition": full_form,
            "spanish_term": None,      # populate via separate translation pass or manual
            "ata_chapter": None,
            "aircraft_system": None,
        }
        points.append(build_point(embed_text, payload)) # type: ignore

    collection.upsert(points) # type: ignore

