import uuid, hashlib
from qdrant_client.models import PointStruct

embedder = SentenceTransformer("BAAI/bge-m3", device="cpu")

def build_point(embed_text: str, payload: dict) -> PointStruct:
    vec = embedder.encode(embed_text, normalize_embeddings=True).tolist()
    # Deterministic ID: same text always maps to the same point (safe for re-ingestion)
    point_id = str(uuid.UUID(hashlib.md5(embed_text.encode()).hexdigest()))
    return PointStruct(id=point_id, vector=vec, payload=payload)