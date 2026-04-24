# knowledge_base/setup.py
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

def create_collection(client: QdrantClient, name="aviation_kb"):
    client.recreate_collection(
        collection_name=name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    # Index frequently filtered metadata fields for fast payload filtering
    for field in ["source_type", "abbreviation", "ata_chapter", "aircraft_system"]:
        client.create_payload_index(
            collection_name=name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )