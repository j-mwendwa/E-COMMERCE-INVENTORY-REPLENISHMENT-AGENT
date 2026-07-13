from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config import settings

_QDRANT_COLLECTIONS: dict[str, object] = {}


def _get_client() -> QdrantClient:
    if settings.qdrant_api_key:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(url=settings.qdrant_url or "http://localhost:6333")


def get_qdrant_store(collection: str = "knowledge_base"):
    if collection in _QDRANT_COLLECTIONS:
        return _QDRANT_COLLECTIONS[collection]

    client = _get_client()
    collections = client.get_collections().collections
    if not any(c.name == collection for c in collections):
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
    _QDRANT_COLLECTIONS[collection] = client
    return client
