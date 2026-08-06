import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import ROOT_DIR

_CHROMA_CLIENT = None
_CHROMA_COLLECTIONS: dict[str, object] = {}


def _get_client():
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is not None:
        return _CHROMA_CLIENT

    chroma_dir = ROOT_DIR / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    try:
        _CHROMA_CLIENT = chromadb.HttpClient(
            host="localhost",
            port=8001,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _CHROMA_CLIENT.heartbeat()
    except Exception:
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    return _CHROMA_CLIENT


def get_chroma_store(collection: str = "knowledge_base"):
    if collection in _CHROMA_COLLECTIONS:
        return _CHROMA_COLLECTIONS[collection]

    client = _get_client()
    col = client.get_or_create_collection(name=collection)
    _CHROMA_COLLECTIONS[collection] = col
    return col
