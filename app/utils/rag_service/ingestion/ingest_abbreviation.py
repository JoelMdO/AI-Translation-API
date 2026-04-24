"""
RAG ingestion — fetches published articles from the Django CMS,
chunks them, and upserts into ChromaDB.

Called automatically on FastAPI startup if either collection is empty,
and manually via POST /api/rag/ingest (admin, Google OAuth required).
"""

def ingest_abbreviations(entries: list[dict], collection: QdrantCollection):
    """
    Entries from db look like:{
    "abbreviation": "ACARS",
    "english": "Aircraft communications addressing and reporting system",
    "spanish": "Sistema de direccionamiento e informe para comunicaciones de aeronaves"
    }
    """
    points = []
    for e in entries: # type: ignore
        # Embed: abbreviation + full English — maximises recall for both query forms
        embed_text = f"{e['abbreviation']} {e['english']}"

        payload = { # type: ignore
            "source_type": "abbreviation",
            "term": e["english"],
            "abbreviation": e["abbreviation"],
            "definition": e["english"],
            "spanish_term": e["spanish"],       # ← ready-made, use directly in prompt
            "ata_chapter": e.get("ata_chapter"), #type: ignore
            "aircraft_system": e.get("aircraft_system"), #type: ignore
        }
        points.append(build_point(embed_text, payload)) # type: ignore

    collection.upsert(points) # type: ignore

